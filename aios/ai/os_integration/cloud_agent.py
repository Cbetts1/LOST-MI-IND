"""
CloudAgent: AI agent that monitors the VAI-OS virtual cloud cluster,
recommends scaling actions, and applies them via the CloudScaler.
"""
import logging

logger = logging.getLogger(__name__)


class CloudAgent:
    """AI agent for virtual cloud cluster management."""

    def __init__(self, node_manager, scaler):
        self._node_manager = node_manager
        self._scaler = scaler
        self._active = False
        self._metrics: dict = {
            "analyze_calls": 0,
            "recommend_calls": 0,
            "apply_calls": 0,
        }
        logger.info("CloudAgent initialized")

    def start(self) -> None:
        """Activate the cloud agent."""
        self._active = True
        logger.info("CloudAgent started")

    def stop(self) -> None:
        """Deactivate the cloud agent."""
        self._active = False

    def analyze_cluster(self) -> dict:
        """
        Analyze the current state of the cloud cluster.

        Returns a dict with node counts, types, and health indicators.
        """
        self._metrics["analyze_calls"] += 1
        nodes = self._node_manager.list_nodes()
        running = [n for n in nodes if n.status == "running"]
        stopped = [n for n in nodes if n.status == "stopped"]
        types: dict[str, int] = {}
        for n in nodes:
            types[n.node_type] = types.get(n.node_type, 0) + 1

        analysis = {
            "total_nodes": len(nodes),
            "running": len(running),
            "stopped": len(stopped),
            "types": types,
            "healthy": len(running) >= 1,
        }
        logger.debug("CloudAgent.analyze_cluster: %s", analysis)
        return analysis

    def recommend_scaling(self) -> dict:
        """
        Recommend a scaling action based on cluster analysis.

        Returns a dict with keys: action, node_type, count, reason.
        """
        self._metrics["recommend_calls"] += 1
        analysis = self.analyze_cluster()
        rec: dict = {"action": "none", "node_type": "compute", "count": 0, "reason": ""}

        if analysis["total_nodes"] == 0:
            rec.update({"action": "scale_up", "count": 2, "reason": "No nodes present"})
        elif analysis["running"] < 1:
            rec.update({"action": "scale_up", "count": 1, "reason": "No running nodes"})
        elif analysis["running"] > 10:
            rec.update({"action": "scale_down", "count": 2, "reason": "Excess capacity"})
        else:
            rec["reason"] = "Cluster size optimal"

        logger.info("CloudAgent recommendation: %s", rec)
        return rec

    def apply_scaling(self, recommendation: dict) -> bool:
        """
        Apply a scaling recommendation via the CloudScaler.

        Returns True if the action was applied.
        """
        self._metrics["apply_calls"] += 1
        action = recommendation.get("action", "none")
        node_type = recommendation.get("node_type", "compute")
        count = recommendation.get("count", 1)

        if action == "scale_up":
            ids = self._scaler.scale_up(node_type, count)
            logger.info("CloudAgent scaled up: %s", ids)
            return bool(ids)
        if action == "scale_down":
            ids = self._scaler.scale_down(node_type, count)
            logger.info("CloudAgent scaled down: %s", ids)
            return bool(ids)
        logger.debug("CloudAgent: no scaling action required")
        return True
