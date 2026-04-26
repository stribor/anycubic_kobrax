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
    CONF_PRINTER_ID,
    CONF_STREAM_PATH,
    CONF_TYPE_ID,
    DEFAULT_MQTT_PASSWORD,
    DEFAULT_MQTT_USERNAME,
    DEFAULT_TYPE_ID,
    DOMAIN,
)


class AnycubicKobraXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Anycubic Kobra X config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AnycubicKobraXOptionsFlow:
        """Create the options flow."""
        return AnycubicKobraXOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            printer_id = user_input[CONF_PRINTER_ID].strip()
            await self.async_set_unique_id(printer_id)
            self._abort_if_unique_id_configured(updates={CONF_HOST: host})

            data = {
                CONF_HOST: host,
                CONF_TYPE_ID: int(user_input[CONF_TYPE_ID]),
                CONF_PRINTER_ID: printer_id,
                CONF_MQTT_USERNAME: user_input[CONF_MQTT_USERNAME].strip(),
                CONF_MQTT_PASSWORD: user_input[CONF_MQTT_PASSWORD],
            }
            if stream_path := user_input.get(CONF_STREAM_PATH):
                data[CONF_STREAM_PATH] = stream_path.strip()

            return self.async_create_entry(title=f"Anycubic {host}", data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TYPE_ID, default=DEFAULT_TYPE_ID): int,
                vol.Required(CONF_PRINTER_ID): str,
                vol.Required(
                    CONF_MQTT_USERNAME, default=DEFAULT_MQTT_USERNAME
                ): str,
                vol.Required(
                    CONF_MQTT_PASSWORD, default=DEFAULT_MQTT_PASSWORD
                ): str,
                vol.Optional(CONF_STREAM_PATH): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )


class AnycubicKobraXOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Anycubic Kobra X."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Anycubic Kobra X options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.options | self.config_entry.data
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
