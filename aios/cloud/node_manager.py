"""
CloudNodeManager: Manages the lifecycle of virtual cloud nodes including
creation, destruction, and querying with optional type filtering.
"""
import logging

from .node import CloudNode

logger = logging.getLogger(__name__)


class CloudNodeManager:
    """Manager for virtual cloud node lifecycle."""

    def __init__(self):
        self.nodes: dict[str, CloudNode] = {}
        self._metrics: dict = {
            "created": 0,
            "destroyed": 0,
        }
        logger.info("CloudNodeManager initialized")

    def create_node(
        self,
        node_type: str = "compute",
        cpu_cores: int = 2,
        ram_mb: int = 512,
        **kwargs,
    ) -> CloudNode:
        """
        Create and register a new cloud node.

        Returns the created CloudNode instance.
        """
        node = CloudNode(node_type=node_type, cpu_cores=cpu_cores, ram_mb=ram_mb)
        self.nodes[node.node_id] = node
        self._metrics["created"] += 1
        logger.info("Node created: id=%s type=%s", node.node_id, node_type)
        return node

    def destroy_node(self, node_id: str) -> bool:
        """
        Stop and remove a node by its ID.

        Returns True if the node existed and was destroyed.
        """
        if node_id not in self.nodes:
            logger.warning("destroy_node: node not found: %s", node_id)
            return False
        node = self.nodes.pop(node_id)
        node.stop()
        self._metrics["destroyed"] += 1
        logger.info("Node destroyed: id=%s", node_id)
        return True

    def list_nodes(self, filter_type: str | None = None) -> list[CloudNode]:
        """
        List all nodes, optionally filtered by node_type.

        Returns a list of CloudNode instances.
        """
        nodes = list(self.nodes.values())
        if filter_type:
            nodes = [n for n in nodes if n.node_type == filter_type]
        return nodes

    def get_node(self, node_id: str) -> CloudNode | None:
        """Return the node with the given ID, or None."""
        return self.nodes.get(node_id)

    def get_stats(self) -> dict:
        """Return node manager statistics."""
        return {
            "total_nodes": len(self.nodes),
            "by_type": {
                t: sum(1 for n in self.nodes.values() if n.node_type == t)
                for t in {n.node_type for n in self.nodes.values()}
            },
            "metrics": dict(self._metrics),
        }
