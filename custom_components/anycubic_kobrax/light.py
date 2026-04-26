"""Light platform for Anycubic Kobra X."""

from __future__ import annotations

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_LIGHT_BRIGHTNESS
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Anycubic Kobra X light."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    async_add_entities([AnycubicKobraXLight(coordinator)])


class AnycubicKobraXLight(AnycubicKobraXEntity, LightEntity):
    """Printer chamber light."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_features = LightEntityFeature(0)

    def __init__(self, coordinator: AnycubicKobraXCoordinator) -> None:
        """Initialize the printer light."""
        super().__init__(coordinator, "light")

    @property
    def is_on(self) -> bool | None:
        """Return true if the light is on."""
        brightness = self.coordinator.data.get(ATTR_LIGHT_BRIGHTNESS)
        if brightness is None:
            return None
        return int(brightness) > 0

    @property
    def brightness(self) -> int | None:
        """Return brightness in Home Assistant's 0-255 range."""
        brightness = self.coordinator.data.get(ATTR_LIGHT_BRIGHTNESS)
        if brightness is None:
            return None
        return round(max(0, min(100, int(brightness))) * 255 / 100)

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is None:
            anycubic_brightness = 100
        else:
            anycubic_brightness = round(int(brightness) * 100 / 255)
        await self.hass.async_add_executor_job(
            self.coordinator.control_light, anycubic_brightness
        )

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the light off."""
        await self.hass.async_add_executor_job(self.coordinator.control_light, 0)
