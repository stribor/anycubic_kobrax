"""Coordinator and MQTT client for Anycubic Kobra X."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
import json
import logging
import re
import ssl
from threading import Event
import time
from typing import Any
from uuid import uuid4

import paho.mqtt.client as mqtt

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_BED_TEMP,
    ATTR_FILENAME,
    ATTR_LIGHT_BRIGHTNESS,
    ATTR_NOZZLE_TEMP,
    ATTR_PRINT_STATE,
    ATTR_PROGRESS,
    ATTR_STREAM_URL,
    ATTR_TARGET_BED_TEMP,
    ATTR_TARGET_NOZZLE_TEMP,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_USERNAME,
    CONF_PRINTER_ID,
    CONF_STREAM_PATH,
    CONF_TYPE_ID,
    DEFAULT_HTTP_PORT,
    DEFAULT_MQTT_PORT,
    DOMAIN,
    QUERY_TYPES,
    TOPIC_BASE,
)

_LOGGER = logging.getLogger(__name__)
_LIVE_URL_RE = re.compile(r"https?://[^\s\"']+/live/[A-Za-z0-9_-]+")
_LIVE_PATH_RE = re.compile(r"/live/[A-Za-z0-9_-]+")


@dataclass(slots=True)
class AnycubicDevice:
    """Configuration needed to talk to the printer."""

    host: str
    type_id: int
    printer_id: str
    username: str
    password: str
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
            stream_path=entry.options.get(
                CONF_STREAM_PATH, entry.data.get(CONF_STREAM_PATH)
            ),
        )
        self._client: mqtt.Client | None = None
        self._connect_event = Event()
        self._connected = False
        self._raw_messages: dict[str, Any] = {}
        self._state: dict[str, Any] = {}
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
        return (
            f"{TOPIC_BASE}/web/printer/{self.device.type_id}/"
            f"{self.device.printer_id}"
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return HA device info shared by all entities."""
        return {
            "identifiers": {(DOMAIN, self.device.printer_id)},
            "manufacturer": "Anycubic",
            "model": f"Kobra X type {self.device.type_id}",
            "name": "Anycubic Kobra X",
            "configuration_url": f"http://{self.device.host}:{DEFAULT_HTTP_PORT}",
        }

    async def async_setup(self) -> None:
        """Connect to MQTT and perform an initial refresh."""
        await self.hass.async_add_executor_job(self._connect)
        await self.async_config_entry_first_refresh()

    async def async_shutdown(self) -> None:
        """Disconnect the MQTT client."""
        client = self._client
        if client is None:
            return
        await self.hass.async_add_executor_job(self._disconnect)

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll the printer over MQTT."""
        if not self._connected:
            raise UpdateFailed("MQTT client is not connected")
        for query_type in QUERY_TYPES:
            self.publish_query(query_type)
        return dict(self._state)

    def publish_query(self, query_type: str) -> None:
        """Publish a query command for a specific Anycubic topic type."""
        payload = self._payload(query_type, "query")
        self._publish(f"{self.base_web_topic}/{query_type}", payload)

    def control_light(self, brightness: int) -> None:
        """Set the printer light brightness as 0-100."""
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

    def start_video(self) -> None:
        """Ask the printer to start camera capture."""
        self._publish(
            f"{self.base_web_topic}/video",
            self._payload("video", "startCapture"),
        )

    def stop_video(self) -> None:
        """Ask the printer to stop camera capture."""
        self._publish(
            f"{self.base_web_topic}/video",
            self._payload("video", "stopCapture"),
        )

    def stream_url(self) -> str | None:
        """Return the best-known FLV stream URL."""
        if stream_url := self._state.get(ATTR_STREAM_URL):
            return str(stream_url)
        if self.device.stream_path:
            path = self.device.stream_path
            if path.startswith("http://") or path.startswith("https://"):
                return path
            if not path.startswith("/"):
                path = f"/{path}"
            return f"http://{self.device.host}:{DEFAULT_HTTP_PORT}{path}"
        return None

    def _connect(self) -> None:
        """Create and start a paho MQTT client."""
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"ha-anycubic-kobrax-{uuid4()}",
            protocol=mqtt.MQTTv311,
        )
        client.username_pw_set(self.device.username, self.device.password)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
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
        self._state["last_topic"] = topic
        self._state["last_payload"] = payload

        if isinstance(payload, dict):
            self._merge_payload(payload)
        if stream_url := self._extract_stream_url(text, payload):
            self._state[ATTR_STREAM_URL] = stream_url

        self.async_set_updated_data(dict(self._state))

    @callback
    def _merge_payload(self, payload: dict[str, Any]) -> None:
        """Merge known Anycubic payload fields into normalized state."""
        candidates = payload.get("data")
        if isinstance(candidates, dict):
            flat = _flatten(candidates)
        else:
            flat = _flatten(payload)

        field_map = {
            ATTR_PRINT_STATE: ("printState", "print_state", "state", "status"),
            ATTR_PROGRESS: ("progress", "printProgress", "percent"),
            ATTR_FILENAME: ("filename", "fileName", "name"),
            ATTR_NOZZLE_TEMP: ("nozzleTemp", "nozzleTemperature", "hotendTemp"),
            ATTR_BED_TEMP: ("bedTemp", "bedTemperature", "hotbedTemp"),
            ATTR_TARGET_NOZZLE_TEMP: ("targetNozzleTemp", "targetHotendTemp"),
            ATTR_TARGET_BED_TEMP: ("targetBedTemp", "targetHotbedTemp"),
            ATTR_LIGHT_BRIGHTNESS: ("brightness", "lightBrightness"),
        }
        for attr, keys in field_map.items():
            value = _first_present(flat, keys)
            if value is not None:
                self._state[attr] = value

    def _extract_stream_url(self, text: str, payload: Any) -> str | None:
        """Find a /live/ camera URL or path in MQTT data."""
        if match := _LIVE_URL_RE.search(text):
            return match.group(0)
        if match := _LIVE_PATH_RE.search(text):
            return f"http://{self.device.host}:{DEFAULT_HTTP_PORT}{match.group(0)}"

        flat = _flatten(payload)
        for key in ("url", "streamUrl", "videoUrl", "flvUrl", "path", "token"):
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
