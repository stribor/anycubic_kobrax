"""Coordinator and MQTT client for Anycubic Kobra X."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import re
import ssl
import tempfile
from threading import Event
import time
from typing import Any
from uuid import uuid4

import paho.mqtt.client as mqtt

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
    ATTR_LAYER,
    ATTR_LAST_TOPIC,
    ATTR_LAST_WILL,
    ATTR_LIGHT_BRIGHTNESS,
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
    ATTR_STREAM_URL,
    ATTR_SUPPLIES_USAGE,
    ATTR_TARGET_BED_TEMP,
    ATTR_TARGET_NOZZLE_TEMP,
    ATTR_TASK_ID,
    ATTR_TOTAL_TIME,
    ATTR_TOTAL_LAYER,
    ATTR_USB_DISK,
    ATTR_VIDEO_STATE,
    ATTR_WIFI_SIGNAL,
    CONF_DEVICE_CERT,
    CONF_DEVICE_CN,
    CONF_DEVICE_KEY,
    CONF_DEVICE_NAME,
    CONF_DEVICE_USN,
    CONF_DEVICE_ZONE,
    CONF_MODEL_NAME,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_PRINTER_ID,
    CONF_STREAM_PATH,
    CONF_TYPE_ID,
    DEFAULT_HTTP_PORT,
    DEFAULT_MQTT_PORT,
    DOMAIN,
    EVENT_AXIS_ERROR,
    EVENT_PRINT_COMPLETED,
    EVENT_PRINT_FAILED,
    EVENT_PRINT_PAUSED,
    EVENT_PRINT_PREHEATING,
    EVENT_PRINT_PRINTING,
    EVENT_PRINT_STARTED,
    EVENT_PRINT_STOPPED,
    QUERY_SPECS,
    TOPIC_BASE,
)

_LOGGER = logging.getLogger(__name__)
_LIVE_URL_RE = re.compile(r"https?://[^\s\"']+/live/[A-Za-z0-9_-]+")
_LIVE_PATH_RE = re.compile(r"/live/[A-Za-z0-9_-]+")
_HOME_AXIS_MAP = {"xy": 4, "z": 3, "xyz": 5}


@dataclass(slots=True)
class AnycubicDevice:
    """Configuration needed to talk to the printer."""

    host: str
    type_id: int
    printer_id: str
    username: str
    password: str
    device_cert: str | None
    device_key: str | None
    name: str | None
    device_name: str | None
    model_name: str | None
    device_cn: str | None
    device_usn: str | None
    device_zone: str | None
    stream_path: str | None


class AnycubicKobraXCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Own the MQTT connection and parsed printer state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.device = AnycubicDevice(
            host=entry.data[CONF_HOST],
            type_id=int(entry.data[CONF_TYPE_ID]),
            printer_id=entry.data[CONF_PRINTER_ID],
            username=entry.options.get(
                CONF_MQTT_USERNAME, entry.data[CONF_MQTT_USERNAME]
            ),
            password=entry.options.get(
                CONF_MQTT_PASSWORD, entry.data[CONF_MQTT_PASSWORD]
            ),
            device_cert=entry.data.get(CONF_DEVICE_CERT),
            device_key=entry.data.get(CONF_DEVICE_KEY),
            name=entry.options.get(CONF_NAME, entry.data.get(CONF_NAME)),
            device_name=entry.data.get(CONF_DEVICE_NAME),
            model_name=entry.data.get(CONF_MODEL_NAME),
            device_cn=entry.data.get(CONF_DEVICE_CN),
            device_usn=entry.data.get(CONF_DEVICE_USN),
            device_zone=entry.data.get(CONF_DEVICE_ZONE),
            stream_path=entry.options.get(
                CONF_STREAM_PATH, entry.data.get(CONF_STREAM_PATH)
            ),
        )
        self._client: mqtt.Client | None = None
        self._connect_event = Event()
        self._connected = False
        self._raw_messages: dict[str, Any] = {}
        self._state: dict[str, Any] = self._initial_state()
        self._requested_file_details: set[str] = set()
        self._event_sequence = 0
        self._last_axis_event_msgid: str | None = None
        self._last_print_event_state: str | None = None
        self.latest_event: dict[str, Any] | None = None
        self.preview_image: bytes | None = None
        self.preview_image_content_type = "image/png"
        self.preview_image_updated: datetime | None = None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
            always_update=False,
        )

    @property
    def base_web_topic(self) -> str:
        """Return base topic for web commands."""
        return self.command_base_topic("web")

    def command_base_topic(self, source: str) -> str:
        """Return base topic for a command source such as web or slicer."""
        return (
            f"{TOPIC_BASE}/{source}/printer/{self.device.type_id}/"
            f"{self.device.printer_id}"
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return HA device info shared by all entities."""
        return {
            "identifiers": {(DOMAIN, self.device.printer_id)},
            "manufacturer": "Anycubic",
            "model": (
                self.device.model_name or f"Kobra X type {self.device.type_id}"
            ),
            "name": self.device.name
            or self.device.device_name
            or self.device.model_name
            or "Anycubic printer",
            "configuration_url": f"http://{self.device.host}:{DEFAULT_HTTP_PORT}",
        }

    def _initial_state(self) -> dict[str, Any]:
        """Return stable metadata discovered during setup."""
        state: dict[str, Any] = {
            ATTR_IP_ADDRESS: self.device.host,
            ATTR_MODEL_ID: self.device.type_id,
        }
        if self.device.name or self.device.device_name:
            state[ATTR_PRINTER_NAME] = self.device.name or self.device.device_name
        if self.device.model_name:
            state[ATTR_MODEL] = self.device.model_name
        if self.device.device_cn:
            state[ATTR_DEVICE_CN] = self.device.device_cn
        if self.device.device_usn:
            state[ATTR_DEVICE_USN] = self.device.device_usn
        if self.device.device_zone:
            state[ATTR_DEVICE_ZONE] = self.device.device_zone
        return state

    @property
    def connected(self) -> bool:
        """Return whether the MQTT client is connected to the printer."""
        return self._connected

    def ensure_connected(self) -> None:
        """Raise if the printer cannot currently accept commands."""
        if not self._connected:
            raise HomeAssistantError("Anycubic printer is offline")

    async def async_setup(self) -> None:
        """Connect to MQTT and perform an initial refresh if the printer is online."""
        try:
            await self.hass.async_add_executor_job(self._connect)
            await self.async_config_entry_first_refresh()
        except (
            ConnectionError,
            ConfigEntryNotReady,
            OSError,
            TimeoutError,
            UpdateFailed,
        ) as err:
            _LOGGER.info(
                "Anycubic printer is unavailable during setup; will retry: %s", err
            )
            self.async_set_updated_data(dict(self._state))

    async def async_shutdown(self) -> None:
        """Disconnect the MQTT client."""
        client = self._client
        if client is None:
            return
        await self.hass.async_add_executor_job(self._disconnect)

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll the printer over MQTT."""
        if not self._connected:
            try:
                await self.hass.async_add_executor_job(self._connect)
            except (ConnectionError, OSError, TimeoutError) as err:
                raise UpdateFailed(
                    f"Could not connect to Anycubic printer: {err}"
                ) from err
        for source, query_type, action in QUERY_SPECS:
            self.publish_query(source, query_type, action)
        return dict(self._state)

    def publish_query(self, source: str, query_type: str, action: str) -> None:
        """Publish a query command for a specific Anycubic topic type."""
        payload = self._payload(query_type, action)
        self._publish(f"{self.command_base_topic(source)}/{query_type}", payload)

    def control_light(self, brightness: int) -> None:
        """Set the printer light brightness as 0-100."""
        self.ensure_connected()
        brightness = max(0, min(100, brightness))
        payload = self._payload(
            "light",
            "control",
            {
                "type": 3,
                "status": 1 if brightness else 0,
                "brightness": brightness,
            },
        )
        self._publish(f"{self.base_web_topic}/light", payload)

    def set_temperature(
        self, command_type: int, bed_temperature: int, nozzle_temperature: int
    ) -> None:
        """Set printer target temperatures."""
        self.ensure_connected()
        bed_temperature = max(0, min(120, bed_temperature))
        nozzle_temperature = max(0, min(300, nozzle_temperature))
        self._publish(
            f"{self.base_web_topic}/tempature",
            self._payload(
                "tempature",
                "set",
                {
                    "type": command_type,
                    "target_hotbed_temp": bed_temperature,
                    "target_nozzle_temp": nozzle_temperature,
                },
            ),
        )

    def set_bed_temperature(self, temperature: int) -> None:
        """Set the hotbed target temperature."""
        target_nozzle_temp = _coerce_int(self._state.get(ATTR_TARGET_NOZZLE_TEMP)) or 0
        self.set_temperature(1, temperature, target_nozzle_temp)

    def set_nozzle_temperature(self, temperature: int) -> None:
        """Set the nozzle target temperature."""
        target_bed_temp = _coerce_int(self._state.get(ATTR_TARGET_BED_TEMP)) or 0
        self.set_temperature(0, target_bed_temp, temperature)

    def preheat_pla(self) -> None:
        """Preheat bed and nozzle for PLA."""
        self.set_temperature(2, 60, 200)

    def print_command(self, action: str) -> None:
        """Send a print lifecycle command."""
        self.ensure_connected()
        self._publish(
            f"{self.base_web_topic}/print",
            self._payload(
                "print",
                action,
                {"taskid": str(self._state.get(ATTR_TASK_ID) or "-1")},
            ),
        )

    def pause_print(self) -> None:
        """Pause the active print."""
        self.print_command("pause")

    def resume_print(self) -> None:
        """Resume the paused print."""
        self.print_command("resume")

    def stop_print(self) -> None:
        """Stop the active print."""
        self.print_command("stop")

    def set_fan_speed(self, speed: int) -> None:
        """Set model fan speed percentage."""
        self.ensure_connected()
        speed = max(0, min(100, speed))
        self._publish(
            f"{self.base_web_topic}/fan",
            self._payload("fan", "setSpeed", {"fan_speed_pct": speed}),
        )

    def request_file_details(self, filename: str, root: str = "local") -> None:
        """Request slicer/file metadata for a known local print file."""
        if not filename:
            return
        request_key = f"{root}:{filename}"
        if request_key in self._requested_file_details:
            return
        self._requested_file_details.add(request_key)
        self._publish(
            f"{self.base_web_topic}/file",
            self._payload(
                "file",
                "fileDetails",
                {"root": root, "filename": filename},
            ),
        )

    def start_video(self) -> None:
        """Ask the printer to start camera capture."""
        self.ensure_connected()
        self._state.pop(ATTR_STREAM_URL, None)
        self._publish(
            f"{self.base_web_topic}/video",
            self._payload("video", "startCapture"),
        )
        self.refresh_stream_url()

    def stop_video(self) -> None:
        """Ask the printer to stop camera capture."""
        self.ensure_connected()
        self._publish(
            f"{self.base_web_topic}/video",
            self._payload("video", "stopCapture"),
        )

    def refresh_stream_url(self) -> None:
        """Ask the printer for current metadata containing the live URL."""
        self.publish_query("web", "info", "query")

    def axis_command(self, action: str, data: Mapping[str, Any] | None = None) -> None:
        """Send an axis command to the printer."""
        self.ensure_connected()
        self._publish(
            f"{self.base_web_topic}/axis",
            self._payload("axis", action, data),
        )

    def move_axis(self, axis: int, move_type: int, distance: int | float) -> None:
        """Move or home one of the printer axis groups."""
        self.axis_command(
            "move",
            {"axis": axis, "move_type": move_type, "distance": distance},
        )

    def move_relative(self, x: float, y: float, z: float) -> None:
        """Move one or more axes relatively in millimeters."""
        for axis, distance in ((1, x), (2, y), (3, z)):
            if distance == 0:
                continue
            self.move_axis(
                axis,
                1 if distance > 0 else 0,
                _distance_payload(distance),
            )

    def home_axis_group(self, axis_group: str) -> None:
        """Home one of the supported axis groups."""
        self.move_axis(_HOME_AXIS_MAP[axis_group], 2, 0)

    def turn_off_axis_motors(self) -> None:
        """Turn off axis motors."""
        self.axis_command("turnOff")

    def stream_url(self, *, allow_configured: bool = True) -> str | None:
        """Return the best-known FLV stream URL."""
        if stream_url := self._state.get(ATTR_STREAM_URL):
            return str(stream_url)
        if allow_configured and self.device.stream_path:
            path = self.device.stream_path
            if path.startswith("http://") or path.startswith("https://"):
                return path
            if not path.startswith("/"):
                path = f"/{path}"
            return f"http://{self.device.host}:{DEFAULT_HTTP_PORT}{path}"
        return None

    def _connect(self) -> None:
        """Create and start a paho MQTT client."""
        if self._client is not None:
            self._disconnect()
        self._connected = False
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"ha-anycubic-kobrax-{uuid4()}",
            protocol=mqtt.MQTTv311,
        )
        client.username_pw_set(self.device.username, self.device.password)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        if self.device.device_cert and self.device.device_key:
            _load_client_cert_chain(
                context, self.device.device_cert, self.device.device_key
            )
        client.tls_set_context(context)
        client.tls_insecure_set(True)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        self._connect_event.clear()
        client.connect(self.device.host, DEFAULT_MQTT_PORT, keepalive=60)
        client.loop_start()
        self._client = client
        if not self._connect_event.wait(timeout=10):
            client.loop_stop()
            client.disconnect()
            self._client = None
            raise TimeoutError("Timed out connecting to Anycubic MQTT broker")
        if not self._connected:
            client.loop_stop()
            client.disconnect()
            self._client = None
            raise ConnectionError("Anycubic MQTT broker rejected the connection")

    def _disconnect(self) -> None:
        """Stop and disconnect the paho MQTT client."""
        if self._client is None:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._client = None
        self._connected = False

    def _publish(self, topic: str, payload: Mapping[str, Any]) -> None:
        """Publish JSON to MQTT."""
        if self._client is None:
            _LOGGER.debug("Skipping publish to %s because MQTT is not connected", topic)
            return
        self._client.publish(topic, json.dumps(payload), qos=0, retain=False)

    def _payload(
        self, message_type: str, action: str, data: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build an Anycubic MQTT command payload."""
        return {
            "type": message_type,
            "action": action,
            "timestamp": int(time.time() * 1000),
            "msgid": str(uuid4()),
            "data": data,
        }

    def _on_connect(
        self,
        client: mqtt.Client,
        _userdata: Any,
        _flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        """Subscribe when MQTT connects."""
        if reason_code.is_failure:
            _LOGGER.error("Failed to connect to Anycubic MQTT broker: %s", reason_code)
            self._connect_event.set()
            return
        self._connected = True
        self._connect_event.set()
        type_id = self.device.type_id
        printer_id = self.device.printer_id
        topics = (
            f"{TOPIC_BASE}/printer/+/{type_id}/{printer_id}/#",
            f"{TOPIC_BASE}/printer/public/{type_id}/{printer_id}/#",
            f"{TOPIC_BASE}/printer/+/+/{printer_id}/#",
            f"{TOPIC_BASE}/slicer/printer/{type_id}/{printer_id}/#",
            f"{TOPIC_BASE}/web/printer/{type_id}/{printer_id}/#",
        )
        for topic in topics:
            client.subscribe(topic)
            _LOGGER.debug("Subscribed to %s", topic)

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        """Record MQTT disconnects."""
        self._connected = False
        if reason_code.is_failure:
            _LOGGER.warning("Disconnected from Anycubic MQTT broker: %s", reason_code)

    def _on_message(
        self, _client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        """Handle an incoming MQTT message from the paho thread."""
        topic = message.topic
        try:
            text = message.payload.decode("utf-8", errors="replace")
            payload: Any = json.loads(text)
        except json.JSONDecodeError:
            _LOGGER.debug("Ignoring non-JSON payload on %s", topic)
            return

        self.hass.loop.call_soon_threadsafe(
            self._async_handle_message, topic, payload, text
        )

    @callback
    def _async_handle_message(self, topic: str, payload: Any, text: str) -> None:
        """Parse a message inside the Home Assistant event loop."""
        self._raw_messages[topic] = payload
        self._state[ATTR_LAST_TOPIC] = topic
        self._state["last_payload"] = _redact_large_payload(payload)

        if isinstance(payload, dict):
            self._merge_payload(topic, payload)
        if stream_url := self._extract_stream_url(text, payload):
            self._state[ATTR_STREAM_URL] = stream_url

        self.async_set_updated_data(dict(self._state))

    @callback
    def _merge_payload(self, topic: str, payload: dict[str, Any]) -> None:
        """Merge known Anycubic payload fields into normalized state."""
        candidates = payload.get("data")
        if isinstance(candidates, dict):
            flat = _flatten(candidates)
        else:
            flat = _flatten(payload)
        all_flat = _flatten(payload)

        message_type = str(payload.get("type", "")).lower()
        topic_tail = topic.rsplit("/", maxsplit=1)[-1].lower()
        if message_type == "lastwill" or topic_tail == "lastwill":
            self._state[ATTR_LAST_WILL] = _coerce_last_will(flat or all_flat)
        if message_type == "multicolorbox" or topic_tail == "multicolorbox":
            self._merge_multi_color_box(payload)
        if message_type == "video" or topic_tail == "video":
            self._state[ATTR_VIDEO_STATE] = payload.get("state") or payload.get("action")
        if message_type == "axis" or topic_tail == "axis":
            self._state[ATTR_AXIS_STATE] = payload.get("state") or payload.get("action")
            if "code" in payload:
                self._state[ATTR_AXIS_CODE] = payload["code"]
            if "msg" in payload:
                self._state[ATTR_AXIS_MESSAGE] = payload["msg"]
            self._record_axis_event(payload)
        if message_type in {"print", "buried"} or topic_tail in {"print", "buried"}:
            self._merge_print_payload(payload)
        if message_type == "file" or topic_tail == "file":
            self._merge_file_payload(payload)

        field_map = {
            ATTR_PRINT_STATE: (
                "printState",
                "print_state",
                "printStatus",
                "taskStatus",
                "jobState",
                "workState",
            ),
            ATTR_PRINTER_NAME: ("printerName", "printer_name", "deviceName"),
            ATTR_MODEL: ("model", "machineModel", "modelName"),
            ATTR_MODEL_ID: ("modelId", "modeId", "typeId"),
            ATTR_DEVICE_CN: ("cn",),
            ATTR_DEVICE_USN: ("usn",),
            ATTR_DEVICE_ZONE: ("zone",),
            ATTR_FIRMWARE_VERSION: ("version", "firmwareVersion", "firmware_version"),
            ATTR_IP_ADDRESS: ("ip", "ipAddress", "ip_address"),
            ATTR_PROGRESS: (
                "progress",
                "printProgress",
                "taskProgress",
                "taskPercent",
                "percent",
                "completion",
            ),
            ATTR_FILENAME: (
                "filename",
                "fileName",
                "file_name",
                "taskName",
                "task_name",
                "printName",
                "name",
            ),
            ATTR_TASK_ID: ("taskid", "task_id"),
            ATTR_FILE_ROOT: ("root",),
            ATTR_FILAMENT_USED: ("filament_used",),
            ATTR_ESTIMATE_DURATION: ("estimate_duration",),
            ATTR_ESTIMATE_WEIGHT: ("estimate_weight",),
            ATTR_GCODE_SIZE: ("gcode_size",),
            ATTR_WIFI_SIGNAL: ("wifi_signal",),
            ATTR_SLICER: ("slicer",),
            ATTR_SUPPLIES_USAGE: ("supplies_usage",),
            ATTR_PRINT_SPEED: (
                "printSpeed",
                "speed",
                "feedrate",
                "feedRate",
            ),
            ATTR_PRINT_SPEED_MODE: ("print_speed_mode", "printSpeedMode"),
            ATTR_REMAINING_TIME: (
                "remain_time",
                "remainingTime",
                "remainTime",
                "timeRemaining",
                "leftTime",
            ),
            ATTR_TOTAL_TIME: (
                "print_time",
                "totalTime",
                "printTime",
                "elapsedTime",
                "usedTime",
                "duration",
            ),
            ATTR_NOZZLE_TEMP: (
                "curr_nozzle_temp",
                "nozzleTemp",
                "nozzleTemperature",
                "hotendTemp",
                "hotendTemperature",
                "currentNozzleTemp",
                "actualNozzleTemp",
            ),
            ATTR_BED_TEMP: (
                "curr_hotbed_temp",
                "curr_bed_temp",
                "bedTemp",
                "bedTemperature",
                "hotbedTemp",
                "hotbedTemperature",
                "currentBedTemp",
                "actualBedTemp",
            ),
            ATTR_TARGET_NOZZLE_TEMP: (
                "target_nozzle_temp",
                "targetNozzleTemp",
                "targetHotendTemp",
                "nozzleTargetTemp",
                "nozzleTargetTemperature",
                "hotendTargetTemp",
            ),
            ATTR_TARGET_BED_TEMP: (
                "target_hotbed_temp",
                "target_bed_temp",
                "targetBedTemp",
                "targetHotbedTemp",
                "bedTargetTemp",
                "bedTargetTemperature",
                "hotbedTargetTemp",
            ),
            ATTR_FAN_SPEED: (
                "fan_speed_pct",
                "fanSpeed",
                "fan",
                "modelFan",
                "modelFanSpeed",
                "fanPercent",
            ),
            ATTR_AUX_FAN_SPEED: (
                "aux_fan_speed_pct",
                "auxFanSpeed",
                "auxiliaryFanSpeed",
                "sideFanSpeed",
            ),
            ATTR_BOX_FAN_SPEED: (
                "box_fan_speed_pct",
                "boxFanSpeed",
                "chamberFanSpeed",
                "filterFanSpeed",
            ),
            ATTR_LIGHT_BRIGHTNESS: (
                "brightness",
                "lightBrightness",
                "light",
            ),
            ATTR_CAMERA_AVAILABLE: ("camera", "camera_available"),
            ATTR_USB_DISK: ("udisk", "usbDisk", "usb_disk"),
            ATTR_MULTI_COLOR_BOX: ("multiColorBox", "multi_color_box"),
            ATTR_VIDEO_STATE: ("videoState", "video_state"),
            ATTR_MATERIAL: ("material", "filament", "filamentType"),
            ATTR_LAYER: ("curr_layer", "layer", "currentLayer", "currLayer"),
            ATTR_TOTAL_LAYER: ("total_layers", "totalLayer", "totalLayers", "layerCount"),
        }
        for attr, keys in field_map.items():
            value = _first_present(flat, keys)
            if value is not None:
                self._state[attr] = value

        if message_type in {"print", "buried"} or topic_tail in {"print", "buried"}:
            print_state = _first_present(flat, ("state", "action"))
            if print_state is not None:
                self._state[ATTR_PRINT_STATE] = print_state

        light_status = _first_present(flat, ("lightStatus", "status"))
        light_brightness = _first_present(flat, ("brightness", "lightBrightness", "light"))
        if light_status is not None and topic_tail == "light":
            if light_brightness is None:
                light_state_int = _coerce_int(light_status)
                if light_state_int is not None:
                    self._state[ATTR_LIGHT_BRIGHTNESS] = 100 if light_state_int else 0

        if message_type in {"print", "buried"} or topic_tail in {"print", "buried"}:
            data = payload.get("data")
            if isinstance(data, dict):
                self._convert_print_minutes_to_seconds(data)
        if message_type == "info" or topic_tail == "info":
            self._merge_info_payload(payload)

        self._normalize_numeric_fields()

    def _normalize_numeric_fields(self) -> None:
        """Convert common numeric state fields to numbers where possible."""
        int_fields = (
            ATTR_PROGRESS,
            ATTR_AXIS_CODE,
            ATTR_ESTIMATE_DURATION,
            ATTR_GCODE_SIZE,
            ATTR_WIFI_SIGNAL,
            ATTR_PRINT_SPEED,
            ATTR_PRINT_SPEED_MODE,
            ATTR_REMAINING_TIME,
            ATTR_TOTAL_TIME,
            ATTR_SUPPLIES_USAGE,
            ATTR_FAN_SPEED,
            ATTR_AUX_FAN_SPEED,
            ATTR_BOX_FAN_SPEED,
            ATTR_LIGHT_BRIGHTNESS,
            ATTR_CAMERA_AVAILABLE,
            ATTR_USB_DISK,
            ATTR_MULTI_COLOR_BOX,
            ATTR_MULTI_COLOR_BOX_STATUS,
            ATTR_MULTI_COLOR_BOX_HUMIDITY,
            ATTR_LOADED_SLOT,
            *ATTR_SLOT_STATUS,
            *ATTR_SLOT_PERCENT,
            *ATTR_SLOT_WEIGHT,
            ATTR_LAYER,
            ATTR_TOTAL_LAYER,
        )
        float_fields = (
            ATTR_NOZZLE_TEMP,
            ATTR_BED_TEMP,
            ATTR_TARGET_NOZZLE_TEMP,
            ATTR_TARGET_BED_TEMP,
            ATTR_MULTI_COLOR_BOX_TEMP,
            ATTR_ESTIMATE_WEIGHT,
            ATTR_FILAMENT_USED,
        )
        for attr in int_fields:
            value = _coerce_int(self._state.get(attr))
            if value is not None:
                self._state[attr] = value
        for attr in float_fields:
            value = _coerce_float(self._state.get(attr))
            if value is not None:
                self._state[attr] = value

    def _merge_multi_color_box(self, payload: dict[str, Any]) -> None:
        """Merge multi-color box data from its nested payload shape."""
        data = payload.get("data")
        if not isinstance(data, dict):
            return
        boxes = data.get("multi_color_box")
        if not isinstance(boxes, list) or not boxes:
            return
        box = boxes[0]
        if not isinstance(box, dict):
            return

        mapping = {
            ATTR_MULTI_COLOR_BOX_STATUS: box.get("status"),
            ATTR_MULTI_COLOR_BOX_TEMP: box.get("temp"),
            ATTR_MULTI_COLOR_BOX_HUMIDITY: box.get("humidity"),
            ATTR_LOADED_SLOT: box.get("loaded_slot"),
        }
        for key, value in mapping.items():
            if value is not None:
                self._state[key] = value

        slots = box.get("slots")
        if isinstance(slots, list):
            materials = sorted(
                {
                    str(slot["type"])
                    for slot in slots
                    if isinstance(slot, dict) and slot.get("type")
                }
            )
            if materials:
                self._state[ATTR_MATERIAL] = ", ".join(materials)

            for index, slot in enumerate(slots[: len(ATTR_SLOT_TYPE)]):
                if not isinstance(slot, dict):
                    continue
                self._state[ATTR_SLOT_TYPE[index]] = slot.get("type")
                self._state[ATTR_SLOT_STATUS[index]] = slot.get("status")
                self._state[ATTR_SLOT_PERCENT[index]] = slot.get(
                    "consumables_percent"
                )
                self._state[ATTR_SLOT_WEIGHT[index]] = slot.get("weight")
                self._state[ATTR_SLOT_SKU[index]] = slot.get("sku")
                color = slot.get("color")
                if isinstance(color, list) and len(color) >= 3:
                    self._state[ATTR_SLOT_COLOR[index]] = (
                        f"#{int(color[0]):02x}{int(color[1]):02x}{int(color[2]):02x}"
                    )
                    self._state[ATTR_SLOT_COLOR_RGB[index]] = [
                        int(color[0]),
                        int(color[1]),
                        int(color[2]),
                    ]
                color_group = slot.get("color_group")
                if (
                    isinstance(color_group, list)
                    and color_group
                    and isinstance(color_group[0], list)
                    and len(color_group[0]) >= 4
                ):
                    self._state[ATTR_SLOT_COLOR_ALPHA[index]] = int(color_group[0][3])

    def _merge_file_payload(self, payload: dict[str, Any]) -> None:
        """Merge file metadata without keeping embedded preview images."""
        data = payload.get("data")
        if not isinstance(data, dict):
            return

        filename = data.get("filename")
        if filename:
            self._state[ATTR_FILENAME] = filename
        root = data.get("root")
        if root:
            self._state[ATTR_FILE_ROOT] = root

        details = data.get("file_details")
        if not isinstance(details, dict):
            return
        self._merge_preview_image(details)
        paint_infos = details.get("paint_infos")
        if isinstance(paint_infos, list) and paint_infos:
            paint_info = paint_infos[0]
            if isinstance(paint_info, dict):
                material = paint_info.get("material_type")
                if material:
                    self._state[ATTR_MATERIAL] = material
                if paint_info.get("filament_used") is not None:
                    self._state[ATTR_FILAMENT_USED] = paint_info["filament_used"]
                    if self._state.get(ATTR_ESTIMATE_WEIGHT) is None:
                        self._state[ATTR_ESTIMATE_WEIGHT] = paint_info["filament_used"]

    def _merge_preview_image(self, details: dict[str, Any]) -> None:
        """Keep the newest file preview in memory without storing it in state."""
        encoded = details.get("png_image") or details.get("thumbnail")
        if not isinstance(encoded, str) or not encoded:
            return

        try:
            image = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            _LOGGER.debug("Ignoring invalid Anycubic file preview image")
            return

        if image == self.preview_image:
            return

        self.preview_image = image
        self.preview_image_content_type = "image/png"
        self.preview_image_updated = datetime.now(timezone.utc)

    def _merge_print_payload(self, payload: dict[str, Any]) -> None:
        """Merge print lifecycle and buried metadata."""
        state = payload.get("state")
        if state:
            self._state[ATTR_PRINT_STATE] = state

        data = payload.get("data")
        if not isinstance(data, dict):
            return

        mappings = {
            ATTR_FILENAME: ("filename", "task_name"),
            ATTR_TASK_ID: ("taskid", "task_id"),
            ATTR_PROGRESS: ("progress",),
            ATTR_LAYER: ("curr_layer",),
            ATTR_TOTAL_LAYER: ("total_layers",),
            ATTR_TOTAL_TIME: ("print_time",),
            ATTR_REMAINING_TIME: ("remain_time", "estimate_duration"),
            ATTR_SUPPLIES_USAGE: ("supplies_usage",),
            ATTR_ESTIMATE_DURATION: ("estimate_duration",),
            ATTR_ESTIMATE_WEIGHT: ("estimate_weight",),
            ATTR_GCODE_SIZE: ("gcode_size",),
            ATTR_WIFI_SIGNAL: ("wifi_signal",),
            ATTR_MATERIAL: ("print_filaments", "slice_filaments"),
            ATTR_SLICER: ("slicer",),
        }
        for attr, keys in mappings.items():
            value = _first_present(data, keys)
            if value is not None:
                self._state[attr] = value

        source_info = data.get("source_info")
        if isinstance(source_info, dict):
            version = source_info.get("software_version")
            if version:
                self._state[ATTR_SLICER] = version

        self._convert_print_minutes_to_seconds(data)
        self._derive_print_estimates()
        self._record_print_event(payload, data)
        if filename := self._state.get(ATTR_FILENAME):
            self.request_file_details(str(filename), str(self._state.get(ATTR_FILE_ROOT, "local")))

    def _merge_info_payload(self, payload: dict[str, Any]) -> None:
        """Merge nested project data from info reports."""
        data = payload.get("data")
        if not isinstance(data, dict):
            return

        project = data.get("project")
        if not isinstance(project, dict):
            return

        mappings = {
            ATTR_PRINT_STATE: ("state",),
            ATTR_FILENAME: ("filename",),
            ATTR_TASK_ID: ("task_id", "taskid"),
            ATTR_PROGRESS: ("progress",),
            ATTR_LAYER: ("curr_layer",),
            ATTR_TOTAL_LAYER: ("total_layers",),
            ATTR_TOTAL_TIME: ("print_time",),
            ATTR_REMAINING_TIME: ("remain_time",),
            ATTR_SUPPLIES_USAGE: ("supplies_usage",),
            ATTR_PRINT_SPEED_MODE: ("print_speed_mode",),
        }
        for attr, keys in mappings.items():
            value = _first_present(project, keys)
            if value is not None:
                self._state[attr] = value

        self._convert_print_minutes_to_seconds(project)
        self._derive_print_estimates()
        self._record_print_event(payload, project)
        if filename := self._state.get(ATTR_FILENAME):
            self.request_file_details(str(filename), str(self._state.get(ATTR_FILE_ROOT, "local")))

    def _record_axis_event(self, payload: dict[str, Any]) -> None:
        """Record actionable axis errors as Home Assistant events."""
        code = _coerce_int(payload.get("code"))
        state = str(payload.get("state", "")).lower()
        if state != "failed" and (code is None or code in {0, 200}):
            return

        msgid = str(payload.get("msgid") or "")
        if msgid and msgid == self._last_axis_event_msgid:
            return
        self._last_axis_event_msgid = msgid
        self._record_event(
            EVENT_AXIS_ERROR,
            {
                "code": code,
                "message": payload.get("msg"),
                "state": payload.get("state"),
                "action": payload.get("action"),
                "msgid": payload.get("msgid"),
            },
        )

    def _record_print_event(
        self, payload: dict[str, Any], data: dict[str, Any]
    ) -> None:
        """Record print lifecycle changes as Home Assistant events."""
        state = str(data.get("state") or payload.get("state") or "").lower()
        action = str(payload.get("action") or "").lower()
        event_type: str | None = None
        if state in {"checking", "auto_leveling"} or action == "printstart":
            event_type = EVENT_PRINT_STARTED
        elif state == "preheating":
            event_type = EVENT_PRINT_PREHEATING
        elif state in {"printing", "updated", "resuming", "resumed"}:
            event_type = EVENT_PRINT_PRINTING
        elif state in {"finished", "finish", "completed", "done"}:
            event_type = EVENT_PRINT_COMPLETED
        elif state in {"pausing", "paused"}:
            event_type = EVENT_PRINT_PAUSED
        elif state in {"cancelled", "canceled", "stopping", "stopped", "stoped"}:
            event_type = EVENT_PRINT_STOPPED
        elif state in {"failed", "error"} or (
            (code := _coerce_int(payload.get("code"))) is not None
            and code not in {0, 200}
        ):
            event_type = EVENT_PRINT_FAILED

        if event_type is None:
            return
        dedupe_state = (
            f"{event_type}:{data.get('taskid') or data.get('task_id')}:"
            f"{data.get('filename') or data.get('task_name')}"
        )
        if dedupe_state == self._last_print_event_state:
            return
        self._last_print_event_state = dedupe_state
        self._record_event(
            event_type,
            {
                "state": payload.get("state") or data.get("state"),
                "action": payload.get("action"),
                "code": payload.get("code"),
                "message": payload.get("msg"),
                "filename": data.get("filename") or data.get("task_name"),
                "progress": data.get("progress"),
                "layer": data.get("curr_layer"),
                "total_layers": data.get("total_layers"),
                "msgid": payload.get("msgid"),
            },
        )

    def _record_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Store the latest event for the event entity to fire."""
        event_data = {key: value for key, value in data.items() if value is not None}
        self._event_sequence += 1
        self.latest_event = {
            "sequence": self._event_sequence,
            "event_type": event_type,
            "data": event_data,
        }
        self.hass.bus.async_fire(
            f"{DOMAIN}_printer_event",
            {
                "entry_id": self.entry.entry_id,
                "printer_id": self.device.printer_id,
                "type": event_type,
                **event_data,
            },
        )

    def _convert_print_minutes_to_seconds(self, data: dict[str, Any]) -> None:
        """Convert Anycubic print_time/remain_time minutes to HA seconds."""
        if "print_time" in data:
            total_time = _coerce_int(data.get("print_time"))
            if total_time is not None:
                self._state[ATTR_TOTAL_TIME] = total_time * 60
        if "remain_time" in data:
            remaining_time = _coerce_int(data.get("remain_time"))
            if remaining_time is not None:
                self._state[ATTR_REMAINING_TIME] = remaining_time * 60

    def _derive_print_estimates(self) -> None:
        """Derive stable print estimates from live print progress reports."""
        total_time = _coerce_int(self._state.get(ATTR_TOTAL_TIME))
        remaining_time = _coerce_int(self._state.get(ATTR_REMAINING_TIME))
        if total_time is not None and remaining_time is not None:
            self._state[ATTR_ESTIMATE_DURATION] = total_time + remaining_time

        if self._state.get(ATTR_ESTIMATE_WEIGHT) is None:
            filament_used = _coerce_float(self._state.get(ATTR_FILAMENT_USED))
            if filament_used is not None:
                self._state[ATTR_ESTIMATE_WEIGHT] = filament_used

    def _extract_stream_url(self, text: str, payload: Any) -> str | None:
        """Find a /live/ camera URL or path in MQTT data."""
        if match := _LIVE_URL_RE.search(text):
            return match.group(0)
        if match := _LIVE_PATH_RE.search(text):
            return f"http://{self.device.host}:{DEFAULT_HTTP_PORT}{match.group(0)}"

        flat = _flatten(payload)
        for key in (
            "url",
            "streamUrl",
            "videoUrl",
            "flvUrl",
            "rtspUrl",
            "path",
            "token",
        ):
            value = flat.get(key)
            if not isinstance(value, str):
                continue
            if value.startswith("http://") or value.startswith("https://"):
                return value
            if value.startswith("/live/"):
                return f"http://{self.device.host}:{DEFAULT_HTTP_PORT}{value}"
            if key == "token" and value:
                return f"http://{self.device.host}:{DEFAULT_HTTP_PORT}/live/{value}"
        return None


def _load_client_cert_chain(context: ssl.SSLContext, cert: str, key: str) -> None:
    """Load an in-memory client certificate into an SSL context."""
    cert_path: str | None = None
    key_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(_ensure_trailing_newline(cert))
            cert_path = file.name
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(_ensure_trailing_newline(key))
            key_path = file.name
        context.load_cert_chain(cert_path, key_path)
    finally:
        for path in (cert_path, key_path):
            if path is None:
                continue
            try:
                os.unlink(path)
            except OSError:
                pass


def _ensure_trailing_newline(value: str) -> str:
    """Return PEM text with the trailing newline OpenSSL expects."""
    if value.endswith("\n"):
        return value
    return f"{value}\n"


def _flatten(value: Any) -> dict[str, Any]:
    """Flatten nested dictionaries and lists by leaf key."""
    flattened: dict[str, Any] = {}

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(child, (dict, list)):
                    flattened[str(key)] = child
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return flattened


def _first_present(flat: Mapping[str, Any], keys: tuple[str, ...]) -> Any | None:
    """Return the first available field, preserving falsy numeric values."""
    for key in keys:
        if key in flat:
            return flat[key]
    return None


def _redact_large_payload(value: Any) -> Any:
    """Drop large embedded image fields from diagnostic payloads."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            if key in {"png_image", "svg_image", "thumbnail"}:
                redacted[key] = "<redacted>"
            else:
                redacted[key] = _redact_large_payload(child)
        return redacted
    if isinstance(value, list):
        return [_redact_large_payload(child) for child in value]
    return value


def _coerce_last_will(flat: Mapping[str, Any]) -> str:
    """Return a readable lastWill/availability value."""
    for key in ("online", "connected", "status", "state", "lastWill"):
        if key not in flat:
            continue
        value = flat[key]
        if isinstance(value, bool):
            return "online" if value else "offline"
        if isinstance(value, (int, float)):
            return "online" if value else "offline"
        return str(value)
    return "received"


def _coerce_int(value: Any) -> int | None:
    """Return an int for numeric-looking values."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    """Return a float for numeric-looking values."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _distance_payload(value: float) -> int | float:
    """Return a compact numeric distance for the Anycubic payload."""
    distance = abs(value)
    if distance.is_integer():
        return int(distance)
    return distance
