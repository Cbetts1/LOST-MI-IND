"""
VAI-OS Event Bus
Publish/subscribe event system for inter-subsystem communication.
Architecture: synchronous, in-process, zero external dependencies.
"""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    """Simple synchronous event bus."""

    def __init__(self):
        self.listeners: dict = defaultdict(list)
        self._history: list = []

    def on(self, event: str, callback):
        """Subscribe callback to event."""
        if callback not in self.listeners[event]:
            self.listeners[event].append(callback)
            logger.debug("Subscribed to '%s'", event)

    def off(self, event: str, callback):
        """Unsubscribe callback from event."""
        if callback in self.listeners[event]:
            self.listeners[event].remove(callback)

    def emit(self, event: str, data: dict = None):
        """Emit event to all subscribers."""
        data = data or {}
        self._history.append({"event": event, "data": data})
        for cb in list(self.listeners.get(event, [])):
            try:
                cb(data)
            except Exception as exc:
                logger.error("EventBus handler for '%s' raised: %s", event, exc)
        logger.debug("Emitted '%s' to %d listeners", event, len(self.listeners.get(event, [])))

    def list_events(self) -> list:
        return list(self.listeners.keys())

    def history(self, limit: int = 50) -> list:
        return self._history[-limit:]
