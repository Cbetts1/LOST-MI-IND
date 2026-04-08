"""
RoundRobinScheduler: A simple round-robin task scheduler for VAI-OS that
executes tasks based on their configured interval in milliseconds.
"""
import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class RoundRobinScheduler:
    """Round-robin scheduler that executes tasks when their interval elapses."""

    def __init__(self):
        self.tasks: deque[dict] = deque()
        self._task_map: dict[str, dict] = {}
        self._metrics: dict = {
            "ticks": 0,
            "tasks_run": 0,
            "errors": 0,
        }
        logger.info("RoundRobinScheduler initialized")

    def add_task(self, name: str, fn: callable, interval_ms: int = 1000) -> None:
        """
        Add a named task to the scheduler.

        interval_ms controls minimum time between runs (in milliseconds).
        """
        task = {
            "id": len(self._task_map),
            "name": name,
            "fn": fn,
            "interval_ms": interval_ms,
            "last_run": 0.0,
            "run_count": 0,
        }
        self.tasks.append(task)
        self._task_map[name] = task
        logger.debug("Task added: %s interval=%dms", name, interval_ms)

    def remove_task(self, name: str) -> bool:
        """Remove a task by name. Returns True if removed."""
        if name not in self._task_map:
            return False
        task = self._task_map.pop(name)
        try:
            self.tasks.remove(task)
        except ValueError:
            pass
        logger.debug("Task removed: %s", name)
        return True

    def tick(self) -> int:
        """
        Run all tasks whose interval has elapsed.

        Returns the number of tasks actually executed this tick.
        """
        self._metrics["ticks"] += 1
        now_ms = time.time() * 1000
        ran = 0
        for task in list(self.tasks):
            elapsed = now_ms - task["last_run"]
            if elapsed >= task["interval_ms"]:
                try:
                    task["fn"]()
                    task["last_run"] = now_ms
                    task["run_count"] += 1
                    ran += 1
                    self._metrics["tasks_run"] += 1
                except Exception as exc:  # pylint: disable=broad-except
                    self._metrics["errors"] += 1
                    logger.error("Scheduler task %s raised: %s", task["name"], exc)
        logger.debug("Scheduler tick: ran %d tasks", ran)
        return ran

    def list_tasks(self) -> list[dict]:
        """Return a summary list of all scheduled tasks."""
        return [
            {
                "name": t["name"],
                "interval_ms": t["interval_ms"],
                "run_count": t["run_count"],
                "last_run": t["last_run"],
            }
            for t in self.tasks
        ]

    def get_stats(self) -> dict:
        """Return scheduler statistics."""
        return {
            "task_count": len(self.tasks),
            "metrics": dict(self._metrics),
        }
