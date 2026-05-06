"""LAN provisioning helpers for Anycubic printers."""

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

from aiohttp import ClientError, ClientSession
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DEVICE_CERT,
    CONF_DEVICE_KEY,
    CONF_DEVICE_UUID,
    CONF_HOST,
    CONF_MODEL_NAME,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_PRINTER_ID,
    CONF_TYPE_ID,
)

CTRL_HTTP_PORT = 18910
PROBE_TIMEOUT = 10
_NONCE_CHARS = string.ascii_letters + string.digits


class CannotConnect(HomeAssistantError):
    """Error raised when the printer cannot be reached."""


class InvalidResponse(HomeAssistantError):
    """Error raised when the printer returns unexpected provisioning data."""


@dataclass(slots=True)
class LanProvisioningResult:
    """Credentials returned by the printer LAN control endpoint."""

    host: str
    type_id: int
    printer_id: str
    username: str
    password: str
    device_cert: str
    device_key: str
    device_uuid: str | None
    model_name: str | None

    def as_config_data(self) -> dict[str, Any]:
        """Return a config-entry-safe representation."""
        data: dict[str, Any] = {
            CONF_HOST: self.host,
            CONF_TYPE_ID: self.type_id,
            CONF_PRINTER_ID: self.printer_id,
            CONF_MQTT_USERNAME: self.username,
            CONF_MQTT_PASSWORD: self.password,
            CONF_DEVICE_CERT: self.device_cert,
            CONF_DEVICE_KEY: self.device_key,
        }
        if self.device_uuid:
            data[CONF_DEVICE_UUID] = self.device_uuid
        if self.model_name:
            data[CONF_MODEL_NAME] = self.model_name
        return data


async def async_probe_lan_printer(
    hass: HomeAssistant, host: str
) -> LanProvisioningResult:
    """Fetch and decrypt LAN MQTT credentials from a printer IP."""
    clean_host = _normalize_host(host)
    session = async_get_clientsession(hass)
    try:
        info = await _fetch_json(session, f"http://{clean_host}:{CTRL_HTTP_PORT}/info")
        token = _require_string(info, "token")
        if len(token) < 32:
            raise InvalidResponse("Printer returned an invalid LAN token")
        ctrl_url = _require_string(info, "ctrlInfoUrl")
        did = uuid4().hex.upper()
        ts = str(int(time.time() * 1000))
        nonce = "".join(secrets.choice(_NONCE_CHARS) for _ in range(6))
        sign = _md5(_md5(token[:16]) + ts + nonce)
        ctrl = await _fetch_json(
            session,
            ctrl_url,
            method="POST",
            params={
                "ts": ts,
                "nonce": nonce,
                "sign": sign,
                "did": did,
            },
        )
    except (ClientError, TimeoutError) as err:
        raise CannotConnect(
            f"Could not connect to Anycubic printer at {clean_host}"
        ) from err

    if ctrl.get("code") != 200:
        raise InvalidResponse(
            f"Printer rejected LAN credential request with code {ctrl.get('code')}"
        )
    data = ctrl.get("data")
    if not isinstance(data, dict):
        raise InvalidResponse("Printer LAN credential response did not include data")

    encrypted_info = _require_string(data, "info")
    iv = _require_string(data, "token")
    bundle = _decrypt_ctrl_info(encrypted_info, token[16:32], iv)

    printer_id = _require_string(bundle, "deviceId")
    type_id = _coerce_type_id(bundle.get("modelId") or bundle.get("modeId"))
    return LanProvisioningResult(
        host=clean_host,
        type_id=type_id,
        printer_id=printer_id,
        username=_require_string(bundle, "username"),
        password=_require_string(bundle, "password"),
        device_cert=_require_string(bundle, "devicecrt"),
        device_key=_require_string(bundle, "devicepk"),
        device_uuid=info.get("usn") if isinstance(info.get("usn"), str) else None,
        model_name=(
            bundle.get("modelName")
            if isinstance(bundle.get("modelName"), str)
            else info.get("modelName")
            if isinstance(info.get("modelName"), str)
            else None
        ),
    )


async def _fetch_json(
    session: ClientSession,
    url: str,
    *,
    method: str = "GET",
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Fetch a JSON object with a bounded timeout."""
    async with session.request(
        method, url, params=params, timeout=PROBE_TIMEOUT
    ) as response:
        response.raise_for_status()
        payload = await response.json(content_type=None)
    if not isinstance(payload, dict):
        raise InvalidResponse("Printer returned non-object JSON")
    return payload


def _decrypt_ctrl_info(encrypted_info: str, key: str, iv: str) -> dict[str, Any]:
    """Decrypt the AES-CBC LAN credential bundle."""
    if len(key.encode()) != 16 or len(iv.encode()) != 16:
        raise InvalidResponse("Printer returned invalid LAN credential crypto material")
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
        raise InvalidResponse("Could not decrypt printer LAN credential bundle") from err
    if not isinstance(bundle, dict):
        raise InvalidResponse("Printer LAN credential bundle was not an object")
    return bundle


def _normalize_host(host: str) -> str:
    """Return a bare host from user input."""
    host = host.strip()
    if host.startswith(("http://", "https://")):
        host = host.split("://", maxsplit=1)[1]
    host = host.split("/", maxsplit=1)[0]
    return host.split(":", maxsplit=1)[0]


def _require_string(data: dict[str, Any], key: str) -> str:
    """Return a required string field."""
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise InvalidResponse(f"Printer response did not include {key}")
    return value


def _coerce_type_id(value: Any) -> int:
    """Return the printer model/type ID as an integer."""
    try:
        return int(value)
    except (TypeError, ValueError) as err:
        raise InvalidResponse("Printer response did not include modelId") from err


def _md5(value: str) -> str:
    """Return lowercase MD5 hex digest."""
    return hashlib.md5(value.encode()).hexdigest()
