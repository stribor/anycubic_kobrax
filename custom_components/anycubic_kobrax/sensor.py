"""Sensors for Anycubic Kobra X."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_BED_TEMP,
    ATTR_FILENAME,
    ATTR_NOZZLE_TEMP,
    ATTR_PRINT_STATE,
    ATTR_PROGRESS,
    ATTR_TARGET_BED_TEMP,
    ATTR_TARGET_NOZZLE_TEMP,
)
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity


@dataclass(frozen=True, slots=True)
class AnycubicSensorDescription:
    """Describe an Anycubic sensor."""

    key: str
    translation_key: str
    device_class: SensorDeviceClass | None = None
    native_unit_of_measurement: str | None = None
    state_class: SensorStateClass | None = None


SENSORS = (
    AnycubicSensorDescription(ATTR_PRINT_STATE, "print_state"),
    AnycubicSensorDescription(
        ATTR_PROGRESS,
        "progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(ATTR_FILENAME, "filename"),
    AnycubicSensorDescription(
        ATTR_NOZZLE_TEMP,
        "nozzle_temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
        SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_BED_TEMP,
        "bed_temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
        SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_TARGET_NOZZLE_TEMP,
        "target_nozzle_temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
        SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_TARGET_BED_TEMP,
        "target_bed_temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
        SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Anycubic Kobra X sensors."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    async_add_entities(
        AnycubicKobraXSensor(coordinator, description) for description in SENSORS
    )


class AnycubicKobraXSensor(AnycubicKobraXEntity, SensorEntity):
    """Sensor backed by normalized coordinator data."""

    entity_description: AnycubicSensorDescription

    def __init__(
        self,
        coordinator: AnycubicKobraXCoordinator,
        description: AnycubicSensorDescription,
    ) -> None:
        """Initialize a sensor."""
        super().__init__(coordinator, description.translation_key)
        self.entity_description = description
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_state_class = description.state_class

    @property
    def native_value(self) -> Any:
        """Return the native sensor value."""
        return self.coordinator.data.get(self.entity_description.key)
