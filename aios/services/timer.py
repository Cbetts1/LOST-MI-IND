"""
VAI-OS Timer Service
Schedules recurring and one-shot callbacks, fired on tick().
Architecture: pure stdlib, integrates with EventBus via tick calls.
"""
import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class TimerService:
    """Manages named timers fired by calling tick()."""

    def __init__(self):
        self.timers: dict = {}
        self._fired_log: deque = deque(maxlen=1000)

    def schedule(self, name: str, fn, interval_seconds: float, one_shot: bool = False):
        """Register a timer that calls fn every interval_seconds."""
        self.timers[name] = {
            "fn": fn,
            "interval": interval_seconds,
            "next_run": time.monotonic() + interval_seconds,
            "active": True,
            "one_shot": one_shot,
            "fire_count": 0,
        }
        logger.debug("Scheduled timer '%s' every %.2fs", name, interval_seconds)

    def cancel(self, name: str):
        """Cancel a timer by name."""
        if name in self.timers:
            self.timers[name]["active"] = False
            logger.debug("Cancelled timer '%s'", name)

    def tick(self) -> int:
        """Fire all due timers. Returns count of fired timers."""
        now = time.monotonic()
        fired = 0
        to_remove = []
        for name, t in self.timers.items():
            if not t["active"]:
                continue
            if now >= t["next_run"]:
                try:
                    t["fn"]()
                    t["fire_count"] += 1
                    self._fired_log.append({"name": name, "at": now})
                    fired += 1
                except Exception as exc:
                    logger.error("Timer '%s' raised: %s", name, exc)
                if t["one_shot"]:
                    to_remove.append(name)
                else:
                    t["next_run"] = now + t["interval"]
        for name in to_remove:
            del self.timers[name]
        return fired

    def list_timers(self) -> list:
        return [
            {
                "name": n,
                "interval": t["interval"],
                "active": t["active"],
                "fire_count": t["fire_count"],
            }
            for n, t in self.timers.items()
        ]
