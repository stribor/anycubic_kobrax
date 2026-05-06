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
    ATTR_AXIS_CODE,
    ATTR_AXIS_MESSAGE,
    ATTR_AXIS_STATE,
    ATTR_BED_TEMP,
    ATTR_BOX_FAN_SPEED,
    ATTR_CAMERA_AVAILABLE,
    ATTR_DEVICE_CN,
    ATTR_DEVICE_USN,
    ATTR_DEVICE_ZONE,
    ATTR_ESTIMATE_DURATION,
    ATTR_ESTIMATE_WEIGHT,
    ATTR_FAN_SPEED,
    ATTR_FILENAME,
    ATTR_FILAMENT_USED,
    ATTR_FILE_ROOT,
    ATTR_FIRMWARE_VERSION,
    ATTR_GCODE_SIZE,
    ATTR_IP_ADDRESS,
    ATTR_LAST_TOPIC,
    ATTR_LAST_WILL,
    ATTR_LAYER,
    ATTR_LOADED_SLOT,
    ATTR_MATERIAL,
    ATTR_MODEL,
    ATTR_MODEL_ID,
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
    ATTR_SLICER,
    ATTR_SLOT_COLOR,
    ATTR_SLOT_COLOR_ALPHA,
    ATTR_SLOT_COLOR_RGB,
    ATTR_SLOT_PERCENT,
    ATTR_SLOT_SKU,
    ATTR_SLOT_STATUS,
    ATTR_SLOT_TYPE,
    ATTR_SLOT_WEIGHT,
    ATTR_TARGET_BED_TEMP,
    ATTR_TARGET_NOZZLE_TEMP,
    ATTR_TASK_ID,
    ATTR_TOTAL_LAYER,
    ATTR_TOTAL_TIME,
    ATTR_USB_DISK,
    ATTR_VIDEO_STATE,
    ATTR_WIFI_SIGNAL,
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
    AnycubicSensorDescription(key=ATTR_AXIS_STATE, translation_key="axis_state"),
    AnycubicSensorDescription(key=ATTR_AXIS_CODE, translation_key="axis_code"),
    AnycubicSensorDescription(key=ATTR_AXIS_MESSAGE, translation_key="axis_message"),
    AnycubicSensorDescription(key=ATTR_PRINT_STATE, translation_key="print_state"),
    AnycubicSensorDescription(key=ATTR_PRINTER_NAME, translation_key="printer_name"),
    AnycubicSensorDescription(key=ATTR_MODEL, translation_key="model"),
    AnycubicSensorDescription(
        key=ATTR_MODEL_ID,
        translation_key="model_id",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AnycubicSensorDescription(
        key=ATTR_DEVICE_CN,
        translation_key="device_cn",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_DEVICE_USN,
        translation_key="device_usn",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_DEVICE_ZONE,
        translation_key="device_zone",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
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
    AnycubicSensorDescription(key=ATTR_TASK_ID, translation_key="task_id"),
    AnycubicSensorDescription(key=ATTR_FILE_ROOT, translation_key="file_root"),
    AnycubicSensorDescription(key=ATTR_MATERIAL, translation_key="material"),
    AnycubicSensorDescription(
        key=ATTR_FILAMENT_USED,
        translation_key="filament_used",
        native_unit_of_measurement="m",
    ),
    AnycubicSensorDescription(
        key=ATTR_ESTIMATE_DURATION,
        translation_key="estimate_duration",
        native_unit_of_measurement="s",
    ),
    AnycubicSensorDescription(
        key=ATTR_ESTIMATE_WEIGHT,
        translation_key="estimate_weight",
        native_unit_of_measurement="g",
    ),
    AnycubicSensorDescription(
        key=ATTR_GCODE_SIZE,
        translation_key="gcode_size",
        native_unit_of_measurement="B",
    ),
    AnycubicSensorDescription(
        key=ATTR_WIFI_SIGNAL,
        translation_key="wifi_signal",
        native_unit_of_measurement="dBm",
    ),
    AnycubicSensorDescription(key=ATTR_SLICER, translation_key="slicer"),
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
    *(
        description
        for slot in range(1, 5)
        for description in (
            AnycubicSensorDescription(
                key=ATTR_SLOT_TYPE[slot - 1],
                translation_key=f"slot_{slot}_type",
            ),
            AnycubicSensorDescription(
                key=ATTR_SLOT_STATUS[slot - 1],
                translation_key=f"slot_{slot}_status",
            ),
            AnycubicSensorDescription(
                key=ATTR_SLOT_PERCENT[slot - 1],
                translation_key=f"slot_{slot}_percent",
                native_unit_of_measurement=PERCENTAGE,
            ),
            AnycubicSensorDescription(
                key=ATTR_SLOT_WEIGHT[slot - 1],
                translation_key=f"slot_{slot}_weight",
                native_unit_of_measurement="g",
            ),
            AnycubicSensorDescription(
                key=ATTR_SLOT_SKU[slot - 1],
                translation_key=f"slot_{slot}_sku",
            ),
            AnycubicSensorDescription(
                key=ATTR_SLOT_COLOR[slot - 1],
                translation_key=f"slot_{slot}_color",
            ),
        )
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
            key = self.entity_description.key
            if key in ATTR_SLOT_COLOR:
                index = ATTR_SLOT_COLOR.index(key)
                attrs: dict[str, Any] = {}
                rgb = self.coordinator.data.get(ATTR_SLOT_COLOR_RGB[index])
                alpha = self.coordinator.data.get(ATTR_SLOT_COLOR_ALPHA[index])
                if rgb is not None:
                    attrs["rgb"] = rgb
                if alpha is not None:
                    attrs["alpha"] = alpha
                return attrs or None
            return None
        payload = self.coordinator.data.get("last_payload")
        return {"payload": payload} if payload is not None else None
