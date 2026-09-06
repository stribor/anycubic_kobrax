"""Protocol regressions using real modules and lightweight HA boundary stubs.

Run with: python -m unittest discover -s tests
The MQTT dependency from requirements.txt must be installed. No broker is used.
"""

from dataclasses import dataclass
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class CoordinatorStub:
    def __class_getitem__(cls, _item):
        return cls

    def __init__(self, hass, *_args, **_kwargs):
        self.hass = hass
        self.data = {}

    def async_set_updated_data(self, data):
        self.data = data


@dataclass(frozen=True, kw_only=True)
class DescriptionStub:
    key: str
    translation_key: str = ""
    icon: str | None = None
    device_class: str | None = None
    native_unit_of_measurement: str | None = None
    state_class: str | None = None
    entity_category: str | None = None
    entity_registry_enabled_default: bool = True


def load_modules():
    """Import whole integration modules, including sensor initialization."""
    definitions = {
        "homeassistant.config_entries": {"ConfigEntry": object},
        "homeassistant.const": {
            "CONF_HOST": "host", "CONF_NAME": "name", "PERCENTAGE": "%",
            "UnitOfTemperature": SimpleNamespace(CELSIUS="°C"),
        },
        "homeassistant.core": {"HomeAssistant": object, "callback": lambda f: f},
        "homeassistant.exceptions": {"ConfigEntryNotReady": RuntimeError, "HomeAssistantError": RuntimeError},
        "homeassistant.helpers.update_coordinator": {
            "DataUpdateCoordinator": CoordinatorStub,
            "CoordinatorEntity": CoordinatorStub, "UpdateFailed": RuntimeError,
        },
        "homeassistant.helpers.device_registry": {"DeviceInfo": dict},
        "homeassistant.helpers.entity": {"EntityCategory": SimpleNamespace(DIAGNOSTIC="diagnostic")},
        "homeassistant.helpers.entity_platform": {"AddEntitiesCallback": object},
        "homeassistant.components.sensor": {
            "SensorDeviceClass": SimpleNamespace(TEMPERATURE="temperature"),
            "SensorEntity": type("SensorEntity", (), {}),
            "SensorEntityDescription": DescriptionStub,
            "SensorStateClass": SimpleNamespace(MEASUREMENT="measurement"),
        },
    }
    modules = {}
    for name, attrs in definitions.items():
        module = ModuleType(name)
        module.__dict__.update(attrs)
        modules[name] = module
    package = ModuleType("_protocol_test_integration")
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/anycubic_kobrax")]
    modules[package.__name__] = package
    with patch.dict(sys.modules, modules):
        coordinator = importlib.import_module(f"{package.__name__}.coordinator")
        sensor = importlib.import_module(f"{package.__name__}.sensor")
    return coordinator, sensor


coordinator_module, sensor_module = load_modules()


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        entry = SimpleNamespace(data={
            "host": "192.0.2.1", "type_id": "20030", "printer_id": "test",
            "mqtt_username": "test", "mqtt_password": "test",
        }, options={}, entry_id="test")
        self.c = coordinator_module.AnycubicKobraXCoordinator(SimpleNamespace(bus=Mock()), entry)
        self.c._connected = True
        self.c._publish = Mock()
        self.c._merge_preview_image = Mock()

    def merge(self, kind, action, state=None, data=None, **extra):
        payload = {"type": kind, "action": action, "state": state, "data": data, "code": 200, **extra}
        self.c._merge_payload(f"anycubic/printer/public/20030/test/{kind}/report", payload)

    def printing(self):
        self.merge("print", "start", "printing", {
            "taskid": "-1", "filename": "test.gcode", "print_time": 17,
            "remain_time": 2, "supplies_usage": 1397, "progress": 90,
        })

    def test_client_commands_and_metadata_never_finish_print(self):
        self.printing()
        before = dict(self.c._state)
        for action in ("query", "getTaskSettings", "getSliceParam"):
            self.c._merge_payload("anycubic/web/printer/20030/test/print", {
                "type": "print", "action": action, "data": None,
            })
        self.merge("print", "getTaskSettings", "done", {})
        self.assertEqual(self.c._state, before)
        self.merge("print", "getSliceParam", "done", {"slice_param": {"remain_time": 0, "temperature": 220}})
        self.assertEqual(self.c._state["remaining_time"], 120)
        self.assertEqual(self.c.latest_event["event_type"], "print_printing")

    def test_file_estimates_and_box_timers_are_isolated(self):
        self.printing()
        live_usage = self.c._state["filament_used"]
        filaments = [{"filament_used": .45, "paint_index": 0}, {"filament_used": 2.93, "paint_index": 1}]
        self.merge("file", "fileDetails", "done", {"file_details": {
            "paint_infos": filaments, "objects_skip_parts": ["first", "second"],
        }})
        self.assertEqual(self.c._state["estimate_weight"], 3.38)
        self.assertEqual(self.c._state["file_filaments"], filaments)
        self.assertEqual(self.c._state["filament_used"], live_usage)
        self.merge("multiColorBox", "getInfo", "success", {"multi_color_box": [{
            "drying_status": {"duration": 0, "remain_time": 0},
        }]})
        self.assertEqual(self.c._state["total_time"], 1020)
        self.assertEqual(self.c._state["remaining_time"], 120)
        self.merge("skip", "query_obj", "done", {"objects_skip_parts": []})
        self.assertEqual(self.c._state["skipped_objects"], [])

    def test_finished_result_survives_idle_and_queries(self):
        self.printing()
        self.merge("print", "start", "finished", {"filename": "test.gcode", "taskid": "-1", "progress": 100})
        sequence = self.c.latest_event["sequence"]
        self.merge("status", "workReport", "free")
        self.merge("print", "query")
        self.merge("info", "report", "done", {"state": "free", "project": None})
        self.assertEqual(self.c._state["print_state"], "finished")
        self.assertEqual(self.c._state["work_state"], "free")
        self.assertEqual(self.c.latest_event["sequence"], sequence)

    def test_poll_rate_new_job_and_idle(self):
        self.printing()
        self.c._publish.reset_mock()
        for now in (0, 1, 30, 59, 60, 61):
            with patch.object(coordinator_module.time, "monotonic", return_value=now):
                self.c._async_handle_message(
                    "anycubic/printer/public/20030/test/tempature/report",
                    {"type": "tempature", "data": {"curr_nozzle_temp": 210}},
                    "{}",
                )
        self.assertEqual(self.c._publish.call_count, 2)
        self.assertEqual(self.c._publish.call_args.args[1]["data"], {"taskid": "-1"})
        self.c._state["print_params"] = {"layer_height": .2}
        self.merge("print", "start", "finished", {"filename": "test.gcode"})
        self.c._request_slice_parameters_if_due()
        self.assertEqual(self.c._publish.call_count, 2)
        self.printing()  # Repeat the same file and local task ID.
        self.assertNotIn("print_params", self.c._state)
        with patch.object(coordinator_module.time, "monotonic", return_value=62):
            self.c._request_slice_parameters_if_due()
        self.assertEqual(self.c._publish.call_count, 4)  # File details + slice parameters.
        self.c._state["work_state"] = "free"
        self.c._request_slice_parameters_if_due()
        self.assertEqual(self.c._publish.call_count, 4)

    def test_paused_polling_stops_when_disconnected(self):
        self.printing()
        self.merge("print", "pause", "paused", {"taskid": "-1"})
        self.c._publish.reset_mock()
        with patch.object(coordinator_module.time, "monotonic", return_value=100):
            self.c._request_slice_parameters_if_due()
        self.assertEqual(self.c._publish.call_count, 1)
        self.c._connected = False
        with patch.object(coordinator_module.time, "monotonic", return_value=200):
            self.c._request_slice_parameters_if_due()
        self.assertEqual(self.c._publish.call_count, 1)

    def test_sensor_attributes(self):
        self.c.data = {"print_objects": ["first", "second"], "estimate_weight": 3.38, "file_filaments": [{"paint_index": 0}]}
        sensor = sensor_module.AnycubicKobraXSensor.__new__(sensor_module.AnycubicKobraXSensor)
        sensor.coordinator = self.c
        sensor.entity_description = next(s for s in sensor_module.SENSORS if s.key == "print_objects")
        self.assertEqual(sensor.native_value, 2)
        self.assertEqual(sensor.extra_state_attributes, {"objects": ["first", "second"]})
        sensor.entity_description = next(s for s in sensor_module.SENSORS if s.key == "estimate_weight")
        self.assertEqual(sensor.extra_state_attributes, {"filaments": [{"paint_index": 0}]})

    def test_printer_telemetry_has_measurement_state_class(self):
        measurement_sensors = {
            "progress",
            "filament_used",
            "nozzle_temperature",
            "bed_temperature",
            "target_nozzle_temperature",
            "target_bed_temperature",
            "fan_speed",
            "aux_fan_speed",
        }
        descriptions = {
            description.key: description for description in sensor_module.SENSORS
        }
        for key in measurement_sensors:
            self.assertEqual(descriptions[key].state_class, "measurement")


if __name__ == "__main__":
    unittest.main()
