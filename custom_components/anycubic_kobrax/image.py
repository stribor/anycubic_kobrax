"""Image entities for Anycubic Kobra X."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Anycubic image entities."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    async_add_entities(
        [
            AnycubicKobraXPreviewImage(hass, coordinator),
            AnycubicKobraXThumbnailImage(hass, coordinator),
        ]
    )


class AnycubicKobraXPreviewImage(AnycubicKobraXEntity, ImageEntity):
    """Show the last preview image reported in file metadata."""

    def __init__(
        self, hass: HomeAssistant, coordinator: AnycubicKobraXCoordinator
    ) -> None:
        """Initialize the preview image entity."""
        AnycubicKobraXEntity.__init__(self, coordinator, "preview_image")
        ImageEntity.__init__(self, hass)

    @property
    def available(self) -> bool:
        """Return whether a preview image is available."""
        return super().available and self.coordinator.preview_image is not None

    @property
    def content_type(self) -> str:
        """Return the preview image content type."""
        return self.coordinator.preview_image_content_type

    @property
    def image_last_updated(self) -> datetime | None:
        """Return when the preview image last changed."""
        return self.coordinator.preview_image_updated

    async def async_image(self) -> bytes | None:
        """Return the latest decoded preview image."""
        return self.coordinator.preview_image


class AnycubicKobraXThumbnailImage(AnycubicKobraXEntity, ImageEntity):
    """Show the last thumbnail image reported in file metadata."""

    def __init__(
        self, hass: HomeAssistant, coordinator: AnycubicKobraXCoordinator
    ) -> None:
        """Initialize the thumbnail image entity."""
        AnycubicKobraXEntity.__init__(self, coordinator, "thumbnail_image")
        ImageEntity.__init__(self, hass)

    @property
    def available(self) -> bool:
        """Return whether a thumbnail image is available."""
        return super().available and self.coordinator.thumbnail_image is not None

    @property
    def content_type(self) -> str:
        """Return the thumbnail image content type."""
        return self.coordinator.thumbnail_image_content_type

    @property
    def image_last_updated(self) -> datetime | None:
        """Return when the thumbnail image last changed."""
        return self.coordinator.thumbnail_image_updated

    async def async_image(self) -> bytes | None:
        """Return the latest decoded thumbnail image."""
        return self.coordinator.thumbnail_image
