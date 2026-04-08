"""
DaemonManager: Registers and manages long-running background daemons
in the VAI-OS system services layer.
"""
import logging
import time

logger = logging.getLogger(__name__)


class DaemonManager:
    """Manages background daemon registration and lifecycle."""

    def __init__(self):
        self.daemons: dict[str, dict] = {}
        self._metrics: dict = {
            "registered": 0,
            "started": 0,
            "stopped": 0,
        }
        logger.info("DaemonManager initialized")

    def register(self, name: str, fn, description: str = "") -> None:
        """Register a daemon function under the given name."""
        self.daemons[name] = {
            "name": name,
            "fn": fn,
            "description": description,
            "status": "registered",
            "started_at": None,
        }
        self._metrics["registered"] += 1
        logger.info("Daemon registered: %s", name)

    def start(self, name: str) -> bool:
        """
        Mark a daemon as running and invoke its function.

        Returns True if successfully started.
        """
        daemon = self.daemons.get(name)
        if not daemon:
            logger.warning("Daemon not found: %s", name)
            return False
        if daemon["status"] == "running":
            logger.warning("Daemon already running: %s", name)
            return False
        try:
            daemon["fn"]()
        except Exception as exc:
            logger.error("Daemon %s raised on start: %s", name, exc)
            daemon["status"] = "error"
            return False
        daemon["status"] = "running"
        daemon["started_at"] = time.time()
        self._metrics["started"] += 1
        logger.info("Daemon started: %s", name)
        return True

    def stop(self, name: str) -> bool:
        """Mark a daemon as stopped. Returns True if it was running."""
        daemon = self.daemons.get(name)
        if not daemon:
            return False
        if daemon["status"] not in ("running", "error"):
            return False
        daemon["status"] = "stopped"
        daemon["started_at"] = None
        self._metrics["stopped"] += 1
        logger.info("Daemon stopped: %s", name)
        return True

    def status(self, name: str) -> str:
        """Return the status string for a daemon, or 'unknown'."""
        return self.daemons.get(name, {}).get("status", "unknown")

    def list_daemons(self) -> list[dict]:
        """Return a list of daemon metadata dicts."""
        return [
            {
                "name": d["name"],
                "description": d["description"],
                "status": d["status"],
                "started_at": d["started_at"],
            }
            for d in self.daemons.values()
        ]

    def get_stats(self) -> dict:
        """Return daemon manager statistics."""
        return {
            "total_daemons": len(self.daemons),
            "metrics": dict(self._metrics),
        }
