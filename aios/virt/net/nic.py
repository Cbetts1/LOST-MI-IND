"""
VirtualNIC: Simulates a virtual Network Interface Card with MAC/IP addressing,
send/receive packet queues, and statistics tracking.
"""
import logging
from collections import deque

logger = logging.getLogger(__name__)


class VirtualNIC:
    """Virtual Network Interface Card."""

    def __init__(self, mac: str = "02:VA:IO:S0:00:01", ip: str = "10.0.0.1"):
        self.mac = mac
        self.ip = ip
        self.send_queue: deque = deque()
        self.recv_queue: deque = deque()
        self._stats: dict = {
            "packets_sent": 0,
            "packets_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
        }
        self.up = True
        logger.info("VirtualNIC initialized: mac=%s ip=%s", mac, ip)

    def send(self, packet: dict) -> None:
        """Enqueue a packet for sending."""
        if not self.up:
            logger.warning("NIC is down, dropping outbound packet")
            return
        self.send_queue.append(packet)
        self._stats["packets_sent"] += 1
        payload = packet.get("payload", "")
        self._stats["bytes_sent"] += len(str(payload))
        logger.debug("NIC send: dst=%s proto=%s", packet.get("dst"), packet.get("proto"))

    def recv(self) -> dict | None:
        """Dequeue and return the next received packet, or None."""
        if not self.recv_queue:
            return None
        packet = self.recv_queue.popleft()
        self._stats["packets_received"] += 1
        payload = packet.get("payload", "")
        self._stats["bytes_received"] += len(str(payload))
        logger.debug("NIC recv: src=%s proto=%s", packet.get("src"), packet.get("proto"))
        return packet

    def inject(self, packet: dict) -> None:
        """Inject a packet into the receive queue (used by router/tests)."""
        self.recv_queue.append(packet)

    def get_stats(self) -> dict:
        """Return NIC statistics."""
        return {
            "mac": self.mac,
            "ip": self.ip,
            "up": self.up,
            "send_queue_len": len(self.send_queue),
            "recv_queue_len": len(self.recv_queue),
            **self._stats,
        }
