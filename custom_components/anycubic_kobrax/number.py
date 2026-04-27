"""Number platform for Anycubic Kobra X."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_FAN_SPEED, ATTR_TARGET_BED_TEMP, ATTR_TARGET_NOZZLE_TEMP
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity


@dataclass(frozen=True, kw_only=True)
class AnycubicNumberDescription(NumberEntityDescription):
    """Describe an Anycubic number entity."""


NUMBERS = (
    AnycubicNumberDescription(
        key=ATTR_TARGET_BED_TEMP,
        translation_key="target_bed_temperature",
        native_min_value=0,
        native_max_value=120,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AnycubicNumberDescription(
        key=ATTR_TARGET_NOZZLE_TEMP,
        translation_key="target_nozzle_temperature",
        native_min_value=0,
        native_max_value=300,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AnycubicNumberDescription(
        key=ATTR_FAN_SPEED,
        translation_key="fan_speed",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Anycubic Kobra X number entities."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    async_add_entities(
        [AnycubicKobraXNumber(coordinator, description) for description in NUMBERS]
    )


class AnycubicKobraXNumber(AnycubicKobraXEntity, NumberEntity):
    """Number entity backed by printer target settings."""

    entity_description: AnycubicNumberDescription

    def __init__(
        self,
        coordinator: AnycubicKobraXCoordinator,
        description: AnycubicNumberDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, description.translation_key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the current target value."""
        return self.coordinator.data.get(self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        """Set the target temperature."""
        if self.entity_description.key == ATTR_FAN_SPEED:
            await self.hass.async_add_executor_job(
                self.coordinator.set_fan_speed,
                round(value),
            )
            return

        if self.entity_description.key == ATTR_TARGET_NOZZLE_TEMP:
            await self.hass.async_add_executor_job(
                self.coordinator.set_nozzle_temperature,
                round(value),
            )
            return

        await self.hass.async_add_executor_job(
            self.coordinator.set_bed_temperature, round(value)
        )
