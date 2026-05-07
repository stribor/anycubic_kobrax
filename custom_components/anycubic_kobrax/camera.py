"""Camera platform for Anycubic Kobra X."""

from __future__ import annotations

import asyncio

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_VIDEO_STATE
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
        self._allow_configured_stream = False

    async def stream_source(self) -> str | None:
        """Return the current FLV stream URL for ffmpeg."""
        if not self.is_streaming:
            return None
        if (
            stream_url := self.coordinator.stream_url(allow_configured=False)
        ) is not None:
            return stream_url
        await self.hass.async_add_executor_job(self.coordinator.refresh_stream_url)
        return self.coordinator.stream_url(
            allow_configured=self._allow_configured_stream
        )

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return no still image so camera cards do not show print previews."""
        return None

    @property
    def is_streaming(self) -> bool:
        """Return whether the printer reports video capture as active."""
        video_state = self.coordinator.data.get(ATTR_VIDEO_STATE)
        if video_state == "pushStarted":
            return True
        if video_state == "pushStopped":
            return False
        return self._attr_is_streaming

    async def async_turn_on(self) -> None:
        """Start camera capture."""
        self._allow_configured_stream = False
        await self.hass.async_add_executor_job(self.coordinator.start_video)
        self._attr_is_streaming = True
        for _ in range(16):
            if self.coordinator.stream_url(allow_configured=False) is not None:
                break
            await self.hass.async_add_executor_job(self.coordinator.refresh_stream_url)
            await asyncio.sleep(0.5)
        else:
            self._allow_configured_stream = True
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Stop camera capture."""
        await self.hass.async_add_executor_job(self.coordinator.stop_video)
        self._attr_is_streaming = False
        self._allow_configured_stream = False
        self.async_write_ha_state()
