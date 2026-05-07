"""Shared Anycubic LAN credential discovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import json
import secrets
import string
import time
from typing import Any
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


CTRL_HTTP_PORT = 18910
PROBE_TIMEOUT = 10
NONCE_CHARS = string.ascii_letters + string.digits


class LanCredentialError(Exception):
    """Base error for LAN credential discovery failures."""


class InvalidLanCredentialResponse(LanCredentialError):
    """Raised when the printer returns unexpected provisioning data."""


@dataclass(slots=True)
class LanCredentialRequest:
    """Signed LAN credential request details."""

    ctrl_url: str
    params: dict[str, str]
    token: str


@dataclass(slots=True)
class LanCredentialBundle:
    """Credentials returned by the printer LAN control endpoint."""

    host: str
    type_id: int
    printer_id: str
    username: str
    password: str
    device_cert: str
    device_key: str
    device_uuid: str | None
    device_name: str | None
    model_name: str | None
    device_cn: str | None
    device_usn: str | None
    device_zone: str | None


def build_credential_request(info: dict[str, Any]) -> LanCredentialRequest:
    """Build the signed POST details for the LAN credential endpoint."""
    token = require_string(info, "token")
    if len(token) < 32:
        raise InvalidLanCredentialResponse("Printer returned an invalid LAN token")
    ts = str(int(time.time() * 1000))
    nonce = "".join(secrets.choice(NONCE_CHARS) for _ in range(6))
    sign = md5(md5(token[:16]) + ts + nonce)
    return LanCredentialRequest(
        ctrl_url=require_string(info, "ctrlInfoUrl"),
        params={
            "ts": ts,
            "nonce": nonce,
            "sign": sign,
            "did": uuid4().hex.upper(),
        },
        token=token,
    )


def parse_credential_response(
    host: str, info: dict[str, Any], ctrl: dict[str, Any], token: str
) -> LanCredentialBundle:
    """Decrypt and normalize a LAN credential response."""
    if ctrl.get("code") != 200:
        raise InvalidLanCredentialResponse(
            f"Printer rejected LAN credential request with code {ctrl.get('code')}"
        )
    data = ctrl.get("data")
    if not isinstance(data, dict):
        raise InvalidLanCredentialResponse(
            "Printer LAN credential response did not include data"
        )

    encrypted_info = require_string(data, "info")
    iv = require_string(data, "token")
    bundle = decrypt_ctrl_info(encrypted_info, token[16:32], iv)

    printer_id = require_string(bundle, "deviceId")
    type_id = coerce_type_id(bundle.get("modelId") or bundle.get("modeId"))
    return LanCredentialBundle(
        host=normalize_host(host),
        type_id=type_id,
        printer_id=printer_id,
        username=require_string(bundle, "username"),
        password=require_string(bundle, "password"),
        device_cert=require_string(bundle, "devicecrt"),
        device_key=require_string(bundle, "devicepk"),
        device_uuid=optional_string(info.get("usn")),
        device_name=optional_string(info.get("deviceName")),
        model_name=optional_string(bundle.get("modelName"))
        or optional_string(info.get("modelName")),
        device_cn=optional_string(info.get("cn")),
        device_usn=optional_string(info.get("usn")),
        device_zone=optional_string(info.get("zone")),
    )


def decrypt_ctrl_info(encrypted_info: str, key: str, iv: str) -> dict[str, Any]:
    """Decrypt the AES-CBC LAN credential bundle."""
    if len(key.encode()) != 16 or len(iv.encode()) != 16:
        raise InvalidLanCredentialResponse(
            "Printer returned invalid LAN credential crypto material"
        )
    try:
        decryptor = Cipher(
            algorithms.AES(key.encode()),
            modes.CBC(iv.encode()),
        ).decryptor()
        padded = (
            decryptor.update(base64.b64decode(encrypted_info))
            + decryptor.finalize()
        )
        unpadder = PKCS7(128).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
        bundle = json.loads(plaintext.decode())
    except (ValueError, json.JSONDecodeError) as err:
        raise InvalidLanCredentialResponse(
            "Could not decrypt printer LAN credential bundle"
        ) from err
    if not isinstance(bundle, dict):
        raise InvalidLanCredentialResponse(
            "Printer LAN credential bundle was not an object"
        )
    return bundle


def normalize_host(host: str) -> str:
    """Return a bare host from user input."""
    host = host.strip()
    if host.startswith(("http://", "https://")):
        host = host.split("://", maxsplit=1)[1]
    host = host.split("/", maxsplit=1)[0]
    return host.split(":", maxsplit=1)[0]


def require_string(data: dict[str, Any], key: str) -> str:
    """Return a required string field."""
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise InvalidLanCredentialResponse(f"Printer response did not include {key}")
    return value


def optional_string(value: Any) -> str | None:
    """Return a non-empty string representation for optional metadata."""
    if isinstance(value, str):
        return value or None
    if isinstance(value, int):
        return str(value)
    return None


def coerce_type_id(value: Any) -> int:
    """Return the printer model/type ID as an integer."""
    try:
        return int(value)
    except (TypeError, ValueError) as err:
        raise InvalidLanCredentialResponse(
            "Printer response did not include modelId"
        ) from err


def md5(value: str) -> str:
    """Return lowercase MD5 hex digest."""
    return hashlib.md5(value.encode()).hexdigest()
