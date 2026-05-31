"""Button platform for Anycubic Kobra X."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity

_ICON_PRINTER_3D = "mdi:printer-3d"
_ICON_PRINTER_3D_OFF = "mdi:printer-3d-off"
_ICON_NOZZLE_HEAT = "mdi:printer-3d-nozzle-heat"


@dataclass(frozen=True, kw_only=True)
class AnycubicButtonDescription(ButtonEntityDescription):
    """Describe an Anycubic button."""

    action: str = ""
    temperature: int | None = None


BUTTONS = (
    AnycubicButtonDescription(
        key="motors_off",
        translation_key="motors_off",
        action="turnOff",
    ),
    AnycubicButtonDescription(
        key="bed_temp_pla",
        translation_key="bed_temp_pla",
        action="setBedTemperature",
        temperature=60,
    ),
    AnycubicButtonDescription(
        key="bed_temp_abs",
        translation_key="bed_temp_abs",
        action="setBedTemperature",
        temperature=90,
    ),
    AnycubicButtonDescription(
        key="nozzle_temp_pla",
        translation_key="nozzle_temp_pla",
        icon=_ICON_NOZZLE_HEAT,
        action="setNozzleTemperature",
        temperature=210,
    ),
    AnycubicButtonDescription(
        key="nozzle_temp_abs",
        translation_key="nozzle_temp_abs",
        icon=_ICON_NOZZLE_HEAT,
        action="setNozzleTemperature",
        temperature=230,
    ),
    AnycubicButtonDescription(
        key="preheat_pla",
        translation_key="preheat_pla",
        icon=_ICON_NOZZLE_HEAT,
        action="preheatPla",
    ),
    AnycubicButtonDescription(
        key="pause_print",
        translation_key="pause_print",
        action="pausePrint",
    ),
    AnycubicButtonDescription(
        key="resume_print",
        translation_key="resume_print",
        icon=_ICON_PRINTER_3D,
        action="resumePrint",
    ),
    AnycubicButtonDescription(
        key="stop_print",
        translation_key="stop_print",
        icon=_ICON_PRINTER_3D_OFF,
        action="stopPrint",
    ),
)

OBSOLETE_AXIS_BUTTON_KEYS = frozenset(
    {
        "home_xy",
        "home_z",
        "home_xyz",
        "move_x_minus_1",
        "move_x_plus_1",
        "move_x_minus_15",
        "move_x_plus_15",
        "move_x_minus_50",
        "move_x_plus_50",
        "move_y_minus_1",
        "move_y_plus_1",
        "move_y_minus_15",
        "move_y_plus_15",
        "move_y_minus_50",
        "move_y_plus_50",
        "move_z_minus_1",
        "move_z_plus_1",
        "move_z_minus_15",
        "move_z_plus_15",
        "move_z_minus_50",
        "move_z_plus_50",
    }
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Anycubic Kobra X buttons."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    _async_remove_obsolete_axis_buttons(hass, entry, coordinator)
    async_add_entities(
        [AnycubicKobraXButton(coordinator, description) for description in BUTTONS]
    )


def _async_remove_obsolete_axis_buttons(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: AnycubicKobraXCoordinator
) -> None:
    """Remove registry entries for axis buttons replaced by services."""
    entity_registry = er.async_get(hass)
    obsolete_unique_ids = {
        f"{coordinator.device.printer_id}_{key}" for key in OBSOLETE_AXIS_BUTTON_KEYS
    }

    for entity_entry in er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    ):
        if (
            entity_entry.entity_id.startswith("button.")
            and entity_entry.platform == DOMAIN
            and entity_entry.unique_id in obsolete_unique_ids
        ):
            entity_registry.async_remove(entity_entry.entity_id)


class AnycubicKobraXButton(AnycubicKobraXEntity, ButtonEntity):
    """Button that sends a momentary printer command."""

    entity_description: AnycubicButtonDescription

    def __init__(
        self,
        coordinator: AnycubicKobraXCoordinator,
        description: AnycubicButtonDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description.translation_key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Press the button."""
        if self.entity_description.action == "turnOff":
            await self.hass.async_add_executor_job(
                self.coordinator.turn_off_axis_motors
            )
            return

        if self.entity_description.action == "setBedTemperature":
            if self.entity_description.temperature is None:
                return
            await self.hass.async_add_executor_job(
                self.coordinator.set_bed_temperature,
                self.entity_description.temperature,
            )
            return

        if self.entity_description.action == "setNozzleTemperature":
            if self.entity_description.temperature is None:
                return
            await self.hass.async_add_executor_job(
                self.coordinator.set_nozzle_temperature,
                self.entity_description.temperature,
            )
            return

        if self.entity_description.action == "preheatPla":
            await self.hass.async_add_executor_job(self.coordinator.preheat_pla)
            return

        if self.entity_description.action == "pausePrint":
            await self.hass.async_add_executor_job(self.coordinator.pause_print)
            return

        if self.entity_description.action == "resumePrint":
            await self.hass.async_add_executor_job(self.coordinator.resume_print)
            return

        if self.entity_description.action == "stopPrint":
            await self.hass.async_add_executor_job(self.coordinator.stop_print)
            return
