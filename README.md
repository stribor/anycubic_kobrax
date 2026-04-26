# Anycubic Kobra X Home Assistant integration

Custom Home Assistant integration for Anycubic FDM printers that expose the
local Anycubic MQTT API used by the Kobra X.

This is an initial v0.1-style implementation. It assumes you already know the
printer host, `type_id`, and `printer_id`.

## Install

Copy `custom_components/anycubic_kobrax` into the `custom_components` directory
of your Home Assistant configuration, restart Home Assistant, then add the
integration from Settings > Devices & services.

## Configuration

Use the values discovered from your printer:

```yaml
host: 192.168.1.100
type_id: 20030
printer_id: your_printer_id
mqtt_username: your_mqtt_username
mqtt_password: your_mqtt_password
```

Do not commit real printer IDs, host addresses, stream tokens, or MQTT
credentials. For local development, keep those in an ignored file such as
`.local/anycubic_kobrax.dev.yaml`.

The camera stream path is optional. If the integration sees a MQTT video
response containing a `/live/<token>` path, it will use that. If token discovery
does not work yet, set the path manually in options, for example:

```text
/live/k5DawnaQ
```

## Implemented

- MQTT connection to the printer on port `9883`
- TLS with certificate validation disabled for the printer's self-signed cert
- Periodic `status`, `info`, `tempature`, `fan`, `peripherie`, and `light`
  queries, plus `lastWill`, `multiColorBox`, and slicer `info`
- Sensors for print state, progress, filename, nozzle temperature, bed
  temperature, target temperatures, fan speeds, material, layer, and timing
- Diagnostic MQTT sensor exposing the last received topic and payload attributes
- Brightness-capable light entity using Anycubic's `0-100` brightness scale
- Camera entity that sends `startCapture`/`stopCapture` and exposes the FLV URL
  to Home Assistant's stream/ffmpeg pipeline
- Local Home Assistant brand icon at
  `custom_components/anycubic_kobrax/brand/icon.png`

## Still to improve

- SSDP/mDNS discovery for `uuid:fdm:...`
- HTTP probing on ports `18088` and `18910`
- Automatic `type_id` and `printer_id` discovery
- More complete decoding once real MQTT payload samples are available
