"""
ProcessManager: Manages virtual OS processes including spawning, killing,
and listing with PID assignment and resource tracking.
"""
import logging
import time

logger = logging.getLogger(__name__)

_STATES = ("running", "sleeping", "stopped", "zombie")


class ProcessManager:
    """Manages virtual processes within VAI-OS."""

    def __init__(self):
        self._next_pid: int = 1
        self.processes: dict[int, dict] = {}
        self._metrics: dict = {
            "total_spawned": 0,
            "total_killed": 0,
        }
        logger.info("ProcessManager initialized")

    @property
    def next_pid(self) -> int:
        """Return the next PID that will be assigned."""
        return self._next_pid

    def spawn(self, name: str, mem_mb: float = 16.0) -> int:
        """
        Spawn a new virtual process.

        Returns the assigned PID.
        """
        pid = self._next_pid
        self._next_pid += 1
        self.processes[pid] = {
            "pid": pid,
            "name": name,
            "state": "running",
            "mem_mb": mem_mb,
            "started_at": time.time(),
            "cpu_cycles": 0,
        }
        self._metrics["total_spawned"] += 1
        logger.info("Process spawned: pid=%d name=%s mem_mb=%.1f", pid, name, mem_mb)
        return pid

    def kill(self, pid: int) -> bool:
        """
        Kill the process with the given PID.

        Returns True if the process existed, False otherwise.
        """
        if pid not in self.processes:
            logger.warning("kill: PID %d not found", pid)
            return False
        proc = self.processes.pop(pid)
        self._metrics["total_killed"] += 1
        logger.info("Process killed: pid=%d name=%s", pid, proc["name"])
        return True

    def list_procs(self) -> list[dict]:
        """Return a list of all current process snapshots."""
        return list(self.processes.values())

    def get_proc(self, pid: int) -> dict | None:
        """Return the process dict for a given PID, or None."""
        return self.processes.get(pid)

    def set_state(self, pid: int, state: str) -> bool:
        """Update the state of a process."""
        if pid not in self.processes or state not in _STATES:
            return False
        self.processes[pid]["state"] = state
        logger.debug("Process %d state -> %s", pid, state)
        return True

    def get_stats(self) -> dict:
        """Return process manager statistics."""
        states: dict[str, int] = {}
        for proc in self.processes.values():
            states[proc["state"]] = states.get(proc["state"], 0) + 1
        return {
            "total_processes": len(self.processes),
            "states": states,
            "next_pid": self._next_pid,
            "metrics": dict(self._metrics),
        }
