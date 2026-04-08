"""
CloudScaler: Manages dynamic scaling of cloud node pools based on
metrics and AI-driven optimization recommendations.
"""
import logging

logger = logging.getLogger(__name__)


class CloudScaler:
    """Scales cloud node pools up or down based on demand."""

    def __init__(self, node_manager, metrics):
        self._nm = node_manager
        self._metrics_svc = metrics
        self._scale_log: list[dict] = []
        self._metrics: dict = {
            "scale_up_calls": 0,
            "scale_down_calls": 0,
            "nodes_added": 0,
            "nodes_removed": 0,
        }
        logger.info("CloudScaler initialized")

    def scale_up(self, node_type: str = "compute", count: int = 1) -> list[str]:
        """
        Create and start 'count' new nodes of the given type.

        Returns a list of new node IDs.
        """
        self._metrics["scale_up_calls"] += 1
        new_ids: list[str] = []
        for _ in range(count):
            node = self._nm.create_node(node_type=node_type)
            node.start()
            new_ids.append(node.node_id)
            self._metrics["nodes_added"] += 1
        self._scale_log.append({"action": "up", "type": node_type, "count": count, "ids": new_ids})
        logger.info("Scaled up %d %s nodes: %s", count, node_type, new_ids)
        if self._metrics_svc:
            self._metrics_svc.increment("cloud.scale_up", count)
        return new_ids

    def scale_down(self, node_type: str = "compute", count: int = 1) -> list[str]:
        """
        Stop and remove 'count' nodes of the given type.

        Prefers to remove stopped nodes first. Returns removed IDs.
        """
        self._metrics["scale_down_calls"] += 1
        candidates = self._nm.list_nodes(filter_type=node_type)
        candidates.sort(key=lambda n: n.status == "running")  # stopped first
        removed_ids: list[str] = []
        for node in candidates[:count]:
            self._nm.destroy_node(node.node_id)
            removed_ids.append(node.node_id)
            self._metrics["nodes_removed"] += 1
        self._scale_log.append({"action": "down", "type": node_type, "count": count, "ids": removed_ids})
        logger.info("Scaled down %d %s nodes: %s", count, node_type, removed_ids)
        if self._metrics_svc:
            self._metrics_svc.increment("cloud.scale_down", count)
        return removed_ids

    def ai_optimize(self, metrics_snapshot: dict) -> dict:
        """
        Produce a scaling decision based on a metrics snapshot.

        Returns a dict with: action, node_type, count, reason.
        """
        cpu_pct = metrics_snapshot.get("cpu_usage_pct", 0)
        active_nodes = metrics_snapshot.get("active_nodes", 0)

        if cpu_pct > 80:
            return {"action": "scale_up", "node_type": "compute", "count": 2,
                    "reason": f"CPU high ({cpu_pct}%)"}
        if cpu_pct < 20 and active_nodes > 3:
            return {"action": "scale_down", "node_type": "compute", "count": 1,
                    "reason": f"CPU low ({cpu_pct}%), excess capacity"}
        return {"action": "none", "node_type": "compute", "count": 0,
                "reason": "Cluster balanced"}

    def get_cluster_stats(self) -> dict:
        """Return a summary of cluster state."""
        nodes = self._nm.list_nodes()
        running = [n for n in nodes if n.status == "running"]
        return {
            "total": len(nodes),
            "running": len(running),
            "stopped": len(nodes) - len(running),
            "scale_events": len(self._scale_log),
            "metrics": dict(self._metrics),
        }
