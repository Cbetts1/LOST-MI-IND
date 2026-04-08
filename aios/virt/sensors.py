"""
sensors.py -- Virtual Sensors Suite for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualSensors simulates the full mobile sensor suite:
      battery, temperature, GPS, accelerometer, gyroscope, proximity, light.
  - Each sensor has a configurable simulated value and read() method.
  - Sensor calibration data loaded from /aios/data/hardware/sensor_config.json.
  - Consumed by: System Services (health), AI Control Plane (context awareness),
    Shell (status bar), Cloud Layer (telemetry).

Integration Points:
  - Battery level   -> System Services (power manager)
  - Temperature     -> System Services (thermal throttle trigger)
  - GPS             -> AI (location context)
  - Motion sensors  -> Shell/UI (orientation, gestures)
  - Metrics         -> HardwareMetrics
  - Hooks           -> HardwareHooks
"""

import json
import logging
import math
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("vaios.virt.sensors")

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "hardware", "sensor_config.json"
)

SENSOR_BATTERY      = "battery"
SENSOR_TEMPERATURE  = "temperature"
SENSOR_GPS          = "gps"
SENSOR_ACCELEROMETER = "accelerometer"
SENSOR_GYROSCOPE    = "gyroscope"
SENSOR_PROXIMITY    = "proximity"
SENSOR_AMBIENT_LIGHT = "ambient_light"

ALL_SENSORS = (
    SENSOR_BATTERY, SENSOR_TEMPERATURE, SENSOR_GPS,
    SENSOR_ACCELEROMETER, SENSOR_GYROSCOPE,
    SENSOR_PROXIMITY, SENSOR_AMBIENT_LIGHT,
)

DEFAULT_VALUES = {
    SENSOR_BATTERY:       {"level": 0.85, "charging": False, "voltage_v": 3.85},
    SENSOR_TEMPERATURE:   {"cpu_c": 38.0, "battery_c": 32.0, "ambient_c": 25.0},
    SENSOR_GPS:           {"lat": 0.0, "lon": 0.0, "alt_m": 0.0, "fix": False},
    SENSOR_ACCELEROMETER: {"x": 0.0, "y": 0.0, "z": 9.81},
    SENSOR_GYROSCOPE:     {"x": 0.0, "y": 0.0, "z": 0.0},
    SENSOR_PROXIMITY:     {"distance_cm": 10.0, "near": False},
    SENSOR_AMBIENT_LIGHT: {"lux": 300.0},
}


class VirtualSensors:
    """
    Simulates the full mobile sensor suite.

    Sensors can be read via read(sensor_id) or read_all().
    Values can be overridden via set_value() for simulation/testing.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        metrics=None,
        hooks=None,
    ) -> None:
        self.config_path = config_path or _DEFAULT_CONFIG_PATH
        self._metrics = metrics
        self._hooks = hooks
        self._values: Dict[str, Any] = {}
        self._read_counts: Dict[str, int] = {s: 0 for s in ALL_SENSORS}
        self._init_time = time.monotonic()
        self._load_config()
        logger.info(
            "[SNS]  VirtualSensors online -- %s",
            ", ".join(ALL_SENSORS),
        )
        if self._hooks:
            self._hooks.fire("sensors.init", {"sensors": list(ALL_SENSORS)})

    def _load_config(self) -> None:
        """Load sensor calibration config, falling back to defaults."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
                self._values = cfg.get("default_values", dict(DEFAULT_VALUES))
        except (FileNotFoundError, json.JSONDecodeError):
            self._values = {k: dict(v) for k, v in DEFAULT_VALUES.items()}

    def read(self, sensor_id: str) -> Dict[str, Any]:
        """
        Read the current value of a sensor.

        Args:
            sensor_id: One of the SENSOR_* constants.

        Returns:
            Dict with sensor reading(s).
        """
        if sensor_id not in ALL_SENSORS:
            raise ValueError(f"Unknown sensor: {sensor_id!r}")
        self._read_counts[sensor_id] += 1
        value = dict(self._values.get(sensor_id, {}))
        value["ts"] = time.monotonic()
        if self._metrics:
            self._metrics.increment_counter(f"sensors.{sensor_id}.reads")
            # Expose key scalar metrics as gauges
            if sensor_id == SENSOR_BATTERY:
                self._metrics.set_gauge("sensors.battery.level", value.get("level", 0))
            elif sensor_id == SENSOR_TEMPERATURE:
                self._metrics.set_gauge("sensors.temperature.cpu_c", value.get("cpu_c", 0))
        if self._hooks:
            self._hooks.fire(f"sensors.read.{sensor_id}", value)
        return value

    def read_all(self) -> Dict[str, Any]:
        """Read all sensors and return a combined dict."""
        return {s: self.read(s) for s in ALL_SENSORS}

    def set_value(self, sensor_id: str, values: Dict[str, Any]) -> None:
        """Override sensor values (for simulation or testing)."""
        if sensor_id not in ALL_SENSORS:
            raise ValueError(f"Unknown sensor: {sensor_id!r}")
        self._values[sensor_id] = values

    def simulate_motion(self, t: float) -> None:
        """Simulate sinusoidal motion on accelerometer/gyroscope."""
        self._values[SENSOR_ACCELEROMETER] = {
            "x": math.sin(t) * 2.0,
            "y": math.cos(t) * 1.5,
            "z": 9.81,
        }
        self._values[SENSOR_GYROSCOPE] = {
            "x": math.sin(t * 0.5) * 0.1,
            "y": math.cos(t * 0.5) * 0.1,
            "z": 0.0,
        }

    def introspect(self) -> Dict[str, Any]:
        return {
            "sensors": list(ALL_SENSORS),
            "read_counts": dict(self._read_counts),
            "current_values": {k: dict(v) for k, v in self._values.items()},
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        total_reads = sum(self._read_counts.values())
        return f"<VirtualSensors sensors={len(ALL_SENSORS)} total_reads={total_reads}>"
