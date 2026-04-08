"""
VirtualCPU: Simulates a multi-core CPU with clock speed, usage tracking,
cycle allocation, and metrics emission for the VAI-OS virtual hardware layer.
"""
import logging
import threading
import time

logger = logging.getLogger(__name__)


class VirtualCPU:
    """Simulates a virtual CPU with configurable cores and clock speed."""

    def __init__(self, cores: int = 4, clock_hz: int = 2_400_000_000):
        self.cores = cores
        self.clock_hz = clock_hz
        self._usage: float = 0.0
        self._allocated_cycles: int = 0
        self._total_cycles_issued: int = 0
        self._lock = threading.Lock()
        self._metrics: dict = {
            "allocate_calls": 0,
            "release_calls": 0,
            "allocation_failures": 0,
        }
        logger.info("VirtualCPU initialized: cores=%d clock_hz=%d", cores, clock_hz)

    @property
    def usage(self) -> float:
        """Return current CPU usage as a percentage (0-100)."""
        return self._usage

    def allocate_cycles(self, n: int) -> bool:
        """
        Attempt to allocate n CPU cycles.

        Returns True if allocation succeeded, False if over capacity.
        """
        with self._lock:
            self._metrics["allocate_calls"] += 1
            max_cycles = self.cores * self.clock_hz
            if self._allocated_cycles + n > max_cycles:
                self._metrics["allocation_failures"] += 1
                logger.warning(
                    "CPU cycle allocation failed: requested=%d available=%d",
                    n,
                    max_cycles - self._allocated_cycles,
                )
                return False
            self._allocated_cycles += n
            self._total_cycles_issued += n
            self._usage = (self._allocated_cycles / max_cycles) * 100.0
            logger.debug("Allocated %d cycles, usage=%.2f%%", n, self._usage)
            return True

    def release_cycles(self, n: int) -> None:
        """Release n previously allocated CPU cycles."""
        with self._lock:
            self._metrics["release_calls"] += 1
            self._allocated_cycles = max(0, self._allocated_cycles - n)
            max_cycles = self.cores * self.clock_hz
            self._usage = (self._allocated_cycles / max_cycles) * 100.0
            logger.debug("Released %d cycles, usage=%.2f%%", n, self._usage)

    def get_stats(self) -> dict:
        """Return a snapshot of CPU statistics."""
        with self._lock:
            return {
                "cores": self.cores,
                "clock_hz": self.clock_hz,
                "usage_pct": round(self._usage, 2),
                "allocated_cycles": self._allocated_cycles,
                "total_cycles_issued": self._total_cycles_issued,
                "metrics": dict(self._metrics),
            }
