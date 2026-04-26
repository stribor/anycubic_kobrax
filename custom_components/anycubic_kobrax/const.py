"""Constants for the Anycubic Kobra X integration."""

from __future__ import annotations

DOMAIN = "anycubic_kobrax"

CONF_HOST = "host"
CONF_TYPE_ID = "type_id"
CONF_PRINTER_ID = "printer_id"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"
CONF_STREAM_PATH = "stream_path"

DEFAULT_MQTT_PORT = 9883
DEFAULT_HTTP_PORT = 18088
DEFAULT_TYPE_ID = 20030
DEFAULT_MQTT_USERNAME = ""
DEFAULT_MQTT_PASSWORD = ""

PLATFORMS = ["sensor", "light", "camera"]

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
ATTR_PRINT_STATE = "print_state"
ATTR_PROGRESS = "progress"
ATTR_FILENAME = "filename"
ATTR_PRINT_SPEED = "print_speed"
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
ATTR_LAYER = "layer"
ATTR_TOTAL_LAYER = "total_layer"
ATTR_STREAM_URL = "stream_url"
ATTR_LAST_TOPIC = "last_topic"
