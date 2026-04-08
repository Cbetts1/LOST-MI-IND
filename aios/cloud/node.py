"""
CloudNode: Represents a single virtual cloud node with resource management,
health reporting, and lifecycle (start/stop) operations.
"""
import logging
import time
import uuid

logger = logging.getLogger(__name__)

_VALID_STATUSES = ("stopped", "running", "error", "provisioning")


class CloudNode:
    """A virtual cloud compute/storage/gateway node."""

    def __init__(
        self,
        node_id: str | None = None,
        node_type: str = "compute",
        cpu_cores: int = 2,
        ram_mb: int = 512,
    ):
        self.node_id: str = node_id or str(uuid.uuid4())[:8]
        self.node_type: str = node_type
        self.cpu_cores: int = cpu_cores
        self.ram_mb: int = ram_mb
        self.status: str = "stopped"
        self._started_at: float | None = None
        self._resources: dict = {}  # {res_type -> allocated_amount}
        self._metrics: dict = {
            "start_count": 0,
            "stop_count": 0,
            "allocation_failures": 0,
        }
        logger.info(
            "CloudNode created: id=%s type=%s cpu=%d ram=%dMB",
            self.node_id, node_type, cpu_cores, ram_mb,
        )

    def start(self) -> None:
        """Start this cloud node."""
        self.status = "running"
        self._started_at = time.time()
        self._metrics["start_count"] += 1
        logger.info("CloudNode started: %s", self.node_id)

    def stop(self) -> None:
        """Stop this cloud node."""
        self.status = "stopped"
        self._started_at = None
        self._resources.clear()
        self._metrics["stop_count"] += 1
        logger.info("CloudNode stopped: %s", self.node_id)

    def get_health(self) -> dict:
        """Return node health information."""
        uptime = (time.time() - self._started_at) if self._started_at else 0.0
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "status": self.status,
            "uptime_s": round(uptime, 2),
            "cpu_cores": self.cpu_cores,
            "ram_mb": self.ram_mb,
            "allocated_resources": dict(self._resources),
        }

    def allocate_resource(self, res_type: str, amount: float) -> bool:
        """
        Allocate a resource (cpu/ram/storage) on this node.

        Returns True if allocation succeeded.
        """
        if self.status != "running":
            logger.warning("Cannot allocate on stopped node %s", self.node_id)
            self._metrics["allocation_failures"] += 1
            return False

        current = self._resources.get(res_type, 0)
        limit = self.cpu_cores if res_type == "cpu" else self.ram_mb
        if current + amount > limit:
            self._metrics["allocation_failures"] += 1
            logger.warning(
                "Resource allocation failed: node=%s res=%s requested=%s available=%s",
                self.node_id, res_type, amount, limit - current,
            )
            return False
        self._resources[res_type] = current + amount
        logger.debug("Allocated %s=%s on node %s", res_type, amount, self.node_id)
        return True
