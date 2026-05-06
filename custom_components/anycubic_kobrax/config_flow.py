"""Config flow for Anycubic Kobra X."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_HOST,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_STREAM_PATH,
    DEFAULT_MQTT_PASSWORD,
    DEFAULT_MQTT_USERNAME,
    DOMAIN,
)
from .lan_probe import CannotConnect, InvalidResponse, async_probe_lan_printer


class AnycubicKobraXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Anycubic Kobra X config flow."""

    VERSION = 1
    MINOR_VERSION = 1

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

                data = result.as_config_data()
                if stream_path := user_input.get(CONF_STREAM_PATH):
                    data[CONF_STREAM_PATH] = stream_path.strip()

                title = result.model_name or f"Anycubic {result.host}"
                return self.async_create_entry(title=title, data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_STREAM_PATH): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )


class AnycubicKobraXOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Anycubic Kobra X."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Anycubic Kobra X options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data | self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
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
