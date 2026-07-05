"""Constants for the Anycubic Kobra X integration."""

from __future__ import annotations

DOMAIN = "anycubic_kobrax"

DATA_SERVICE_REGISTERED = "services_registered"

FRONTEND_FOLDER = "frontend_panel"
CARD_FILENAME = "anycubic-kobrax-card.js"
CARD_VERSION = "0.1.35"

CONF_HOST = "host"
CONF_TYPE_ID = "type_id"
CONF_PRINTER_ID = "printer_id"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"
CONF_DEVICE_CERT = "device_cert"
CONF_DEVICE_KEY = "device_key"
CONF_DEVICE_UUID = "device_uuid"
CONF_DEVICE_NAME = "device_name"
CONF_DEVICE_CN = "device_cn"
CONF_DEVICE_USN = "device_usn"
CONF_DEVICE_ZONE = "device_zone"
CONF_MODEL_NAME = "model_name"
CONF_STREAM_PATH = "stream_path"
CONF_CONFIG_ENTRY_ID = "config_entry_id"
CONF_AXIS = "axis"
CONF_X = "x"
CONF_Y = "y"
CONF_Z = "z"

SERVICE_MOVE_AXIS = "move_axis"
SERVICE_HOME_AXIS = "home_axis"
SERVICE_MOTORS_OFF = "motors_off"

DEFAULT_MQTT_PORT = 9883
DEFAULT_HTTP_PORT = 18088
DEFAULT_TYPE_ID = 20030
DEFAULT_MQTT_USERNAME = ""
DEFAULT_MQTT_PASSWORD = ""

PLATFORMS = ["sensor", "light", "camera", "button", "number", "image", "event"]

EVENT_AXIS_ERROR = "axis_error"
EVENT_PRINT_STARTED = "print_started"
EVENT_PRINT_PREHEATING = "print_preheating"
EVENT_PRINT_PRINTING = "print_printing"
EVENT_PRINT_COMPLETED = "print_completed"
EVENT_PRINT_PAUSED = "print_paused"
EVENT_PRINT_STOPPED = "print_stopped"
EVENT_PRINT_FAILED = "print_failed"
EVENT_TYPES = [
    EVENT_AXIS_ERROR,
    EVENT_PRINT_STARTED,
    EVENT_PRINT_PREHEATING,
    EVENT_PRINT_PRINTING,
    EVENT_PRINT_COMPLETED,
    EVENT_PRINT_PAUSED,
    EVENT_PRINT_STOPPED,
    EVENT_PRINT_FAILED,
]

QUERY_SPECS = (
    ("web", "lastWill", "query"),
    ("web", "status", "query"),
    ("web", "info", "query"),
    ("web", "tempature", "query"),
    ("web", "fan", "query"),
    ("web", "peripherie", "query"),
    ("web", "light", "query"),
    ("web", "multiColorBox", "getInfo"),
    ("slicer", "info", "query"),
)

TOPIC_BASE = "anycubic/anycubicCloud/v1"

ATTR_LAST_WILL = "last_will"
ATTR_AXIS_STATE = "axis_state"
ATTR_AXIS_CODE = "axis_code"
ATTR_AXIS_MESSAGE = "axis_message"
ATTR_PRINT_STATE = "print_state"
ATTR_PRINTER_NAME = "printer_name"
ATTR_MODEL = "model"
ATTR_MODEL_ID = "model_id"
ATTR_DEVICE_CN = "device_cn"
ATTR_DEVICE_USN = "device_usn"
ATTR_DEVICE_ZONE = "device_zone"
ATTR_FIRMWARE_VERSION = "firmware_version"
ATTR_IP_ADDRESS = "ip_address"
ATTR_PROGRESS = "progress"
ATTR_FILENAME = "filename"
ATTR_TASK_ID = "task_id"
ATTR_LOCAL_TASK_ID = "local_task_id"
ATTR_FILE_ROOT = "file_root"
ATTR_FILE_UPLOAD_URL = "file_upload_url"
ATTR_FILAMENT_USED = "filament_used"
ATTR_ESTIMATE_DURATION = "estimate_duration"
ATTR_ESTIMATE_WEIGHT = "estimate_weight"
ATTR_GCODE_SIZE = "gcode_size"
ATTR_WIFI_SIGNAL = "wifi_signal"
ATTR_SLICER = "slicer"
ATTR_SLICER_VERSION = "slicer_version"
ATTR_APP_VERSION = "app_version"
ATTR_PRINTER_TYPE = "printer_type"
ATTR_BED_LEVELING = "bed_leveling"
ATTR_FLOW_CALIBRATION = "flow_calibration"
ATTR_FOREIGN_OBJECT_DETECTION = "foreign_object_detection"
ATTR_SPAGHETTI_DETECTION = "spaghetti_detection"
ATTR_TIME_LAPSE = "time_lapse"
ATTR_PRINT_FILAMENTS = "print_filaments"
ATTR_SLICE_FILAMENTS = "slice_filaments"
ATTR_PRINT_FILAMENTS_WEIGHT = "print_filaments_weight"
ATTR_STORAGE_TOTAL = "storage_total"
ATTR_STORAGE_USED = "storage_used"
ATTR_PRINT_PARAMS = "print_params"
ATTR_SUPPLIES_USAGE = "supplies_usage"
ATTR_PRINT_SPEED = "print_speed"
ATTR_PRINT_SPEED_MODE = "print_speed_mode"
ATTR_PRINT_STATUS = "print_status"
ATTR_PROJECT_PAUSE = "project_pause"
ATTR_PROJECT_TYPE = "project_type"
ATTR_TASK_SETTINGS = "task_settings"
ATTR_CAMERA_TIMELAPSE = "camera_timelapse"
ATTR_Z_COMPENSATION = "z_compensation"
ATTR_REMAINING_TIME = "remaining_time"
ATTR_TOTAL_TIME = "total_time"
ATTR_NOZZLE_TEMP = "nozzle_temperature"
ATTR_BED_TEMP = "bed_temperature"
ATTR_TARGET_NOZZLE_TEMP = "target_nozzle_temperature"
ATTR_TARGET_BED_TEMP = "target_bed_temperature"
ATTR_FAN_SPEED = "fan_speed"
ATTR_AUX_FAN_SPEED = "aux_fan_speed"
ATTR_BOX_FAN_SPEED = "box_fan_speed"
ATTR_LIGHT_BRIGHTNESS = "light_brightness"
ATTR_MATERIAL = "material"
ATTR_CAMERA_AVAILABLE = "camera_available"
ATTR_USB_DISK = "usb_disk"
ATTR_USB_PATH = "usb_path"
ATTR_TIMELAPSE_PATH = "timelapse_path"
ATTR_PERIPHERAL_CODE = "peripheral_code"
ATTR_MULTI_COLOR_BOX = "multi_color_box"
ATTR_HEAD_TOOLS_MODEL = "head_tools_model"
ATTR_MULTI_COLOR_BOX_ID = "multi_color_box_id"
ATTR_MULTI_COLOR_BOX_MODEL_ID = "multi_color_box_model_id"
ATTR_MULTI_COLOR_BOX_STATUS = "multi_color_box_status"
ATTR_MULTI_COLOR_BOX_TEMP = "multi_color_box_temperature"
ATTR_MULTI_COLOR_BOX_HUMIDITY = "multi_color_box_humidity"
ATTR_LOADED_SLOT = "loaded_slot"
ATTR_MULTI_COLOR_BOX_AUTO_FEED = "multi_color_box_auto_feed"
ATTR_MULTI_COLOR_BOX_DRYING_STATUS = "multi_color_box_drying_status"
ATTR_MULTI_COLOR_BOX_DRYING_DURATION = "multi_color_box_drying_duration"
ATTR_MULTI_COLOR_BOX_DRYING_REMAINING_TIME = "multi_color_box_drying_remaining_time"
ATTR_MULTI_COLOR_BOX_DRYING_TARGET_TEMP = "multi_color_box_drying_target_temperature"
ATTR_MULTI_COLOR_BOX_FEED_STATUS = "multi_color_box_feed_status"
ATTR_MULTI_COLOR_BOX_FEED_CODE = "multi_color_box_feed_code"
ATTR_MULTI_COLOR_BOX_FEED_SLOT = "multi_color_box_feed_slot"
ATTR_MULTI_COLOR_BOX_FEED_TYPE = "multi_color_box_feed_type"
ATTR_SOURCE_MODELS = "source_models"
ATTR_SOURCE_MODEL_COUNT = "source_model_count"
ATTR_SOURCE_MODELS_FROM = "source_models_from"
ATTR_SOURCE_PLATE_INDEX = "source_plate_index"
ATTR_SOURCE_SLICE_PROCESS = "source_slice_process"
ATTR_AUTO_LEVELING_SUPPORT = "auto_leveling_support"
ATTR_CAMERA_TIMELAPSE_SUPPORT = "camera_timelapse_support"
ATTR_DELETE_BATCH_SUPPORT = "delete_batch_support"
ATTR_DRYING_FIRST_SUPPORT = "drying_first_support"
ATTR_FLOW_CALIBRATION_SUPPORT = "flow_calibration_support"
ATTR_FOREIGN_OBJECT_DETECTION_SUPPORT = "foreign_object_detection_support"
ATTR_GCODE_3MF_SUPPORT = "gcode_3mf_support"
ATTR_KEEP_PRINT_HEAD_TEMP_SUPPORT = "keep_print_head_temp_support"
ATTR_PRE_CANCEL_SUPPORT = "pre_cancel_support"
ATTR_PREHEATING_SUPPORT = "preheating_support"
ATTR_SHENGWANG_RDT_SUPPORT = "shengwang_rdt_support"
ATTR_SHENGWANG_RTC_SUPPORT = "shengwang_rtc_support"
ATTR_VIBRATION_COMPENSATION_SUPPORT = "vibration_compensation_support"

MULTI_COLOR_SLOT_COUNT = 4
ATTR_SLOT_TYPE = tuple(f"slot_{slot}_type" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_SLOT_STATUS = tuple(f"slot_{slot}_status" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_SLOT_PERCENT = tuple(f"slot_{slot}_percent" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_SLOT_WEIGHT = tuple(f"slot_{slot}_weight" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_SLOT_SKU = tuple(f"slot_{slot}_sku" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_SLOT_COLOR = tuple(f"slot_{slot}_color" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_SLOT_COLOR_RGB = tuple(f"slot_{slot}_color_rgb" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_SLOT_COLOR_ALPHA = tuple(f"slot_{slot}_color_alpha" for slot in range(1, MULTI_COLOR_SLOT_COUNT + 1))
ATTR_LAYER = "layer"
ATTR_TOTAL_LAYER = "total_layer"
ATTR_STREAM_URL = "stream_url"
ATTR_VIDEO_STATE = "video_state"
ATTR_LAST_TOPIC = "last_topic"
