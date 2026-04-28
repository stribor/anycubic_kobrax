"""Frontend assets for Anycubic Kobra X."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, FRONTEND_FOLDER

CARD_URL = f"/{DOMAIN}_card_static"
BRAND_URL = f"/{DOMAIN}_brand_static"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve dashboard card assets."""
    integration_dir = Path(__file__).parent

    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    CARD_URL,
                    str(integration_dir / FRONTEND_FOLDER),
                    cache_headers=False,
                ),
                StaticPathConfig(
                    BRAND_URL,
                    str(integration_dir / "brand"),
                    cache_headers=True,
                ),
            ]
        )
    except RuntimeError as err:
        if "already registered" not in str(err):
            raise
