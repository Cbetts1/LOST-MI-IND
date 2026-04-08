"""
hooks.py — Introspection, Logging, and Metrics Hooks for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - HardwareHooks is a singleton registry of hook callbacks.
  - Three hook categories: INTROSPECT (state inspection), LOG (event logging), METRICS (performance data).
  - Any component can register a hook with hooks.register(category, name, fn).
  - Any component can fire hooks with hooks.fire(event, payload).
  - All hooks are non-blocking; exceptions inside a hook are swallowed and logged to stderr.

Integration Points:
  - Used by every virtual hardware module (cpu, memory, storage, etc.)
  - Consumed by: AI Control Plane (introspect), System Services (logging), Cloud Layer (metrics telemetry)
"""

import logging
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List

logger = logging.getLogger("vaios.virt.hooks")

INTROSPECT = "introspect"
LOG = "log"
METRICS = "metrics"

CATEGORIES = (INTROSPECT, LOG, METRICS)


class HardwareHooks:
    """
    Central hook registry for the Virtual Hardware Layer.

    Supports three hook categories:
      - INTROSPECT: state snapshot callbacks (for debugging / AI observation)
      - LOG: event log callbacks (structured log entries)
      - METRICS: numeric metrics callbacks (for telemetry / dashboards)
    """

    def __init__(self) -> None:
        self._hooks: Dict[str, Dict[str, List[Callable]]] = {
            cat: defaultdict(list) for cat in CATEGORIES
        }
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 1000
        logger.info("[HOOK] HardwareHooks registry initialized")

    def register(self, category: str, event: str, fn: Callable) -> None:
        """Register a callback for a specific category and event name."""
        if category not in CATEGORIES:
            raise ValueError(f"Unknown hook category: {category!r}. Must be one of {CATEGORIES}")
        self._hooks[category][event].append(fn)
        logger.debug("[HOOK] Registered %s hook for event=%r", category, event)

    def unregister(self, category: str, event: str, fn: Callable) -> None:
        """Unregister a previously registered callback."""
        try:
            self._hooks[category][event].remove(fn)
        except ValueError:
            pass

    def fire(self, event: str, payload: Any = None, categories: tuple = CATEGORIES) -> None:
        """
        Fire all registered hooks for the given event across the specified categories.

        Args:
            event: Event name string (e.g. 'cpu.tick', 'memory.alloc').
            payload: Arbitrary data passed to each hook callback.
            categories: Which hook categories to fire (default: all).
        """
        entry = {
            "ts": time.monotonic(),
            "event": event,
            "payload": payload,
        }
        self._event_history.append(entry)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        for cat in categories:
            for fn in list(self._hooks[cat].get(event, [])):
                try:
                    fn(event, payload)
                except Exception as exc:  # pylint: disable=broad-except
                    import sys
                    print(f"[HOOK ERROR] {cat}/{event}: {exc}", file=sys.stderr)

    def list_hooks(self) -> Dict[str, Dict[str, int]]:
        """Return a summary of registered hook counts."""
        return {
            cat: {evt: len(fns) for evt, fns in evts.items()}
            for cat, evts in self._hooks.items()
        }

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent hook events from the in-memory history."""
        return self._event_history[-limit:]

    def __repr__(self) -> str:
        total = sum(len(fns) for evts in self._hooks.values() for fns in evts.values())
        return f"<HardwareHooks registered_hooks={total}>"


# Module-level singleton
_hooks_instance: HardwareHooks = None  # type: ignore


def get_hooks() -> HardwareHooks:
    """Return the global HardwareHooks singleton, creating it if needed."""
    global _hooks_instance
    if _hooks_instance is None:
        _hooks_instance = HardwareHooks()
    return _hooks_instance


def _builtin_log_hook(event: str, payload: Any) -> None:
    """Built-in log hook — writes all hardware events to the vaios logger."""
    logger.debug("[HW-EVENT] event=%r payload=%r", event, payload)


def install_builtin_hooks(hooks: HardwareHooks) -> None:
    """Install the default built-in introspection/logging/metrics hooks."""
    for event_prefix in (
        "cpu.", "memory.", "storage.", "nic.", "display.",
        "io.", "firmware.", "sensors.", "radio.", "bus.",
    ):
        hooks.register(LOG, event_prefix + "*", _builtin_log_hook)
    hooks.register(LOG, "*", _builtin_log_hook)
    logger.info("[HOOK] Built-in logging hooks installed")
