#!/usr/bin/env python3
"""Extract file preview images from Anycubic MQTT JSONL captures."""

from __future__ import annotations

import argparse
import base64
import binascii
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any


IMAGE_FIELDS = {
    "png_image": ".png",
    "thumbnail": ".png",
    "svg_image": ".svg",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract png_image, thumbnail, and svg_image fields from MQTT JSONL captures."
    )
    parser.add_argument(
        "capture",
        nargs="?",
        type=Path,
        default=Path(".local/mqtt-capture.jsonl"),
        help="MQTT JSONL capture path.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path(".local/mqtt-images"),
        help="Directory for extracted image files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    counters: Counter[str] = Counter()
    written: list[Path] = []
    seen: set[tuple[str, str]] = set()

    with args.capture.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            record = json.loads(line)
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            details = _file_details(payload)
            if not details:
                continue

            filename = _safe_name(
                str(payload.get("data", {}).get("filename") or f"line-{line_number}")
            )
            for field, suffix in IMAGE_FIELDS.items():
                encoded = details.get(field)
                counters[f"{field}_seen"] += int(encoded is not None)
                if not isinstance(encoded, str) or not encoded:
                    continue
                if encoded.startswith("<redacted"):
                    counters[f"{field}_redacted"] += 1
                    continue
                if "<truncated" in encoded:
                    counters[f"{field}_truncated"] += 1
                    continue

                try:
                    decoded = base64.b64decode(encoded, validate=True)
                except (binascii.Error, ValueError):
                    counters[f"{field}_invalid_base64"] += 1
                    continue

                digest_key = (field, decoded[:64].hex() + str(len(decoded)))
                if digest_key in seen:
                    counters[f"{field}_duplicate"] += 1
                    continue
                seen.add(digest_key)

                if field == "svg_image":
                    output = args.output_dir / f"{filename}-{field}{suffix}"
                    output.write_bytes(decoded)
                else:
                    output = args.output_dir / f"{filename}-{field}{suffix}"
                    output.write_bytes(decoded)
                written.append(output)
                counters[f"{field}_written"] += 1

    for path in written:
        print(path)
    if counters:
        print("\nSummary:")
        for key, value in sorted(counters.items()):
            print(f"{key}: {value}")
    else:
        print("No file image payloads found.")
    return 0


def _file_details(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    details = data.get("file_details")
    return details if isinstance(details, dict) else None


def _safe_name(value: str) -> str:
    name = Path(value).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:120] or "mqtt-image"


if __name__ == "__main__":
    raise SystemExit(main())
