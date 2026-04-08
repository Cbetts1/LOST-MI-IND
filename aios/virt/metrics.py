"""
metrics.py — Hardware Metrics Collection and Export for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - HardwareMetrics is a central metrics aggregator that all virt devices write into.
  - Metrics are stored as timestamped numeric samples keyed by metric name.
  - Supports counters, gauges, and histograms.
  - Metrics are consumed by: Cloud Layer (telemetry), AI Control Plane (resource scheduling),
    System Services (health monitor).
  - Designed for periodic polling (call collect() on a schedule) or push from each device.

Integration Points:
  - All virtual hardware devices register and write metrics here.
  - Cloud Layer reads metrics via export_snapshot().
  - AI Control Plane reads CPU/memory pressure metrics for scheduling decisions.
"""

import logging
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vaios.virt.metrics")

_MAX_SAMPLES = 500


class HardwareMetrics:
    """
    Aggregates numeric hardware metrics from all virtual devices.

    Metric types:
      gauge   — current value (overwritten on each write)
      counter — monotonically increasing value (accumulated)
      histogram — sliding window of samples
    """

    def __init__(self) -> None:
        self._gauges: Dict[str, float] = {}
        self._counters: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=_MAX_SAMPLES))
        self._last_collected: float = 0.0
        logger.info("[MET] HardwareMetrics initialized")

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric (current instantaneous value)."""
        self._gauges[name] = value

    def increment_counter(self, name: str, amount: float = 1.0) -> None:
        """Increment a counter metric."""
        self._counters[name] += amount

    def record_histogram(self, name: str, value: float) -> None:
        """Append a sample to a histogram metric."""
        self._histograms[name].append({"ts": time.monotonic(), "v": value})

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def get_gauge(self, name: str, default: float = 0.0) -> float:
        """Return the current value of a gauge metric."""
        return self._gauges.get(name, default)

    def get_counter(self, name: str) -> float:
        """Return the accumulated counter value."""
        return self._counters[name]

    def get_histogram(self, name: str) -> List[Dict[str, Any]]:
        """Return all histogram samples as a list."""
        return list(self._histograms[name])

    def get_histogram_stats(self, name: str) -> Dict[str, Optional[float]]:
        """Return basic stats (min, max, mean, last) for a histogram."""
        samples = [s["v"] for s in self._histograms[name]]
        if not samples:
            return {"min": None, "max": None, "mean": None, "last": None, "count": 0}
        return {
            "min": min(samples),
            "max": max(samples),
            "mean": sum(samples) / len(samples),
            "last": samples[-1],
            "count": len(samples),
        }

    # ------------------------------------------------------------------
    # Snapshot / Export
    # ------------------------------------------------------------------

    def collect(self) -> Dict[str, Any]:
        """
        Collect and return a full snapshot of all current metrics.
        Called by telemetry service or health monitor on a schedule.
        """
        self._last_collected = time.monotonic()
        snapshot = {
            "ts": time.time(),
            "gauges": dict(self._gauges),
            "counters": dict(self._counters),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self._histograms
            },
        }
        logger.debug("[MET] Snapshot collected: %d gauges, %d counters, %d histograms",
                     len(self._gauges), len(self._counters), len(self._histograms))
        return snapshot

    def export_snapshot(self) -> Dict[str, Any]:
        """Alias for collect(); intended for external consumers (Cloud, AI)."""
        return self.collect()

    def reset_counters(self) -> None:
        """Reset all counters to zero (e.g. after a reporting period)."""
        self._counters.clear()

    def list_metric_names(self) -> Dict[str, List[str]]:
        """Return all registered metric names by type."""
        return {
            "gauges": list(self._gauges.keys()),
            "counters": list(self._counters.keys()),
            "histograms": list(self._histograms.keys()),
        }

    def __repr__(self) -> str:
        return (
            f"<HardwareMetrics gauges={len(self._gauges)} "
            f"counters={len(self._counters)} "
            f"histograms={len(self._histograms)}>"
        )


# Module-level singleton
_metrics_instance: HardwareMetrics = None  # type: ignore


def get_metrics() -> HardwareMetrics:
    """Return the global HardwareMetrics singleton."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = HardwareMetrics()
    return _metrics_instance
