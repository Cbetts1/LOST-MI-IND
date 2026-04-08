"""
VAIOSKernel: The central kernel for VAI-OS. Manages subsystem registration,
ordered boot/shutdown lifecycle, and system-wide coordination.
"""
import logging
import time

logger = logging.getLogger(__name__)

VERSION = "0.1.0"


class VAIOSKernel:
    """Core VAI-OS kernel managing subsystem lifecycle."""

    version: str = VERSION

    def __init__(self):
        self.subsystems: dict = {}
        self._boot_time: float | None = None
        self._shutdown_time: float | None = None
        self._booted: bool = False
        self._metrics: dict = {
            "subsystems_registered": 0,
            "boot_duration_ms": 0.0,
        }
        logger.info("VAIOSKernel v%s created", self.version)

    def register_subsystem(self, name: str, obj: object) -> None:
        """Register a named subsystem with the kernel."""
        self.subsystems[name] = obj
        self._metrics["subsystems_registered"] += 1
        logger.debug("Subsystem registered: %s (%s)", name, type(obj).__name__)

    def get_subsystem(self, name: str):
        """Retrieve a registered subsystem by name."""
        sub = self.subsystems.get(name)
        if sub is None:
            logger.warning("Subsystem not found: %s", name)
        return sub

    def boot(self) -> None:
        """
        Boot the kernel: record boot time and mark as booted.

        Individual subsystem initialization is performed externally
        (by the Bootloader / main.py) before calling boot().
        """
        if self._booted:
            logger.warning("Kernel already booted, ignoring boot() call")
            return
        self._boot_time = time.time()
        self._booted = True
        logger.info(
            "VAIOSKernel booted with %d subsystems", len(self.subsystems)
        )

    def shutdown(self) -> None:
        """Gracefully shut down all registered subsystems."""
        logger.info("VAIOSKernel initiating shutdown...")
        self._shutdown_time = time.time()
        self._booted = False
        for name in reversed(list(self.subsystems.keys())):
            sub = self.subsystems[name]
            if hasattr(sub, "shutdown"):
                try:
                    sub.shutdown()
                    logger.debug("Subsystem %s shut down", name)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("Error shutting down subsystem %s: %s", name, exc)
        logger.info("VAIOSKernel shutdown complete")

    def emit_boot_complete(self) -> None:
        """Print the canonical boot-complete messages."""
        uptime_s = 0.0
        if self._boot_time:
            uptime_s = time.time() - self._boot_time
        self._metrics["boot_duration_ms"] = round(uptime_s * 1000, 2)
        print("[VAI-OS] Boot Complete")
        print("[VAI-OS] System Ready")
        logger.info("Boot complete, uptime so far: %.2fs", uptime_s)

    @property
    def is_booted(self) -> bool:
        """Return True if the kernel has completed booting."""
        return self._booted

    def get_stats(self) -> dict:
        """Return kernel runtime statistics."""
        uptime = 0.0
        if self._boot_time:
            uptime = time.time() - self._boot_time
        return {
            "version": self.version,
            "booted": self._booted,
            "uptime_s": round(uptime, 2),
            "subsystem_count": len(self.subsystems),
            "subsystem_names": list(self.subsystems.keys()),
            "metrics": dict(self._metrics),
        }
