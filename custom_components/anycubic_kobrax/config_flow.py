"""Config flow for Anycubic Kobra X."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DEVICE_NAME,
    CONF_HOST,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_STREAM_PATH,
    DEFAULT_MQTT_PASSWORD,
    DEFAULT_MQTT_USERNAME,
    DOMAIN,
)
from .lan_probe import (
    CannotConnect,
    InvalidResponse,
    LanProvisioningResult,
    async_probe_lan_printer,
)


class AnycubicKobraXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Anycubic Kobra X config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize flow-scoped probe data."""
        self._probe_result: LanProvisioningResult | None = None
        self._stream_path: str | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AnycubicKobraXOptionsFlow:
        """Create the options flow."""
        return AnycubicKobraXOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                result = await async_probe_lan_printer(
                    self.hass, user_input[CONF_HOST]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(result.printer_id)
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: result.host}
                )

                self._probe_result = result
                self._stream_path = user_input.get(CONF_STREAM_PATH)
                return await self.async_step_details()

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_STREAM_PATH): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovered printer metadata."""
        if self._probe_result is None:
            return await self.async_step_user()

        result = self._probe_result
        default_name = (
            result.device_name
            or result.model_name
            or f"Anycubic {result.host}"
        )

        if user_input is not None:
            name = user_input[CONF_NAME].strip() or default_name
            data = result.as_config_data()
            data[CONF_NAME] = name
            data[CONF_DEVICE_NAME] = result.device_name or name
            if stream_path := self._stream_path:
                data[CONF_STREAM_PATH] = stream_path.strip()
            return self.async_create_entry(title=name, data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=default_name): str,
            }
        )
        return self.async_show_form(step_id="details", data_schema=schema)


class AnycubicKobraXOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Anycubic Kobra X."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Anycubic Kobra X options."""
        if user_input is not None:
            if name := user_input.get(CONF_NAME):
                user_input[CONF_NAME] = name.strip()
                self.hass.config_entries.async_update_entry(
                    self.config_entry, title=user_input[CONF_NAME]
                )
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data | self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=data.get(
                            CONF_NAME,
                            data.get(CONF_DEVICE_NAME, data.get(CONF_MODEL_NAME, "")),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_STREAM_PATH,
                        default=data.get(CONF_STREAM_PATH, ""),
                    ): str,
                    vol.Optional(
                        CONF_MQTT_USERNAME,
                        default=data.get(CONF_MQTT_USERNAME, DEFAULT_MQTT_USERNAME),
                    ): str,
                    vol.Optional(
                        CONF_MQTT_PASSWORD,
                        default=data.get(CONF_MQTT_PASSWORD, DEFAULT_MQTT_PASSWORD),
                    ): str,
                }
            ),
        )
