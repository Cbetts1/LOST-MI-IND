"""
Sandbox: Provides isolated execution environments for VAI-OS processes
with configurable resource limits and execution tracking.
"""
import logging
import time
import uuid

logger = logging.getLogger(__name__)


class Sandbox:
    """Lightweight process sandboxing with resource limit enforcement."""

    def __init__(self, permission_manager):
        self._perm = permission_manager
        self.active_sandboxes: dict[str, dict] = {}
        self._metrics: dict = {
            "created": 0,
            "destroyed": 0,
            "executions": 0,
            "limit_violations": 0,
        }
        logger.info("Sandbox initialized")

    def create_sandbox(self, name: str, limits: dict) -> str:
        """
        Create a new sandbox with the given resource limits.

        Returns a unique sandbox_id.
        """
        sandbox_id = str(uuid.uuid4())[:8]
        self.active_sandboxes[sandbox_id] = {
            "sandbox_id": sandbox_id,
            "name": name,
            "limits": dict(limits),
            "created_at": time.time(),
            "exec_count": 0,
            "cpu_used": 0.0,
            "mem_used": 0.0,
        }
        self._metrics["created"] += 1
        logger.info("Sandbox created: id=%s name=%s limits=%s", sandbox_id, name, limits)
        return sandbox_id

    def run_in_sandbox(self, sandbox_id: str, fn, *args):
        """
        Execute a callable within the named sandbox.

        Enforces execution count limit if 'max_exec' is set.
        Returns the callable's return value.
        """
        sandbox = self.active_sandboxes.get(sandbox_id)
        if sandbox is None:
            raise KeyError(f"Sandbox {sandbox_id!r} not found")

        limits = sandbox["limits"]
        max_exec = limits.get("max_exec", float("inf"))
        if sandbox["exec_count"] >= max_exec:
            self._metrics["limit_violations"] += 1
            raise PermissionError(
                f"Sandbox {sandbox_id} exceeded max_exec={max_exec}"
            )

        self._metrics["executions"] += 1
        sandbox["exec_count"] += 1
        t0 = time.time()
        try:
            result = fn(*args)
            logger.debug("Sandbox.run_in_sandbox: id=%s fn=%s OK", sandbox_id, getattr(fn, "__name__", fn))
            return result
        except Exception as exc:
            logger.error("Sandbox.run_in_sandbox: id=%s error=%s", sandbox_id, exc)
            raise
        finally:
            elapsed_ms = (time.time() - t0) * 1000
            sandbox["cpu_used"] += elapsed_ms

    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Remove a sandbox. Returns True if it existed."""
        if sandbox_id in self.active_sandboxes:
            del self.active_sandboxes[sandbox_id]
            self._metrics["destroyed"] += 1
            logger.info("Sandbox destroyed: id=%s", sandbox_id)
            return True
        return False

    def get_stats(self, sandbox_id: str) -> dict:
        """Return statistics for a specific sandbox."""
        sb = self.active_sandboxes.get(sandbox_id, {})
        return dict(sb)
