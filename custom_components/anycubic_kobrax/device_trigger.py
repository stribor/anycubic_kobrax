"""Device triggers for Anycubic Kobra X."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import CONF_CONFIG_ENTRY_ID, DOMAIN, EVENT_TYPES

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_CONFIG_ENTRY_ID): cv.string,
        vol.Required(CONF_TYPE): vol.In(EVENT_TYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return available Anycubic Kobra X device triggers."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        return []

    triggers: list[dict[str, Any]] = []
    for entry_id in device.config_entries:
        if entry_id not in hass.data.get(DOMAIN, {}):
            continue
        triggers.extend(
            {
                CONF_PLATFORM: "device",
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_CONFIG_ENTRY_ID: entry_id,
                CONF_TYPE: event_type,
            }
            for event_type in EVENT_TYPES
        )
    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: dict[str, Any],
    action: Any,
    trigger_info: dict[str, Any],
) -> CALLBACK_TYPE:
    """Attach an Anycubic Kobra X device trigger."""
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: f"{DOMAIN}_printer_event",
            event_trigger.CONF_EVENT_DATA: {
                CONF_CONFIG_ENTRY_ID: config[CONF_CONFIG_ENTRY_ID],
                CONF_TYPE: config[CONF_TYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )
