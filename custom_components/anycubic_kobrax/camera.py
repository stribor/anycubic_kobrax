"""Camera platform for Anycubic Kobra X."""

from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Anycubic Kobra X camera."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    async_add_entities([AnycubicKobraXCamera(coordinator)])


class AnycubicKobraXCamera(AnycubicKobraXEntity, Camera):
    """FFmpeg-backed FLV camera stream for the printer."""

    _attr_supported_features = CameraEntityFeature.STREAM | CameraEntityFeature.ON_OFF
    _attr_is_streaming = False

    def __init__(self, coordinator: AnycubicKobraXCoordinator) -> None:
        """Initialize the camera."""
        AnycubicKobraXEntity.__init__(self, coordinator, "camera")
        Camera.__init__(self)

    async def stream_source(self) -> str | None:
        """Return the current FLV stream URL for ffmpeg."""
        if self.coordinator.stream_url() is None:
            await self.async_turn_on()
        return self.coordinator.stream_url()

    async def async_turn_on(self) -> None:
        """Start camera capture."""
        await self.hass.async_add_executor_job(self.coordinator.start_video)
        self._attr_is_streaming = True

    async def async_turn_off(self) -> None:
        """Stop camera capture."""
        await self.hass.async_add_executor_job(self.coordinator.stop_video)
        self._attr_is_streaming = False
