"""
AuditLog: Immutable structured audit event log for VAI-OS security
compliance, with query and export capabilities.
"""
import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class AuditLog:
    """Append-only structured audit log with query support."""

    def __init__(self, maxlen: int = 50_000):
        self.events: deque = deque(maxlen=maxlen)
        self._metrics: dict = {
            "total_logged": 0,
            "by_outcome": {"allowed": 0, "denied": 0},
        }
        logger.info("AuditLog initialized (maxlen=%d)", maxlen)

    def log_event(
        self,
        event_type: str,
        subject: str,
        resource: str,
        action: str,
        outcome: str,
        **meta,
    ) -> None:
        """
        Append an audit event.

        Standard fields: event_type, subject, resource, action, outcome.
        Additional metadata accepted as keyword arguments.
        """
        event = {
            "ts": time.time(),
            "event_type": event_type,
            "subject": subject,
            "resource": resource,
            "action": action,
            "outcome": outcome,
            **meta,
        }
        self.events.append(event)
        self._metrics["total_logged"] += 1
        self._metrics["by_outcome"][outcome] = (
            self._metrics["by_outcome"].get(outcome, 0) + 1
        )
        logger.debug(
            "Audit: [%s] %s %s on %s -> %s",
            event_type, subject, action, resource, outcome,
        )

    def query_events(
        self,
        event_type: str | None = None,
        subject: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Filter audit events by type and/or subject."""
        results = list(self.events)
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        if subject:
            results = [e for e in results if e["subject"] == subject]
        return results[-limit:]

    def tail(self, n: int = 20) -> list[dict]:
        """Return the last n audit events."""
        return list(self.events)[-n:]

    def export(self) -> list[dict]:
        """Export all audit events as a list of dicts."""
        return list(self.events)

    def get_stats(self) -> dict:
        """Return audit log statistics."""
        return {
            "total_events": len(self.events),
            "metrics": dict(self._metrics),
        }
