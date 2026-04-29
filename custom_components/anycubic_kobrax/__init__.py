"""Home Assistant integration for Anycubic Kobra X FDM printers."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import AnycubicKobraXCoordinator
from .frontend import async_register_frontend
from .services import async_setup_services


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up Anycubic Kobra X from a config entry."""
    coordinator = AnycubicKobraXCoordinator(hass, entry)
    try:
        await coordinator.async_setup()
    except (ConnectionError, OSError, TimeoutError) as err:
        raise ConfigEntryNotReady(f"Could not connect to Anycubic printer: {err}") from err
    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_setup_services(hass)
    await async_register_frontend(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload an Anycubic Kobra X config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Reload the integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
