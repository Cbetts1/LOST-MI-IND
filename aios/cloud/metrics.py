"""
CloudMetrics: Provides counters, gauges, and histograms for VAI-OS cloud
telemetry with snapshot capabilities for dashboards and scaling decisions.
"""
import logging

logger = logging.getLogger(__name__)


class CloudMetrics:
    """Telemetry store for cloud counters, gauges, and histograms."""

    def __init__(self):
        self.counters: dict[str, float] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list] = {}
        logger.info("CloudMetrics initialized")

    def increment(self, name: str, value: float = 1.0) -> None:
        """Increment a named counter by value."""
        self.counters[name] = self.counters.get(name, 0.0) + value
        logger.debug("Metric increment: %s += %s", name, value)

    def gauge_set(self, name: str, value: float) -> None:
        """Set a named gauge to value."""
        self.gauges[name] = value
        logger.debug("Metric gauge_set: %s = %s", name, value)

    def histogram_record(self, name: str, value: float) -> None:
        """Record a value in a named histogram."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)
        # Keep histograms bounded
        if len(self.histograms[name]) > 10_000:
            self.histograms[name] = self.histograms[name][-5_000:]
        logger.debug("Metric histogram_record: %s = %s", name, value)

    def snapshot(self) -> dict:
        """Return a point-in-time snapshot of all metrics."""
        histo_summaries = {}
        for name, values in self.histograms.items():
            if values:
                histo_summaries[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": histo_summaries,
        }
