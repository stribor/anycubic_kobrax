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

QUERY_TYPES = ("status", "info", "tempature", "fan", "peripherie", "light")

TOPIC_BASE = "anycubic/anycubicCloud/v1"

ATTR_PRINT_STATE = "print_state"
ATTR_PROGRESS = "progress"
ATTR_FILENAME = "filename"
ATTR_NOZZLE_TEMP = "nozzle_temperature"
ATTR_BED_TEMP = "bed_temperature"
ATTR_TARGET_NOZZLE_TEMP = "target_nozzle_temperature"
ATTR_TARGET_BED_TEMP = "target_bed_temperature"
ATTR_LIGHT_BRIGHTNESS = "light_brightness"
ATTR_STREAM_URL = "stream_url"
