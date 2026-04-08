"""
ComputeService: Manages virtual compute tasks on cloud nodes including
task submission, status tracking, and cancellation.
"""
import logging
import time
import uuid

logger = logging.getLogger(__name__)

_TASK_STATES = ("pending", "running", "completed", "failed", "cancelled")


class ComputeService:
    """Virtual compute task execution service."""

    def __init__(self, node_manager):
        self._nm = node_manager
        self._tasks: dict[str, dict] = {}
        self._metrics: dict = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
        logger.info("ComputeService initialized")

    def run_task(self, task_def: dict) -> str:
        """
        Submit a compute task for execution.

        Returns a unique task_id string.
        """
        task_id = str(uuid.uuid4())[:8]
        nodes = self._nm.list_nodes(filter_type="compute")
        running = [n for n in nodes if n.status == "running"]

        task = {
            "task_id": task_id,
            "name": task_def.get("name", "unnamed"),
            "state": "pending",
            "submitted_at": time.time(),
            "completed_at": None,
            "node_id": running[0].node_id if running else None,
            "result": None,
        }
        self._tasks[task_id] = task
        self._metrics["submitted"] += 1

        # Simulate immediate execution for virtual tasks
        if running:
            task["state"] = "running"
            task["state"] = "completed"
            task["completed_at"] = time.time()
            task["result"] = {"output": f"Task {task_id} completed", "exit_code": 0}
            self._metrics["completed"] += 1
        else:
            task["state"] = "failed"
            task["result"] = {"error": "No running compute nodes"}
            self._metrics["failed"] += 1

        logger.info("ComputeService.run_task: id=%s state=%s", task_id, task["state"])
        return task_id

    def get_task_status(self, task_id: str) -> dict:
        """Return the status dict for a task, or empty dict if not found."""
        return dict(self._tasks.get(task_id, {}))

    def list_tasks(self) -> list[dict]:
        """Return a list of all task status dicts."""
        return list(self._tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.

        Returns True if the task was found and cancelled.
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task["state"] in ("completed", "failed", "cancelled"):
            return False
        task["state"] = "cancelled"
        self._metrics["cancelled"] += 1
        logger.info("ComputeService.cancel_task: id=%s", task_id)
        return True

    def get_stats(self) -> dict:
        """Return compute service statistics."""
        return {
            "total_tasks": len(self._tasks),
            "metrics": dict(self._metrics),
        }
