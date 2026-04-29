"""Home Assistant services for Anycubic Kobra X."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_AXIS,
    CONF_CONFIG_ENTRY_ID,
    CONF_X,
    CONF_Y,
    CONF_Z,
    DATA_SERVICE_REGISTERED,
    DOMAIN,
    SERVICE_HOME_AXIS,
    SERVICE_MOTORS_OFF,
    SERVICE_MOVE_AXIS,
)
from .coordinator import AnycubicKobraXCoordinator

_MOVE_AXIS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CONFIG_ENTRY_ID): cv.string,
        vol.Optional(CONF_X, default=0): vol.Coerce(float),
        vol.Optional(CONF_Y, default=0): vol.Coerce(float),
        vol.Optional(CONF_Z, default=0): vol.Coerce(float),
    }
)

_HOME_AXIS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CONFIG_ENTRY_ID): cv.string,
        vol.Required(CONF_AXIS): vol.In(("xy", "z", "xyz")),
    }
)

_MOTORS_OFF_SCHEMA = vol.Schema({vol.Optional(CONF_CONFIG_ENTRY_ID): cv.string})


def async_setup_services(hass: HomeAssistant) -> None:
    """Register Anycubic Kobra X services once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_SERVICE_REGISTERED):
        return
    domain_data[DATA_SERVICE_REGISTERED] = True

    async def async_move_axis(call: ServiceCall) -> None:
        coordinator = _coordinator_from_call(hass, call.data)
        await hass.async_add_executor_job(
            coordinator.move_relative,
            call.data[CONF_X],
            call.data[CONF_Y],
            call.data[CONF_Z],
        )

    async def async_home_axis(call: ServiceCall) -> None:
        coordinator = _coordinator_from_call(hass, call.data)
        await hass.async_add_executor_job(
            coordinator.home_axis_group,
            call.data[CONF_AXIS],
        )

    async def async_motors_off(call: ServiceCall) -> None:
        coordinator = _coordinator_from_call(hass, call.data)
        await hass.async_add_executor_job(coordinator.turn_off_axis_motors)

    hass.services.async_register(
        DOMAIN,
        SERVICE_MOVE_AXIS,
        async_move_axis,
        schema=_MOVE_AXIS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_HOME_AXIS,
        async_home_axis,
        schema=_HOME_AXIS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MOTORS_OFF,
        async_motors_off,
        schema=_MOTORS_OFF_SCHEMA,
    )


def _coordinator_from_call(
    hass: HomeAssistant, data: dict[str, Any]
) -> AnycubicKobraXCoordinator:
    """Return the coordinator targeted by a service call."""
    domain_data = hass.data.get(DOMAIN, {})
    config_entry_id = data.get(CONF_CONFIG_ENTRY_ID)
    if config_entry_id:
        coordinator = domain_data.get(config_entry_id)
        if isinstance(coordinator, AnycubicKobraXCoordinator):
            return coordinator
        raise HomeAssistantError(
            f"No Anycubic Kobra X config entry found for {config_entry_id}"
        )

    coordinators = [
        value
        for key, value in domain_data.items()
        if key != DATA_SERVICE_REGISTERED
        and isinstance(value, AnycubicKobraXCoordinator)
    ]
    if len(coordinators) == 1:
        return coordinators[0]
    if not coordinators:
        raise HomeAssistantError("No Anycubic Kobra X printer is loaded")
    raise HomeAssistantError(
        "config_entry_id is required when multiple Anycubic Kobra X printers "
        "are loaded"
    )
