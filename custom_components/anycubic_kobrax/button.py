"""Button platform for Anycubic Kobra X."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity


@dataclass(frozen=True, kw_only=True)
class AnycubicButtonDescription(ButtonEntityDescription):
    """Describe an Anycubic button."""

    action: str = "move"
    axis: int | None = None
    move_type: int | None = None
    distance: int | None = None
    temperature: int | None = None


BUTTONS = (
    AnycubicButtonDescription(
        key="home_xy",
        translation_key="home_xy",
        axis=4,
        move_type=2,
        distance=0,
    ),
    AnycubicButtonDescription(
        key="home_z",
        translation_key="home_z",
        axis=3,
        move_type=2,
        distance=0,
    ),
    AnycubicButtonDescription(
        key="home_xyz",
        translation_key="home_xyz",
        axis=5,
        move_type=2,
        distance=0,
    ),
    AnycubicButtonDescription(
        key="move_x_minus_1",
        translation_key="move_x_minus_1",
        axis=1,
        move_type=0,
        distance=1,
    ),
    AnycubicButtonDescription(
        key="move_x_plus_1",
        translation_key="move_x_plus_1",
        axis=1,
        move_type=1,
        distance=1,
    ),
    AnycubicButtonDescription(
        key="move_x_minus_15",
        translation_key="move_x_minus_15",
        axis=1,
        move_type=0,
        distance=15,
    ),
    AnycubicButtonDescription(
        key="move_x_plus_15",
        translation_key="move_x_plus_15",
        axis=1,
        move_type=1,
        distance=15,
    ),
    AnycubicButtonDescription(
        key="move_x_minus_50",
        translation_key="move_x_minus_50",
        axis=1,
        move_type=0,
        distance=50,
    ),
    AnycubicButtonDescription(
        key="move_x_plus_50",
        translation_key="move_x_plus_50",
        axis=1,
        move_type=1,
        distance=50,
    ),
    AnycubicButtonDescription(
        key="move_y_minus_1",
        translation_key="move_y_minus_1",
        axis=2,
        move_type=0,
        distance=1,
    ),
    AnycubicButtonDescription(
        key="move_y_plus_1",
        translation_key="move_y_plus_1",
        axis=2,
        move_type=1,
        distance=1,
    ),
    AnycubicButtonDescription(
        key="move_y_minus_15",
        translation_key="move_y_minus_15",
        axis=2,
        move_type=0,
        distance=15,
    ),
    AnycubicButtonDescription(
        key="move_y_plus_15",
        translation_key="move_y_plus_15",
        axis=2,
        move_type=1,
        distance=15,
    ),
    AnycubicButtonDescription(
        key="move_y_minus_50",
        translation_key="move_y_minus_50",
        axis=2,
        move_type=0,
        distance=50,
    ),
    AnycubicButtonDescription(
        key="move_y_plus_50",
        translation_key="move_y_plus_50",
        axis=2,
        move_type=1,
        distance=50,
    ),
    AnycubicButtonDescription(
        key="move_z_minus_1",
        translation_key="move_z_minus_1",
        axis=3,
        move_type=0,
        distance=1,
    ),
    AnycubicButtonDescription(
        key="move_z_plus_1",
        translation_key="move_z_plus_1",
        axis=3,
        move_type=1,
        distance=1,
    ),
    AnycubicButtonDescription(
        key="move_z_minus_15",
        translation_key="move_z_minus_15",
        axis=3,
        move_type=0,
        distance=15,
    ),
    AnycubicButtonDescription(
        key="move_z_plus_15",
        translation_key="move_z_plus_15",
        axis=3,
        move_type=1,
        distance=15,
    ),
    AnycubicButtonDescription(
        key="move_z_minus_50",
        translation_key="move_z_minus_50",
        axis=3,
        move_type=0,
        distance=50,
    ),
    AnycubicButtonDescription(
        key="move_z_plus_50",
        translation_key="move_z_plus_50",
        axis=3,
        move_type=1,
        distance=50,
    ),
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
        action="setNozzleTemperature",
        temperature=210,
    ),
    AnycubicButtonDescription(
        key="nozzle_temp_abs",
        translation_key="nozzle_temp_abs",
        action="setNozzleTemperature",
        temperature=230,
    ),
    AnycubicButtonDescription(
        key="preheat_pla",
        translation_key="preheat_pla",
        action="preheatPla",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Anycubic Kobra X buttons."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    async_add_entities(
        [AnycubicKobraXButton(coordinator, description) for description in BUTTONS]
    )


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

        if (
            self.entity_description.axis is None
            or self.entity_description.move_type is None
            or self.entity_description.distance is None
        ):
            return
        await self.hass.async_add_executor_job(
            self.coordinator.move_axis,
            self.entity_description.axis,
            self.entity_description.move_type,
            self.entity_description.distance,
        )
