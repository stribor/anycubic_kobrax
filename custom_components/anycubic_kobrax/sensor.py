"""Sensors for Anycubic Kobra X."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_AUX_FAN_SPEED,
    ATTR_BED_TEMP,
    ATTR_BOX_FAN_SPEED,
    ATTR_CAMERA_AVAILABLE,
    ATTR_FAN_SPEED,
    ATTR_FILENAME,
    ATTR_FIRMWARE_VERSION,
    ATTR_IP_ADDRESS,
    ATTR_LAST_TOPIC,
    ATTR_LAST_WILL,
    ATTR_LAYER,
    ATTR_LOADED_SLOT,
    ATTR_MATERIAL,
    ATTR_MODEL,
    ATTR_MULTI_COLOR_BOX,
    ATTR_MULTI_COLOR_BOX_HUMIDITY,
    ATTR_MULTI_COLOR_BOX_STATUS,
    ATTR_MULTI_COLOR_BOX_TEMP,
    ATTR_NOZZLE_TEMP,
    ATTR_PRINTER_NAME,
    ATTR_PRINT_STATE,
    ATTR_PRINT_SPEED,
    ATTR_PRINT_SPEED_MODE,
    ATTR_PROGRESS,
    ATTR_REMAINING_TIME,
    ATTR_TARGET_BED_TEMP,
    ATTR_TARGET_NOZZLE_TEMP,
    ATTR_TOTAL_LAYER,
    ATTR_TOTAL_TIME,
    ATTR_USB_DISK,
    ATTR_VIDEO_STATE,
)
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AnycubicSensorDescription(SensorEntityDescription):
    """Describe an Anycubic sensor."""

    diagnostic_payload: bool = False


SENSORS = (
    AnycubicSensorDescription(key=ATTR_LAST_WILL, translation_key="last_will"),
    AnycubicSensorDescription(key=ATTR_PRINT_STATE, translation_key="print_state"),
    AnycubicSensorDescription(key=ATTR_PRINTER_NAME, translation_key="printer_name"),
    AnycubicSensorDescription(key=ATTR_MODEL, translation_key="model"),
    AnycubicSensorDescription(
        key=ATTR_FIRMWARE_VERSION, translation_key="firmware_version"
    ),
    AnycubicSensorDescription(key=ATTR_IP_ADDRESS, translation_key="ip_address"),
    AnycubicSensorDescription(
        key=ATTR_PROGRESS,
        translation_key="progress",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AnycubicSensorDescription(key=ATTR_FILENAME, translation_key="filename"),
    AnycubicSensorDescription(key=ATTR_MATERIAL, translation_key="material"),
    AnycubicSensorDescription(
        key=ATTR_PRINT_SPEED,
        translation_key="print_speed",
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINT_SPEED_MODE,
        translation_key="print_speed_mode",
    ),
    AnycubicSensorDescription(
        key=ATTR_REMAINING_TIME,
        translation_key="remaining_time",
        native_unit_of_measurement="s",
    ),
    AnycubicSensorDescription(
        key=ATTR_TOTAL_TIME,
        translation_key="total_time",
        native_unit_of_measurement="s",
    ),
    AnycubicSensorDescription(
        key=ATTR_NOZZLE_TEMP,
        translation_key="nozzle_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AnycubicSensorDescription(
        key=ATTR_BED_TEMP,
        translation_key="bed_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AnycubicSensorDescription(
        key=ATTR_TARGET_NOZZLE_TEMP,
        translation_key="target_nozzle_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AnycubicSensorDescription(
        key=ATTR_TARGET_BED_TEMP,
        translation_key="target_bed_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AnycubicSensorDescription(
        key=ATTR_FAN_SPEED,
        translation_key="fan_speed",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AnycubicSensorDescription(
        key=ATTR_AUX_FAN_SPEED,
        translation_key="aux_fan_speed",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AnycubicSensorDescription(
        key=ATTR_BOX_FAN_SPEED,
        translation_key="box_fan_speed",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AnycubicSensorDescription(
        key=ATTR_CAMERA_AVAILABLE, translation_key="camera_available"
    ),
    AnycubicSensorDescription(key=ATTR_USB_DISK, translation_key="usb_disk"),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX, translation_key="multi_color_box"
    ),
    AnycubicSensorDescription(key=ATTR_VIDEO_STATE, translation_key="video_state"),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_STATUS,
        translation_key="multi_color_box_status",
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_TEMP,
        translation_key="multi_color_box_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_HUMIDITY,
        translation_key="multi_color_box_humidity",
        native_unit_of_measurement=PERCENTAGE,
    ),
    AnycubicSensorDescription(
        key=ATTR_LOADED_SLOT,
        translation_key="loaded_slot",
    ),
    AnycubicSensorDescription(
        key=ATTR_LAYER,
        translation_key="layer",
    ),
    AnycubicSensorDescription(
        key=ATTR_TOTAL_LAYER,
        translation_key="total_layer",
    ),
    AnycubicSensorDescription(
        key=ATTR_LAST_TOPIC,
        translation_key="last_mqtt_message",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
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
        [AnycubicKobraXSensor(coordinator, description) for description in SENSORS]
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
