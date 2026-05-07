#!/usr/bin/env python3
"""Capture Anycubic LAN MQTT messages as newline-delimited JSON."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import ssl
import sys
import tempfile
import threading
import time
from typing import Any
from uuid import uuid4


DEFAULT_PORT = 9883
DEFAULT_TOPIC = "anycubic/anycubicCloud/v1/#"
SENSITIVE_KEYS = {
    "access_token",
    "client_key",
    "clientkey",
    "device_key",
    "key",
    "mqtt_password",
    "mqtt_username",
    "password",
    "printer_id",
    "refresh_token",
    "stream_path",
    "token",
    "username",
}
LARGE_KEYS = {"png_image", "thumbnail", "image", "preview"}
MAX_STRING_LENGTH = 500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Subscribe to the Anycubic printer MQTT broker and write captured "
            "messages as JSONL for decoder development."
        )
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path(".local/anycubic_kobrax.dev.yaml"),
        help="Local JSON or simple key: value config file.",
    )
    parser.add_argument("--host", help="Printer IP or hostname.")
    parser.add_argument("--port", type=int, help=f"MQTT port, default {DEFAULT_PORT}.")
    parser.add_argument("--username", help="MQTT username.")
    parser.add_argument("--password", help="MQTT password.")
    parser.add_argument("--cert", type=Path, help="Client certificate PEM path.")
    parser.add_argument("--key", type=Path, help="Client private key PEM path.")
    parser.add_argument(
        "-t",
        "--topic",
        action="append",
        help=f"Topic filter to subscribe to. May be repeated. Default: {DEFAULT_TOPIC}",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSONL path. Defaults to stdout.",
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Stop after this many messages.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Stop after this many seconds.",
    )
    parser.add_argument(
        "--client-id",
        help="MQTT client id. Defaults to a generated kobrax_capture_* id.",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Write payloads without redacting sensitive-looking fields.",
    )
    parser.add_argument(
        "--raw-payload",
        action="store_true",
        help="Include raw payload text alongside parsed JSON payloads.",
    )
    parser.add_argument(
        "--strict-tls",
        action="store_true",
        help="Verify broker TLS certificate instead of accepting the printer self-signed certificate.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return loaded

    config: dict[str, Any] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path}:{line_number}: expected 'key: value'")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"{path}:{line_number}: empty key")
        if value and value[0] in {"'", '"'} and value[-1:] == value[0]:
            value = value[1:-1]
        elif value.lower() in {"true", "false"}:
            config[key] = value.lower() == "true"
            continue
        else:
            try:
                config[key] = int(value)
                continue
            except ValueError:
                pass
        config[key] = value
    return config


def config_value(
    args: argparse.Namespace,
    config: Mapping[str, Any],
    arg_name: str,
    *config_names: str,
    default: Any = None,
) -> Any:
    value = getattr(args, arg_name)
    if value is not None:
        return value
    for name in config_names:
        if config.get(name) not in {None, ""}:
            return config[name]
    return default


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in SENSITIVE_KEYS:
                redacted[key] = "<redacted>"
            elif normalized in LARGE_KEYS and isinstance(child, str):
                redacted[key] = f"<redacted {len(child)} chars>"
            else:
                redacted[key] = redact(child)
        return redacted
    if isinstance(value, list):
        return [redact(child) for child in value]
    if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
        return f"{value[:MAX_STRING_LENGTH]}...<truncated {len(value)} chars>"
    return value


def decode_payload(payload: bytes) -> tuple[Any, str]:
    text = payload.decode("utf-8", errors="replace")
    try:
        return json.loads(text), text
    except json.JSONDecodeError:
        return text, text


def build_client(
    *,
    client_id: str,
    username: str,
    password: str,
    cert: str | Path | None,
    key: str | Path | None,
    strict_tls: bool,
) -> mqtt.Client:
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311,
    )
    client.username_pw_set(username, password)

    context = ssl.create_default_context()
    if not strict_tls:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    if cert and key:
        load_cert_chain(context, cert, key)
    client.tls_set_context(context)
    client.tls_insecure_set(not strict_tls)
    return client


def load_cert_chain(
    context: ssl.SSLContext, cert: str | Path, key: str | Path
) -> None:
    """Load a cert/key pair from paths or PEM text."""
    cert_text = str(cert)
    key_text = str(key)
    cert_path_value = path_if_existing(cert_text)
    key_path_value = path_if_existing(key_text)
    if cert_path_value and key_path_value:
        context.load_cert_chain(cert_path_value, key_path_value)
        return

    cert_path: str | None = None
    key_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(ensure_trailing_newline(cert_text))
            cert_path = file.name
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(ensure_trailing_newline(key_text))
            key_path = file.name
        context.load_cert_chain(cert_path, key_path)
    finally:
        for path in (cert_path, key_path):
            if path is not None:
                try:
                    os.unlink(path)
                except OSError:
                    pass


def ensure_trailing_newline(value: str) -> str:
    return value if value.endswith("\n") else f"{value}\n"


def path_if_existing(value: str) -> str | None:
    if "\n" in value or "-----BEGIN " in value:
        return None
    try:
        path = Path(value).expanduser()
        return str(path) if path.exists() else None
    except OSError:
        return None


def open_output(path: Path | None):
    if path is None:
        return sys.stdout, False
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a", encoding="utf-8"), True


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    host = config_value(args, config, "host", "host")
    username = config_value(args, config, "username", "mqtt_username", "username")
    password = config_value(args, config, "password", "mqtt_password", "password")
    port = int(config_value(args, config, "port", "mqtt_port", "port", default=DEFAULT_PORT))
    cert = config_value(args, config, "cert", "client_cert", "cert", "device_cert")
    key = config_value(args, config, "key", "client_key", "key", "device_key")
    topics = args.topic or [DEFAULT_TOPIC]

    missing = [
        name
        for name, value in (
            ("host", host),
            ("username", username),
            ("password", password),
        )
        if not value
    ]
    if missing:
        print(
            f"Missing required setting(s): {', '.join(missing)}. "
            "Pass CLI args or create .local/anycubic_kobrax.dev.yaml.",
            file=sys.stderr,
        )
        return 2

    cert_value = Path(cert).expanduser() if isinstance(cert, Path) else cert
    key_value = Path(key).expanduser() if isinstance(key, Path) else key
    if bool(cert_value) != bool(key_value):
        print("Pass both --cert and --key, or neither.", file=sys.stderr)
        return 2

    try:
        import paho.mqtt.client as mqtt_module
    except ModuleNotFoundError:
        print(
            "Missing dependency: paho-mqtt. Install it in this environment or run "
            "from a Home Assistant environment that has paho-mqtt.",
            file=sys.stderr,
        )
        return 2

    global mqtt
    mqtt = mqtt_module

    stop_event = threading.Event()
    connected_event = threading.Event()
    done_event = threading.Event()
    message_count = 0
    output, should_close = open_output(args.output)

    def request_stop(_signum: int, _frame: Any) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    client = build_client(
        client_id=args.client_id or f"kobrax_capture_{uuid4()}",
        username=str(username),
        password=str(password),
        cert=cert_value,
        key=key_value,
        strict_tls=args.strict_tls,
    )

    def on_connect(
        client: mqtt.Client,
        _userdata: Any,
        _flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        if reason_code.is_failure:
            print(f"MQTT connection failed: {reason_code}", file=sys.stderr)
            stop_event.set()
            connected_event.set()
            return
        for topic in topics:
            client.subscribe(topic)
            print(f"Subscribed to {topic}", file=sys.stderr)
        connected_event.set()

    def on_message(
        _client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        nonlocal message_count
        payload, raw_text = decode_payload(message.payload)
        if not args.no_redact:
            payload = redact(payload)

        record: dict[str, Any] = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "topic": message.topic,
            "qos": message.qos,
            "retain": message.retain,
            "payload": payload,
        }
        if args.raw_payload:
            record["raw_payload"] = raw_text if args.no_redact else redact(raw_text)

        output.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        output.flush()
        message_count += 1
        if args.count is not None and message_count >= args.count:
            done_event.set()
            stop_event.set()

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print(f"Connecting to {host}:{port}", file=sys.stderr)
        client.connect(str(host), port, keepalive=60)
        client.loop_start()

        if not connected_event.wait(timeout=10):
            print("Timed out waiting for MQTT connection.", file=sys.stderr)
            return 1

        deadline = time.monotonic() + args.duration if args.duration else None
        while not stop_event.is_set():
            if deadline is not None and time.monotonic() >= deadline:
                break
            done_event.wait(timeout=0.25)
    finally:
        stop_event.set()
        client.loop_stop()
        client.disconnect()
        if should_close:
            output.close()

    print(f"Captured {message_count} message(s).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
