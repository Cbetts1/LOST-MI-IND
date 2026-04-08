"""
VirtualIO: Simulates I/O device buffers (stdin, stdout, stderr, and custom
devices) using deque-based queues for the VAI-OS virtual hardware layer.
"""
import logging
from collections import deque

logger = logging.getLogger(__name__)

_DEFAULT_DEVICES = ("stdin", "stdout", "stderr")


class VirtualIO:
    """Manages virtual I/O device buffers."""

    def __init__(self):
        self.devices: dict[str, deque] = {}
        self._metrics: dict = {"writes": 0, "reads": 0, "read_misses": 0}
        for name in _DEFAULT_DEVICES:
            self.register_device(name)
        logger.info("VirtualIO initialized with default devices: %s", list(_DEFAULT_DEVICES))

    def register_device(self, name: str) -> None:
        """Register a new named I/O device buffer."""
        if name not in self.devices:
            self.devices[name] = deque()
            logger.debug("Registered I/O device: %s", name)

    def write(self, device: str, data: str) -> None:
        """Write data to the specified device buffer."""
        if device not in self.devices:
            self.register_device(device)
        self.devices[device].append(data)
        self._metrics["writes"] += 1
        logger.debug("IO write -> device=%s len=%d", device, len(data))

    def read(self, device: str) -> str:
        """
        Read and return the next item from the device buffer.

        Returns an empty string if the buffer is empty.
        """
        self._metrics["reads"] += 1
        if device not in self.devices or not self.devices[device]:
            self._metrics["read_misses"] += 1
            return ""
        data = self.devices[device].popleft()
        logger.debug("IO read <- device=%s len=%d", device, len(data))
        return data

    def peek(self, device: str) -> str:
        """Return the next item without removing it, or empty string."""
        if device not in self.devices or not self.devices[device]:
            return ""
        return self.devices[device][0]

    def get_stats(self) -> dict:
        """Return I/O statistics and device buffer sizes."""
        return {
            "devices": {name: len(buf) for name, buf in self.devices.items()},
            "metrics": dict(self._metrics),
        }
