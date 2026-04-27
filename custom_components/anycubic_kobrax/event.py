"""Event entities for Anycubic Kobra X."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import EVENT_TYPES
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Anycubic Kobra X event entities."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    async_add_entities([AnycubicKobraXPrinterEvent(coordinator)])


class AnycubicKobraXPrinterEvent(AnycubicKobraXEntity, EventEntity):
    """Printer event stream."""

    _attr_event_types = EVENT_TYPES

    def __init__(self, coordinator: AnycubicKobraXCoordinator) -> None:
        """Initialize the printer event entity."""
        super().__init__(coordinator, "printer_event")
        self._last_sequence = 0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Trigger a Home Assistant event for new printer events."""
        event = self.coordinator.latest_event
        if event is not None and event["sequence"] != self._last_sequence:
            self._last_sequence = event["sequence"]
            self._trigger_event(
                event["event_type"],
                event.get("data") or {},
            )
        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return latest event data as attributes."""
        event = self.coordinator.latest_event
        if event is None:
            return None
        return event.get("data") or None
