"""LAN provisioning helpers for Anycubic printers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DEVICE_CERT,
    CONF_DEVICE_CN,
    CONF_DEVICE_KEY,
    CONF_DEVICE_NAME,
    CONF_DEVICE_USN,
    CONF_DEVICE_UUID,
    CONF_DEVICE_ZONE,
    CONF_HOST,
    CONF_MODEL_NAME,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_PRINTER_ID,
    CONF_TYPE_ID,
)
from .lan_credentials import (
    CTRL_HTTP_PORT,
    PROBE_TIMEOUT,
    InvalidLanCredentialResponse,
    build_credential_request,
    normalize_host,
    parse_credential_response,
)


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
    device_name: str | None
    model_name: str | None
    device_cn: str | None
    device_usn: str | None
    device_zone: str | None

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
        if self.device_name:
            data[CONF_DEVICE_NAME] = self.device_name
        if self.model_name:
            data[CONF_MODEL_NAME] = self.model_name
        if self.device_cn:
            data[CONF_DEVICE_CN] = self.device_cn
        if self.device_usn:
            data[CONF_DEVICE_USN] = self.device_usn
        if self.device_zone:
            data[CONF_DEVICE_ZONE] = self.device_zone
        return data


async def async_probe_lan_printer(
    hass: HomeAssistant, host: str
) -> LanProvisioningResult:
    """Fetch and decrypt LAN MQTT credentials from a printer IP."""
    clean_host = normalize_host(host)
    session = async_get_clientsession(hass)
    try:
        info = await _fetch_json(session, f"http://{clean_host}:{CTRL_HTTP_PORT}/info")
        request = build_credential_request(info)
        ctrl = await _fetch_json(
            session,
            request.ctrl_url,
            method="POST",
            params=request.params,
        )
    except (ClientError, TimeoutError) as err:
        raise CannotConnect(
            f"Could not connect to Anycubic printer at {clean_host}"
        ) from err
    except InvalidLanCredentialResponse as err:
        raise InvalidResponse(str(err)) from err

    try:
        bundle = parse_credential_response(clean_host, info, ctrl, request.token)
    except InvalidLanCredentialResponse as err:
        raise InvalidResponse(str(err)) from err
    return LanProvisioningResult(
        host=bundle.host,
        type_id=bundle.type_id,
        printer_id=bundle.printer_id,
        username=bundle.username,
        password=bundle.password,
        device_cert=bundle.device_cert,
        device_key=bundle.device_key,
        device_uuid=bundle.device_uuid,
        device_name=bundle.device_name,
        model_name=bundle.model_name,
        device_cn=bundle.device_cn,
        device_usn=bundle.device_usn,
        device_zone=bundle.device_zone,
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
