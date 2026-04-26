"""Base entity for Anycubic Kobra X."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AnycubicKobraXCoordinator


class AnycubicKobraXEntity(CoordinatorEntity[AnycubicKobraXCoordinator]):
    """Base entity for Anycubic Kobra X."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AnycubicKobraXCoordinator, translation_key: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{coordinator.device.printer_id}_{translation_key}"
        )
        self._attr_device_info = DeviceInfo(**coordinator.device_info)
