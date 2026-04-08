"""
nic.py -- Virtual Network Interface Card for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualNIC simulates an Ethernet/WiFi network interface.
  - Implements send()/recv() queue model: sent packets go to a TX queue;
    received packets are pushed into an RX queue by the caller.
  - MAC address is auto-generated as a VAI-OS local administered address.
  - MTU defaults to 1500 bytes.
  - Consumed by: Network Layer (TCP/IP stack), Cloud Layer (telemetry upload).

Integration Points:
  - NIC TX/RX queues  -> Network Layer (stack.py)
  - Link state change -> OS Kernel interrupt simulation
  - Metrics           -> HardwareMetrics
  - Hooks             -> HardwareHooks
"""

import logging
import queue
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("vaios.virt.nic")

VAIOS_NIC_MAC = "02:VA:10:50:00:01"
DEFAULT_MTU = 1500
DEFAULT_SPEED_MBPS = 1000


class NetworkPacket:
    """Represents a virtual network packet."""
    def __init__(self, src_mac: str, dst_mac: str, payload: bytes, proto: str = "ETH") -> None:
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.payload = payload
        self.proto = proto
        self.timestamp = time.monotonic()
        self.size = len(payload)

    def __repr__(self) -> str:
        return f"<Packet src={self.src_mac} dst={self.dst_mac} proto={self.proto} size={self.size}B>"


class VirtualNIC:
    """
    Simulates a virtual network interface card.

    Provides TX/RX packet queue model for the Network Layer.
    """

    def __init__(
        self,
        mac: str = VAIOS_NIC_MAC,
        mtu: int = DEFAULT_MTU,
        speed_mbps: int = DEFAULT_SPEED_MBPS,
        metrics=None,
        hooks=None,
    ) -> None:
        self.mac = mac
        self.mtu = mtu
        self.speed_mbps = speed_mbps
        self._metrics = metrics
        self._hooks = hooks
        self._tx_queue: queue.Queue = queue.Queue(maxsize=1024)
        self._rx_queue: queue.Queue = queue.Queue(maxsize=1024)
        self._tx_bytes: int = 0
        self._rx_bytes: int = 0
        self._tx_packets: int = 0
        self._rx_packets: int = 0
        self._link_up: bool = True
        self._init_time = time.monotonic()
        logger.info("[NIC]  VirtualNIC online -- mac=%s mtu=%d speed=%dMbps", mac, mtu, speed_mbps)
        if self._hooks:
            self._hooks.fire("nic.init", {"mac": mac, "mtu": mtu})

    def send(self, packet: NetworkPacket) -> None:
        """Enqueue a packet for transmission."""
        if not self._link_up:
            raise IOError("NIC link is down")
        if packet.size > self.mtu:
            raise ValueError(f"Packet size {packet.size} exceeds MTU {self.mtu}")
        self._tx_queue.put_nowait(packet)
        self._tx_bytes += packet.size
        self._tx_packets += 1
        if self._metrics:
            self._metrics.set_gauge("nic.tx_bytes", self._tx_bytes)
            self._metrics.increment_counter("nic.tx_packets")
        if self._hooks:
            self._hooks.fire("nic.send", {"size": packet.size, "proto": packet.proto})

    def recv(self, timeout: float = 0.0) -> Optional[NetworkPacket]:
        """Dequeue a received packet (returns None if none available)."""
        try:
            packet = self._rx_queue.get(block=timeout > 0, timeout=timeout or None)
            self._rx_bytes += packet.size
            self._rx_packets += 1
            if self._metrics:
                self._metrics.set_gauge("nic.rx_bytes", self._rx_bytes)
                self._metrics.increment_counter("nic.rx_packets")
            if self._hooks:
                self._hooks.fire("nic.recv", {"size": packet.size})
            return packet
        except queue.Empty:
            return None

    def inject_packet(self, packet: NetworkPacket) -> None:
        """Inject a packet into the RX queue (used by test/simulation code)."""
        self._rx_queue.put_nowait(packet)

    def drain_tx_queue(self):
        """Drain and return all packets from TX queue (for simulation)."""
        packets = []
        while not self._tx_queue.empty():
            try:
                packets.append(self._tx_queue.get_nowait())
            except queue.Empty:
                break
        return packets

    def set_link_up(self, state: bool) -> None:
        self._link_up = state
        if self._hooks:
            self._hooks.fire("nic.link_change", {"link_up": state})
        logger.info("[NIC] Link state -> %s", "UP" if state else "DOWN")

    def introspect(self) -> Dict[str, Any]:
        return {
            "mac": self.mac,
            "mtu": self.mtu,
            "speed_mbps": self.speed_mbps,
            "link_up": self._link_up,
            "tx_bytes": self._tx_bytes,
            "tx_packets": self._tx_packets,
            "rx_bytes": self._rx_bytes,
            "rx_packets": self._rx_packets,
            "tx_queue_depth": self._tx_queue.qsize(),
            "rx_queue_depth": self._rx_queue.qsize(),
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        return f"<VirtualNIC mac={self.mac} link={'UP' if self._link_up else 'DOWN'} mtu={self.mtu}>"
