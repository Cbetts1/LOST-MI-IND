"""
VirtualRAM: Simulates system memory with allocation, deallocation, and
usage tracking for the VAI-OS virtual hardware layer.
"""
import logging
import threading

logger = logging.getLogger(__name__)


class VirtualRAM:
    """Simulates virtual RAM with configurable total capacity."""

    def __init__(self, total_mb: float = 2048.0):
        self.total_mb = total_mb
        self._used_mb: float = 0.0
        self._lock = threading.Lock()
        self._metrics: dict = {
            "allocate_calls": 0,
            "free_calls": 0,
            "allocation_failures": 0,
            "peak_used_mb": 0.0,
        }
        logger.info("VirtualRAM initialized: total_mb=%.1f", total_mb)

    @property
    def used_mb(self) -> float:
        """Return currently used memory in MB."""
        return self._used_mb

    @property
    def free_mb(self) -> float:
        """Return free memory in MB."""
        return self.total_mb - self._used_mb

    def allocate(self, mb: float) -> bool:
        """
        Attempt to allocate mb megabytes.

        Returns True on success, False if insufficient memory.
        """
        with self._lock:
            self._metrics["allocate_calls"] += 1
            if self._used_mb + mb > self.total_mb:
                self._metrics["allocation_failures"] += 1
                logger.warning(
                    "RAM allocation failed: requested=%.1fMB free=%.1fMB",
                    mb,
                    self.free_mb,
                )
                return False
            self._used_mb += mb
            if self._used_mb > self._metrics["peak_used_mb"]:
                self._metrics["peak_used_mb"] = self._used_mb
            logger.debug("Allocated %.1fMB RAM, used=%.1fMB", mb, self._used_mb)
            return True

    def free(self, mb: float) -> None:
        """Free mb megabytes of previously allocated memory."""
        with self._lock:
            self._metrics["free_calls"] += 1
            self._used_mb = max(0.0, self._used_mb - mb)
            logger.debug("Freed %.1fMB RAM, used=%.1fMB", mb, self._used_mb)

    def get_stats(self) -> dict:
        """Return a snapshot of RAM statistics."""
        with self._lock:
            return {
                "total_mb": self.total_mb,
                "used_mb": round(self._used_mb, 2),
                "free_mb": round(self.free_mb, 2),
                "usage_pct": round((self._used_mb / self.total_mb) * 100.0, 2),
                "metrics": dict(self._metrics),
            }
