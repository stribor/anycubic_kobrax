"""Sensors for Anycubic Kobra X."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_AUX_FAN_SPEED,
    ATTR_BED_TEMP,
    ATTR_BOX_FAN_SPEED,
    ATTR_FAN_SPEED,
    ATTR_FILENAME,
    ATTR_LAST_TOPIC,
    ATTR_LAST_WILL,
    ATTR_LAYER,
    ATTR_MATERIAL,
    ATTR_NOZZLE_TEMP,
    ATTR_PRINT_STATE,
    ATTR_PRINT_SPEED,
    ATTR_PROGRESS,
    ATTR_REMAINING_TIME,
    ATTR_TARGET_BED_TEMP,
    ATTR_TARGET_NOZZLE_TEMP,
    ATTR_TOTAL_LAYER,
    ATTR_TOTAL_TIME,
)
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AnycubicSensorDescription:
    """Describe an Anycubic sensor."""

    key: str
    translation_key: str
    device_class: SensorDeviceClass | None = None
    native_unit_of_measurement: str | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    diagnostic_payload: bool = False


SENSORS = (
    AnycubicSensorDescription(ATTR_LAST_WILL, "last_will"),
    AnycubicSensorDescription(ATTR_PRINT_STATE, "print_state"),
    AnycubicSensorDescription(
        ATTR_PROGRESS,
        "progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(ATTR_FILENAME, "filename"),
    AnycubicSensorDescription(ATTR_MATERIAL, "material"),
    AnycubicSensorDescription(
        ATTR_PRINT_SPEED,
        "print_speed",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_REMAINING_TIME,
        "remaining_time",
        SensorDeviceClass.DURATION,
        UnitOfTime.SECONDS,
        SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_TOTAL_TIME,
        "total_time",
        SensorDeviceClass.DURATION,
        UnitOfTime.SECONDS,
        SensorStateClass.MEASUREMENT,
    ),
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
    AnycubicSensorDescription(
        ATTR_FAN_SPEED,
        "fan_speed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_AUX_FAN_SPEED,
        "aux_fan_speed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_BOX_FAN_SPEED,
        "box_fan_speed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_LAYER,
        "layer",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_TOTAL_LAYER,
        "total_layer",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AnycubicSensorDescription(
        ATTR_LAST_TOPIC,
        "last_mqtt_message",
        entity_category=EntityCategory.DIAGNOSTIC,
        diagnostic_payload=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Anycubic Kobra X sensors."""
    coordinator: AnycubicKobraXCoordinator = entry.runtime_data
    _LOGGER.info("Setting up %s Anycubic Kobra X sensors", len(SENSORS))
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
        self._attr_entity_category = description.entity_category

    @property
    def native_value(self) -> Any:
        """Return the native sensor value."""
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return diagnostic MQTT payload attributes."""
        if not self.entity_description.diagnostic_payload:
            return None
        payload = self.coordinator.data.get("last_payload")
        return {"payload": payload} if payload is not None else None
