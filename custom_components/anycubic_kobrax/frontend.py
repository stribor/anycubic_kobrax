"""Frontend assets for Anycubic Kobra X."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import CARD_FILENAME, CARD_VERSION, DOMAIN, FRONTEND_FOLDER

CARD_URL = f"/{DOMAIN}_card_static"
BRAND_URL = f"/{DOMAIN}_brand_static"
CARD_RESOURCE_URL = f"{CARD_URL}/{CARD_FILENAME}"
CARD_RESOURCE_VERSIONED_URL = f"{CARD_RESOURCE_URL}?v={CARD_VERSION}"

_LOGGER = logging.getLogger(__name__)


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

    await _async_register_lovelace_resource(hass)


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the dashboard card resource for storage-mode Lovelace."""
    lovelace_data = hass.data.get(LOVELACE_DATA)
    if lovelace_data is None:
        _LOGGER.debug("Lovelace data is not available; skipping card resource setup")
        return

    if lovelace_data.resource_mode != MODE_STORAGE:
        _LOGGER.info(
            "Lovelace resource mode is YAML; add %s manually as a module resource",
            CARD_RESOURCE_VERSIONED_URL,
        )
        return

    resources = lovelace_data.resources
    await resources.async_get_info()

    for resource in resources.async_items():
        url = resource.get("url", "")
        if url.split("?", 1)[0] != CARD_RESOURCE_URL:
            continue
        if url != CARD_RESOURCE_VERSIONED_URL:
            await resources.async_update_item(
                resource["id"],
                {
                    "res_type": "module",
                    "url": CARD_RESOURCE_VERSIONED_URL,
                },
            )
        return

    await resources.async_create_item(
        {
            "res_type": "module",
            "url": CARD_RESOURCE_VERSIONED_URL,
        }
    )
