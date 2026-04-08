"""
radio.py -- Virtual Radio Subsystem for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualRadio simulates cellular (LTE/5G), WiFi 6, and Bluetooth 5.2 radios.
  - Each radio can be powered on/off independently.
  - transmit(freq, data) / receive(freq) provide a simple virtual RF interface.
  - Signal strength is simulated with configurable RSSI values.
  - Consumed by: Network Layer (cellular, wifi, bt transport), Cloud Layer.

Integration Points:
  - Cellular       -> Network Layer (WWAN interface)
  - WiFi           -> Network Layer (WLAN interface, also NIC)
  - Bluetooth      -> System Services (peripherals, audio)
  - Radio metrics  -> HardwareMetrics
  - Hooks          -> HardwareHooks
"""

import logging
import queue
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vaios.virt.radio")

RADIO_CELLULAR  = "cellular"
RADIO_WIFI      = "wifi"
RADIO_BLUETOOTH = "bluetooth"

ALL_RADIOS = (RADIO_CELLULAR, RADIO_WIFI, RADIO_BLUETOOTH)


class RadioPacket:
    """Represents a virtual radio transmission."""
    def __init__(self, radio: str, freq_mhz: float, data: bytes) -> None:
        self.radio = radio
        self.freq_mhz = freq_mhz
        self.data = data
        self.timestamp = time.monotonic()
        self.size = len(data)

    def __repr__(self) -> str:
        return f"<RadioPacket radio={self.radio} freq={self.freq_mhz}MHz size={self.size}B>"


class RadioInterface:
    """Simulates a single radio (cellular, WiFi, or Bluetooth)."""

    def __init__(self, radio_type: str, default_freq_mhz: float) -> None:
        self.radio_type = radio_type
        self.default_freq_mhz = default_freq_mhz
        self._powered: bool = False
        self._rssi_dbm: float = -65.0
        self._tx_queue: queue.Queue = queue.Queue(maxsize=512)
        self._rx_queue: queue.Queue = queue.Queue(maxsize=512)
        self._tx_count: int = 0
        self._rx_count: int = 0

    def power_on(self) -> None:
        self._powered = True
        logger.debug("[RAD] %s radio powered ON", self.radio_type)

    def power_off(self) -> None:
        self._powered = False
        logger.debug("[RAD] %s radio powered OFF", self.radio_type)

    def is_powered(self) -> bool:
        return self._powered

    def transmit(self, freq_mhz: float, data: bytes) -> None:
        if not self._powered:
            raise IOError(f"{self.radio_type} radio is powered off")
        pkt = RadioPacket(self.radio_type, freq_mhz, data)
        self._tx_queue.put_nowait(pkt)
        self._tx_count += 1

    def receive(self, freq_mhz: Optional[float] = None) -> Optional[RadioPacket]:
        try:
            pkt = self._rx_queue.get_nowait()
            self._rx_count += 1
            return pkt
        except queue.Empty:
            return None

    def inject_rx(self, pkt: RadioPacket) -> None:
        """Inject a received packet (for simulation/testing)."""
        self._rx_queue.put_nowait(pkt)

    def set_rssi(self, rssi_dbm: float) -> None:
        self._rssi_dbm = rssi_dbm

    def get_rssi(self) -> float:
        return self._rssi_dbm

    def introspect(self) -> Dict[str, Any]:
        return {
            "type": self.radio_type,
            "powered": self._powered,
            "rssi_dbm": self._rssi_dbm,
            "tx_count": self._tx_count,
            "rx_count": self._rx_count,
        }


class VirtualRadio:
    """
    Simulates the full mobile radio subsystem.

    Radios:
      - Cellular: LTE/5G  (default band 2100 MHz)
      - WiFi: 802.11ax/6  (default 5180 MHz / 5GHz)
      - Bluetooth: 5.2    (default 2402 MHz)
    """

    RADIO_DEFAULTS = {
        RADIO_CELLULAR:  2100.0,
        RADIO_WIFI:      5180.0,
        RADIO_BLUETOOTH: 2402.0,
    }

    def __init__(self, metrics=None, hooks=None) -> None:
        self._metrics = metrics
        self._hooks = hooks
        self._radios: Dict[str, RadioInterface] = {
            r: RadioInterface(r, freq)
            for r, freq in self.RADIO_DEFAULTS.items()
        }
        self._init_time = time.monotonic()
        # Power on all radios by default
        for r in self._radios.values():
            r.power_on()
        logger.info("[RAD]  VirtualRadio online -- LTE/5G, WiFi6, BT5.2")
        if self._hooks:
            self._hooks.fire("radio.init", {"radios": list(ALL_RADIOS)})

    def transmit(self, radio: str, freq_mhz: float, data: bytes) -> None:
        """Transmit data on the specified radio at the given frequency."""
        if radio not in self._radios:
            raise ValueError(f"Unknown radio: {radio!r}")
        self._radios[radio].transmit(freq_mhz, data)
        if self._metrics:
            self._metrics.increment_counter(f"radio.{radio}.tx_count")
            self._metrics.increment_counter(f"radio.{radio}.tx_bytes", len(data))
        if self._hooks:
            self._hooks.fire("radio.transmit", {"radio": radio, "freq": freq_mhz, "size": len(data)})

    def receive(self, radio: str, freq_mhz: Optional[float] = None) -> Optional[RadioPacket]:
        """Receive a packet from the specified radio."""
        if radio not in self._radios:
            raise ValueError(f"Unknown radio: {radio!r}")
        pkt = self._radios[radio].receive(freq_mhz)
        if pkt and self._metrics:
            self._metrics.increment_counter(f"radio.{radio}.rx_count")
        if pkt and self._hooks:
            self._hooks.fire("radio.receive", {"radio": radio, "size": pkt.size})
        return pkt

    def power_on(self, radio: str) -> None:
        self._radios[radio].power_on()
        if self._hooks:
            self._hooks.fire("radio.power", {"radio": radio, "state": "on"})

    def power_off(self, radio: str) -> None:
        self._radios[radio].power_off()
        if self._hooks:
            self._hooks.fire("radio.power", {"radio": radio, "state": "off"})

    def get_rssi(self, radio: str) -> float:
        return self._radios[radio].get_rssi()

    def set_rssi(self, radio: str, rssi_dbm: float) -> None:
        self._radios[radio].set_rssi(rssi_dbm)
        if self._metrics:
            self._metrics.set_gauge(f"radio.{radio}.rssi_dbm", rssi_dbm)

    def get_interface(self, radio: str) -> RadioInterface:
        return self._radios[radio]

    def introspect(self) -> Dict[str, Any]:
        return {
            "radios": {r: iface.introspect() for r, iface in self._radios.items()},
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        states = {r: ("ON" if i.is_powered() else "OFF") for r, i in self._radios.items()}
        return f"<VirtualRadio {states}>"
