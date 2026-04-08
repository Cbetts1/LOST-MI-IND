"""
BootBrain: AI agent that orchestrates the full VAI-OS boot sequence,
manages boot phases, and handles recovery from boot errors.
"""
import logging
import time

logger = logging.getLogger(__name__)


class BootBrain:
    """AI orchestrator for the VAI-OS boot sequence."""

    def __init__(self, kernel):
        self._kernel = kernel
        self.phases: list[tuple] = []  # (name, fn)
        self._boot_log: list[str] = []
        self._metrics: dict = {
            "phases_run": 0,
            "phases_failed": 0,
            "recoveries": 0,
        }
        logger.info("BootBrain initialized")

    def add_phase(self, name: str, fn) -> None:
        """Add a named boot phase function."""
        self.phases.append((name, fn))
        logger.debug("Boot phase added: %s", name)

    def run_boot_sequence(self) -> bool:
        """
        Execute all registered boot phases in order.

        Returns True if all phases completed successfully.
        """
        logger.info("BootBrain: starting boot sequence (%d phases)", len(self.phases))
        for name, fn in self.phases:
            t0 = time.time()
            try:
                fn()
                elapsed = round((time.time() - t0) * 1000, 2)
                self._metrics["phases_run"] += 1
                msg = f"[OK] {name} ({elapsed}ms)"
                self._boot_log.append(msg)
                logger.info("Boot phase OK: %s in %sms", name, elapsed)
            except Exception as exc:
                elapsed = round((time.time() - t0) * 1000, 2)
                self._metrics["phases_failed"] += 1
                msg = f"[FAIL] {name}: {exc} ({elapsed}ms)"
                self._boot_log.append(msg)
                logger.error("Boot phase FAIL: %s -> %s", name, exc)
                recovered = self.handle_boot_error(name, exc)
                if not recovered:
                    logger.critical("Boot aborted at phase: %s", name)
                    return False
        logger.info("BootBrain: boot sequence complete")
        return True

    def handle_boot_error(self, phase: str, error: Exception) -> bool:
        """
        Attempt recovery from a boot phase error.

        Returns True if the system can continue booting.
        For most errors, log and continue (non-fatal recovery).
        """
        self._metrics["recoveries"] += 1
        logger.warning(
            "BootBrain recovering from phase=%s error=%s", phase, error
        )
        self._boot_log.append(f"[RECOVERY] phase={phase} error={error}")
        # Non-critical phases: continue booting
        non_critical = {"cloud", "ai_inference", "developer_tools", "wizard"}
        for keyword in non_critical:
            if keyword in phase.lower():
                logger.info("Phase '%s' is non-critical, continuing boot", phase)
                return True
        # For critical phases, return False to abort boot
        return False

    def get_boot_log(self) -> list[str]:
        """Return the accumulated boot phase log."""
        return list(self._boot_log)

    def get_stats(self) -> dict:
        """Return boot brain statistics."""
        return {
            "phases_total": len(self.phases),
            "metrics": dict(self._metrics),
        }
