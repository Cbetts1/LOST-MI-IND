"""
SyscallDispatcher: Provides a registry-based system call dispatch mechanism
for the VAI-OS kernel, allowing subsystems to expose callable interfaces.
"""
import logging

logger = logging.getLogger(__name__)


class SyscallDispatcher:
    """Registry and dispatcher for VAI-OS system calls."""

    def __init__(self):
        self.handlers: dict[str, callable] = {}
        self._metrics: dict = {
            "dispatch_calls": 0,
            "dispatch_errors": 0,
            "registrations": 0,
        }
        logger.info("SyscallDispatcher initialized")

    def register_handler(self, name: str, fn: callable) -> None:
        """Register a syscall handler under the given name."""
        self.handlers[name] = fn
        self._metrics["registrations"] += 1
        logger.debug("Syscall registered: %s -> %s", name, fn.__qualname__)

    def dispatch(self, name: str, *args, **kwargs):
        """
        Dispatch a syscall by name with the provided arguments.

        Returns the handler's return value.
        Raises KeyError if the syscall is not registered.
        """
        self._metrics["dispatch_calls"] += 1
        if name not in self.handlers:
            self._metrics["dispatch_errors"] += 1
            logger.error("Syscall not found: %s", name)
            raise KeyError(f"Unknown syscall: {name!r}")
        try:
            result = self.handlers[name](*args, **kwargs)
            logger.debug("Syscall dispatched: %s", name)
            return result
        except Exception as exc:
            self._metrics["dispatch_errors"] += 1
            logger.error("Syscall %s raised: %s", name, exc)
            raise

    def list_syscalls(self) -> list[str]:
        """Return a sorted list of registered syscall names."""
        return sorted(self.handlers.keys())

    def get_stats(self) -> dict:
        """Return syscall dispatcher statistics."""
        return {
            "registered_syscalls": len(self.handlers),
            "metrics": dict(self._metrics),
        }
