"""Constants for the Anycubic Kobra X integration."""

from __future__ import annotations

DOMAIN = "anycubic_kobrax"

DATA_SERVICE_REGISTERED = "services_registered"

FRONTEND_FOLDER = "frontend_panel"
CARD_FILENAME = "anycubic-kobrax-card.js"
CARD_VERSION = "0.1.18"

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
ATTR_FILE_ROOT = "file_root"
ATTR_FILAMENT_USED = "filament_used"
ATTR_ESTIMATE_DURATION = "estimate_duration"
ATTR_ESTIMATE_WEIGHT = "estimate_weight"
ATTR_GCODE_SIZE = "gcode_size"
ATTR_WIFI_SIGNAL = "wifi_signal"
ATTR_SLICER = "slicer"
ATTR_SUPPLIES_USAGE = "supplies_usage"
ATTR_PRINT_SPEED = "print_speed"
ATTR_PRINT_SPEED_MODE = "print_speed_mode"
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
ATTR_MULTI_COLOR_BOX = "multi_color_box"
ATTR_MULTI_COLOR_BOX_STATUS = "multi_color_box_status"
ATTR_MULTI_COLOR_BOX_TEMP = "multi_color_box_temperature"
ATTR_MULTI_COLOR_BOX_HUMIDITY = "multi_color_box_humidity"
ATTR_LOADED_SLOT = "loaded_slot"

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
