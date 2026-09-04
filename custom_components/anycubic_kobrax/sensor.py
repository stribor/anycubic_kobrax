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
    ATTR_APP_VERSION,
    ATTR_AUTO_LEVELING_SUPPORT,
    ATTR_BED_TEMP,
    ATTR_BED_LEVELING,
    ATTR_BOX_FAN_SPEED,
    ATTR_CAMERA_AVAILABLE,
    ATTR_CAMERA_TIMELAPSE,
    ATTR_CAMERA_TIMELAPSE_SUPPORT,
    ATTR_DELETE_BATCH_SUPPORT,
    ATTR_DEVICE_CN,
    ATTR_DEVICE_USN,
    ATTR_DEVICE_ZONE,
    ATTR_DRYING_FIRST_SUPPORT,
    ATTR_ESTIMATE_DURATION,
    ATTR_ESTIMATE_WEIGHT,
    ATTR_FAN_SPEED,
    ATTR_FILENAME,
    ATTR_FILAMENT_USED,
    ATTR_FILE_ROOT,
    ATTR_FILE_UPLOAD_URL,
    ATTR_FIRMWARE_VERSION,
    ATTR_FLOW_CALIBRATION,
    ATTR_FLOW_CALIBRATION_SUPPORT,
    ATTR_FOREIGN_OBJECT_DETECTION,
    ATTR_FOREIGN_OBJECT_DETECTION_SUPPORT,
    ATTR_GCODE_SIZE,
    ATTR_GCODE_3MF_SUPPORT,
    ATTR_HEAD_TOOLS_MODEL,
    ATTR_IP_ADDRESS,
    ATTR_KEEP_PRINT_HEAD_TEMP_SUPPORT,
    ATTR_LAST_TOPIC,
    ATTR_LAST_WILL,
    ATTR_LAYER,
    ATTR_LOADED_SLOT,
    ATTR_LOCAL_TASK_ID,
    ATTR_MATERIAL,
    ATTR_MODEL,
    ATTR_MODEL_ID,
    ATTR_MULTI_COLOR_BOX,
    ATTR_MULTI_COLOR_BOX_AUTO_FEED,
    ATTR_MULTI_COLOR_BOX_DRYING_DURATION,
    ATTR_MULTI_COLOR_BOX_DRYING_REMAINING_TIME,
    ATTR_MULTI_COLOR_BOX_DRYING_STATUS,
    ATTR_MULTI_COLOR_BOX_DRYING_TARGET_TEMP,
    ATTR_MULTI_COLOR_BOX_FEED_CODE,
    ATTR_MULTI_COLOR_BOX_FEED_SLOT,
    ATTR_MULTI_COLOR_BOX_FEED_STATUS,
    ATTR_MULTI_COLOR_BOX_FEED_TYPE,
    ATTR_MULTI_COLOR_BOX_HUMIDITY,
    ATTR_MULTI_COLOR_BOX_ID,
    ATTR_MULTI_COLOR_BOX_MODEL_ID,
    ATTR_MULTI_COLOR_BOX_STATUS,
    ATTR_MULTI_COLOR_BOX_TEMP,
    ATTR_NOZZLE_TEMP,
    ATTR_PERIPHERAL_CODE,
    ATTR_PREHEATING_SUPPORT,
    ATTR_PRE_CANCEL_SUPPORT,
    ATTR_PRINT_FILAMENTS,
    ATTR_PRINT_FILAMENTS_WEIGHT,
    ATTR_PRINT_PARAMS,
    ATTR_PRINTER_NAME,
    ATTR_PRINTER_TYPE,
    ATTR_PRINT_STATE,
    ATTR_PRINT_SPEED,
    ATTR_PRINT_SPEED_MODE,
    ATTR_PRINT_STATUS,
    ATTR_PRINTER_EVENT_CODE,
    ATTR_PRINTER_EVENT_ERROR,
    ATTR_PROJECT_PAUSE,
    ATTR_PROJECT_TYPE,
    ATTR_PROGRESS,
    ATTR_REMAINING_TIME,
    ATTR_SHENGWANG_RDT_SUPPORT,
    ATTR_SHENGWANG_RTC_SUPPORT,
    ATTR_SLICER,
    ATTR_SLICER_VERSION,
    ATTR_SLICE_FILAMENTS,
    ATTR_SLOT_COLOR,
    ATTR_SLOT_COLOR_ALPHA,
    ATTR_SLOT_COLOR_RGB,
    ATTR_SLOT_PERCENT,
    ATTR_SLOT_SKU,
    ATTR_SLOT_STATUS,
    ATTR_SLOT_TYPE,
    ATTR_SLOT_WEIGHT,
    ATTR_SPAGHETTI_DETECTION,
    ATTR_STORAGE_TOTAL,
    ATTR_STORAGE_USED,
    ATTR_SUPPLIES_USAGE,
    ATTR_TARGET_BED_TEMP,
    ATTR_TARGET_NOZZLE_TEMP,
    ATTR_TASK_ID,
    ATTR_TIMELAPSE_PATH,
    ATTR_TOTAL_LAYER,
    ATTR_TOTAL_TIME,
    ATTR_TIME_LAPSE,
    ATTR_USB_DISK,
    ATTR_USB_PATH,
    ATTR_VIDEO_STATE,
    ATTR_VIBRATION_COMPENSATION_SUPPORT,
    ATTR_WIFI_SIGNAL,
    ATTR_SOURCE_MODEL_COUNT,
    ATTR_SOURCE_MODELS_FROM,
    ATTR_SOURCE_MODELS,
    ATTR_SOURCE_PLATE_INDEX,
    ATTR_SOURCE_SLICE_PROCESS,
    ATTR_TASK_SETTINGS,
    ATTR_Z_COMPENSATION,
)
from .coordinator import AnycubicKobraXCoordinator
from .entity import AnycubicKobraXEntity

_LOGGER = logging.getLogger(__name__)
_ICON_PRINTER_3D = "mdi:printer-3d"
_ICON_PRINTER_3D_OFF = "mdi:printer-3d-off"
_ICON_NOZZLE_ALERT = "mdi:printer-3d-nozzle-alert"
_ICON_NOZZLE_HEAT = "mdi:printer-3d-nozzle-heat"
_ICON_NOZZLE_HEAT_OUTLINE = "mdi:printer-3d-nozzle-heat-outline"
_ICON_NOZZLE_OFF = "mdi:printer-3d-nozzle-off"
_ICON_NOZZLE_OFF_OUTLINE = "mdi:printer-3d-nozzle-off-outline"
_ICON_NOZZLE_OUTLINE = "mdi:printer-3d-nozzle-outline"


@dataclass(frozen=True, kw_only=True)
class AnycubicSensorDescription(SensorEntityDescription):
    """Describe an Anycubic sensor."""

    diagnostic_payload: bool = False


SENSORS = (
    AnycubicSensorDescription(
        key=ATTR_LAST_WILL,
        translation_key="last_will",
        icon=_ICON_PRINTER_3D,
    ),
    AnycubicSensorDescription(key=ATTR_AXIS_STATE, translation_key="axis_state"),
    AnycubicSensorDescription(key=ATTR_AXIS_CODE, translation_key="axis_code"),
    AnycubicSensorDescription(key=ATTR_AXIS_MESSAGE, translation_key="axis_message"),
    AnycubicSensorDescription(
        key=ATTR_PRINT_STATE,
        translation_key="print_state",
        icon=_ICON_PRINTER_3D,
    ),
    AnycubicSensorDescription(key=ATTR_PRINTER_NAME, translation_key="printer_name"),
    AnycubicSensorDescription(
        key=ATTR_MODEL,
        translation_key="model",
        icon=_ICON_PRINTER_3D,
    ),
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
    AnycubicSensorDescription(
        key=ATTR_LOCAL_TASK_ID, translation_key="local_task_id"
    ),
    AnycubicSensorDescription(key=ATTR_FILE_ROOT, translation_key="file_root"),
    AnycubicSensorDescription(
        key=ATTR_FILE_UPLOAD_URL,
        translation_key="file_upload_url",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(key=ATTR_MATERIAL, translation_key="material"),
    AnycubicSensorDescription(
        key=ATTR_FILAMENT_USED,
        translation_key="filament_used",
        native_unit_of_measurement="g",
    ),
    AnycubicSensorDescription(
        key=ATTR_SUPPLIES_USAGE,
        translation_key="supplies_usage",
        native_unit_of_measurement="mm",
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
        key=ATTR_SLICER_VERSION, translation_key="slicer_version"
    ),
    AnycubicSensorDescription(key=ATTR_APP_VERSION, translation_key="app_version"),
    AnycubicSensorDescription(
        key=ATTR_PRINTER_TYPE,
        translation_key="printer_type",
        icon=_ICON_PRINTER_3D,
    ),
    AnycubicSensorDescription(key=ATTR_BED_LEVELING, translation_key="bed_leveling"),
    AnycubicSensorDescription(
        key=ATTR_FLOW_CALIBRATION, translation_key="flow_calibration"
    ),
    AnycubicSensorDescription(
        key=ATTR_FOREIGN_OBJECT_DETECTION,
        translation_key="foreign_object_detection",
    ),
    AnycubicSensorDescription(
        key=ATTR_SPAGHETTI_DETECTION, translation_key="spaghetti_detection"
    ),
    AnycubicSensorDescription(key=ATTR_TIME_LAPSE, translation_key="time_lapse"),
    AnycubicSensorDescription(
        key=ATTR_PRINT_FILAMENTS, translation_key="print_filaments"
    ),
    AnycubicSensorDescription(
        key=ATTR_SLICE_FILAMENTS, translation_key="slice_filaments"
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINT_FILAMENTS_WEIGHT,
        translation_key="print_filaments_weight",
        native_unit_of_measurement="g",
    ),
    AnycubicSensorDescription(
        key=ATTR_STORAGE_TOTAL,
        translation_key="storage_total",
        native_unit_of_measurement="MB",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AnycubicSensorDescription(
        key=ATTR_STORAGE_USED,
        translation_key="storage_used",
        native_unit_of_measurement="MB",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINT_PARAMS,
        translation_key="print_params",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINT_SPEED,
        translation_key="print_speed",
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINT_SPEED_MODE,
        translation_key="print_speed_mode",
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINT_STATUS,
        translation_key="print_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINTER_EVENT_CODE,
        translation_key="printer_event_code",
        icon="mdi:alert-circle-outline",
    ),
    AnycubicSensorDescription(
        key=ATTR_PRINTER_EVENT_ERROR,
        translation_key="printer_event_error",
        icon=_ICON_NOZZLE_ALERT,
    ),
    AnycubicSensorDescription(
        key=ATTR_PROJECT_PAUSE,
        translation_key="project_pause",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_PROJECT_TYPE,
        translation_key="project_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_TASK_SETTINGS,
        translation_key="task_settings",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_CAMERA_TIMELAPSE,
        translation_key="camera_timelapse",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_Z_COMPENSATION,
        translation_key="z_compensation",
        native_unit_of_measurement="mm",
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
        icon=_ICON_NOZZLE_HEAT,
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
        icon=_ICON_NOZZLE_HEAT_OUTLINE,
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
        key=ATTR_USB_PATH,
        translation_key="usb_path",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_TIMELAPSE_PATH,
        translation_key="timelapse_path",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_PERIPHERAL_CODE,
        translation_key="peripheral_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX, translation_key="multi_color_box"
    ),
    AnycubicSensorDescription(key=ATTR_VIDEO_STATE, translation_key="video_state"),
    AnycubicSensorDescription(
        key=ATTR_HEAD_TOOLS_MODEL,
        translation_key="head_tools_model",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_ID,
        translation_key="multi_color_box_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_MODEL_ID,
        translation_key="multi_color_box_model_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
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
        key=ATTR_MULTI_COLOR_BOX_AUTO_FEED,
        translation_key="multi_color_box_auto_feed",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_DRYING_STATUS,
        translation_key="multi_color_box_drying_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_DRYING_DURATION,
        translation_key="multi_color_box_drying_duration",
        native_unit_of_measurement="s",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_DRYING_REMAINING_TIME,
        translation_key="multi_color_box_drying_remaining_time",
        native_unit_of_measurement="s",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_DRYING_TARGET_TEMP,
        translation_key="multi_color_box_drying_target_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_FEED_STATUS,
        translation_key="multi_color_box_feed_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_FEED_CODE,
        translation_key="multi_color_box_feed_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_FEED_SLOT,
        translation_key="multi_color_box_feed_slot",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_MULTI_COLOR_BOX_FEED_TYPE,
        translation_key="multi_color_box_feed_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    *(
        description
        for slot in range(1, 5)
        for description in (
            AnycubicSensorDescription(
                key=ATTR_SLOT_TYPE[slot - 1],
                translation_key=f"slot_{slot}_type",
                icon=_ICON_NOZZLE_OUTLINE,
            ),
            AnycubicSensorDescription(
                key=ATTR_SLOT_STATUS[slot - 1],
                translation_key=f"slot_{slot}_status",
                icon=_ICON_NOZZLE_OUTLINE,
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
                icon=_ICON_NOZZLE_OUTLINE,
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
        key=ATTR_SOURCE_MODELS,
        translation_key="source_models",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_SOURCE_MODEL_COUNT,
        translation_key="source_model_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_SOURCE_MODELS_FROM,
        translation_key="source_models_from",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_SOURCE_PLATE_INDEX,
        translation_key="source_plate_index",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    AnycubicSensorDescription(
        key=ATTR_SOURCE_SLICE_PROCESS,
        translation_key="source_slice_process",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    *(
        AnycubicSensorDescription(
            key=key,
            translation_key=translation_key,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
        )
        for key, translation_key in (
            (ATTR_AUTO_LEVELING_SUPPORT, "auto_leveling_support"),
            (ATTR_CAMERA_TIMELAPSE_SUPPORT, "camera_timelapse_support"),
            (ATTR_DELETE_BATCH_SUPPORT, "delete_batch_support"),
            (ATTR_DRYING_FIRST_SUPPORT, "drying_first_support"),
            (ATTR_FLOW_CALIBRATION_SUPPORT, "flow_calibration_support"),
            (
                ATTR_FOREIGN_OBJECT_DETECTION_SUPPORT,
                "foreign_object_detection_support",
            ),
            (ATTR_GCODE_3MF_SUPPORT, "gcode_3mf_support"),
            (
                ATTR_KEEP_PRINT_HEAD_TEMP_SUPPORT,
                "keep_print_head_temp_support",
            ),
            (ATTR_PRE_CANCEL_SUPPORT, "pre_cancel_support"),
            (ATTR_PREHEATING_SUPPORT, "preheating_support"),
            (ATTR_SHENGWANG_RDT_SUPPORT, "shengwang_rdt_support"),
            (ATTR_SHENGWANG_RTC_SUPPORT, "shengwang_rtc_support"),
            (
                ATTR_VIBRATION_COMPENSATION_SUPPORT,
                "vibration_compensation_support",
            ),
        )
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
        value = self.coordinator.data.get(self.entity_description.key)
        if self.entity_description.key == ATTR_PRINT_PARAMS and isinstance(value, dict):
            # Keep structured settings out of HA's length-limited state string.
            return "available"
        return value

    @property
    def icon(self) -> str | None:
        """Return a printer-specific icon when the current state can refine it."""
        key = self.entity_description.key
        value = self.coordinator.data.get(key)

        if key == ATTR_LAST_WILL:
            return (
                _ICON_PRINTER_3D_OFF
                if str(value).lower() == "offline"
                else self.entity_description.icon or super().icon
            )

        if key == ATTR_PRINT_STATE:
            state = str(value).lower()
            if state in {"failed", "error"}:
                return _ICON_NOZZLE_ALERT
            if state in {"cancelled", "canceled", "stopping", "stopped", "stoped"}:
                return _ICON_PRINTER_3D_OFF
            if state == "preheating":
                return _ICON_NOZZLE_HEAT
            return self.entity_description.icon or super().icon

        if key == ATTR_NOZZLE_TEMP:
            return (
                _ICON_NOZZLE_OFF
                if _is_cool(self.coordinator.data.get(ATTR_TARGET_NOZZLE_TEMP))
                and _is_cool(value, threshold=40)
                else self.entity_description.icon or super().icon
            )

        if key == ATTR_TARGET_NOZZLE_TEMP:
            return (
                _ICON_NOZZLE_OFF_OUTLINE
                if _is_cool(value)
                else self.entity_description.icon or super().icon
            )

        return self.entity_description.icon or super().icon

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return diagnostic MQTT payload attributes."""
        if not self.entity_description.diagnostic_payload:
            key = self.entity_description.key
            if key == ATTR_PRINT_PARAMS:
                params = self.coordinator.data.get(key)
                return dict(params) if isinstance(params, dict) else None
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


def _is_cool(value: Any, *, threshold: float = 0) -> bool:
    """Return true when a temperature value is effectively not heating."""
    if value is None:
        return True
    try:
        return float(value) <= threshold
    except (TypeError, ValueError):
        return False
