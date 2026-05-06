# Anycubic Kobra X Home Assistant integration

Custom Home Assistant integration for Anycubic FDM printers that expose the
local Anycubic MQTT API used by the Kobra X.

Setup only needs the printer's LAN IP address. The printer must be online, on
the same network as Home Assistant, and have LAN mode enabled.

## Install

Copy `custom_components/anycubic_kobrax` into the `custom_components` directory
of your Home Assistant configuration, restart Home Assistant, then add the
integration from Settings > Devices & services.

## Configuration

Add the integration from Settings > Devices & services and enter the printer
host or IP address:

```yaml
host: 192.168.1.100
```

During setup the integration reads `http://<printer>:18910/info`, signs the
printer's LAN control request, decrypts the returned MQTT bundle, and stores the
local MQTT username, password, client certificate, client key, model ID, and
printer ID in the Home Assistant config entry.

Do not commit real printer IDs, host addresses, stream tokens, MQTT
credentials, client certificates, or client keys. For local development, keep
those in an ignored file such as `.local/anycubic_kobrax.dev.yaml`.

The camera stream path is optional. If the integration sees a MQTT video
response containing a `/live/<token>` path, it will use that. If token discovery
does not work, set the path manually in options, for example:

```text
/live/k5DawnaQ
```

## Implemented

- MQTT connection to the printer on port `9883`
- TLS with certificate validation disabled for the printer's self-signed cert
- IP-only setup that discovers LAN MQTT credentials from port `18910`
- Periodic `status`, `info`, `tempature`, `fan`, `peripherie`, and `light`
  queries, plus `lastWill`, `multiColorBox`, and slicer `info`
- Sensors for print state, progress, filename, nozzle temperature, bed
  temperature, target temperatures, fan speeds, material, layer, and timing
- Diagnostic MQTT sensor exposing the last received topic and payload attributes
- Brightness-capable light entity using Anycubic's `0-100` brightness scale
- Camera entity that sends `startCapture`/`stopCapture` and exposes the FLV URL
  to Home Assistant's stream/ffmpeg pipeline
- Lovelace camera card with start/stop stream control and a synced printer light
  toggle
- Local Home Assistant brand icon at
  `custom_components/anycubic_kobrax/brand/icon.png`

## Still to improve

- SSDP/mDNS discovery for `uuid:fdm:...`
- More complete decoding once real MQTT payload samples are available
