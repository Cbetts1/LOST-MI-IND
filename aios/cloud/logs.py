"""
CloudLogger: Structured log store for VAI-OS cloud services with
level/source filtering and tail queries.
"""
import logging
import time
from collections import deque

logger = logging.getLogger(__name__)

_LEVELS = ("debug", "info", "warning", "error", "critical")


class CloudLogger:
    """Stores structured cloud log entries with query support."""

    def __init__(self, maxlen: int = 10_000):
        self.entries: deque = deque(maxlen=maxlen)
        self._metrics: dict = {
            "total_logged": 0,
            "by_level": {lvl: 0 for lvl in _LEVELS},
        }
        logger.info("CloudLogger initialized (maxlen=%d)", maxlen)

    def log(self, level: str, source: str, message: str, **extra) -> None:
        """Append a structured log entry."""
        level = level.lower()
        entry = {
            "ts": time.time(),
            "level": level,
            "source": source,
            "message": message,
            **extra,
        }
        self.entries.append(entry)
        self._metrics["total_logged"] += 1
        self._metrics["by_level"][level] = self._metrics["by_level"].get(level, 0) + 1
        logger.debug("CloudLog [%s] %s: %s", level, source, message)

    def query(
        self,
        level: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Filter log entries by level and/or source."""
        results = list(self.entries)
        if level:
            results = [e for e in results if e["level"] == level.lower()]
        if source:
            results = [e for e in results if e["source"] == source]
        return results[-limit:]

    def tail(self, n: int = 20) -> list[dict]:
        """Return the last n log entries."""
        return list(self.entries)[-n:]

    def get_stats(self) -> dict:
        """Return logger statistics."""
        return {
            "total_entries": len(self.entries),
            "metrics": dict(self._metrics),
        }
