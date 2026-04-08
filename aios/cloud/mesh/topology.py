"""
MeshTopology: Models the VAI-OS virtual mesh network topology with nodes,
edges, and Dijkstra shortest-path computation (pure Python, no external libs).
"""
import logging
import heapq

logger = logging.getLogger(__name__)


class MeshTopology:
    """Graph-based mesh network topology with shortest-path support."""

    def __init__(self):
        self.nodes: dict[str, dict] = {}   # node_id -> {type, ip, status, ...}
        self.edges: list[dict] = []         # [{src, dst, cost, status}]
        self._metrics: dict = {
            "nodes_added": 0,
            "nodes_removed": 0,
            "edges_added": 0,
            "edges_removed": 0,
            "path_queries": 0,
        }
        logger.info("MeshTopology initialized")

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(self, node_id: str, **attrs) -> None:
        """Add or update a topology node."""
        self.nodes[node_id] = {"node_id": node_id, **attrs}
        self._metrics["nodes_added"] += 1
        logger.debug("MeshTopology.add_node: %s", node_id)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges. Returns True if existed."""
        if node_id not in self.nodes:
            return False
        del self.nodes[node_id]
        self.edges = [
            e for e in self.edges if e["src"] != node_id and e["dst"] != node_id
        ]
        self._metrics["nodes_removed"] += 1
        logger.debug("MeshTopology.remove_node: %s", node_id)
        return True

    # ------------------------------------------------------------------
    # Edge management
    # ------------------------------------------------------------------

    def add_edge(self, src: str, dst: str, cost: int = 1, status: str = "up") -> None:
        """Add a directed edge between src and dst."""
        # Remove existing edge in same direction first
        self.edges = [e for e in self.edges if not (e["src"] == src and e["dst"] == dst)]
        self.edges.append({"src": src, "dst": dst, "cost": cost, "status": status})
        self._metrics["edges_added"] += 1
        logger.debug("MeshTopology.add_edge: %s -> %s cost=%d", src, dst, cost)

    def remove_edge(self, src: str, dst: str) -> bool:
        """Remove a directed edge. Returns True if it existed."""
        before = len(self.edges)
        self.edges = [e for e in self.edges if not (e["src"] == src and e["dst"] == dst)]
        removed = len(self.edges) < before
        if removed:
            self._metrics["edges_removed"] += 1
        return removed

    # ------------------------------------------------------------------
    # Pathfinding
    # ------------------------------------------------------------------

    def get_adjacency(self) -> dict[str, list]:
        """Return adjacency list: {node_id -> [(neighbor, cost)]}."""
        adj: dict[str, list] = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge.get("status", "up") == "up":
                src, dst, cost = edge["src"], edge["dst"], edge["cost"]
                if src in adj:
                    adj[src].append((dst, cost))
        return adj

    def shortest_path(self, src: str, dst: str) -> list[str]:
        """
        Compute the shortest path from src to dst using Dijkstra's algorithm.

        Returns an ordered list of node IDs forming the path,
        or an empty list if no path exists.
        """
        self._metrics["path_queries"] += 1
        if src not in self.nodes or dst not in self.nodes:
            logger.warning("shortest_path: unknown node(s) %s -> %s", src, dst)
            return []

        adj = self.get_adjacency()
        dist: dict[str, float] = {n: float("inf") for n in self.nodes}
        prev: dict[str, str | None] = {n: None for n in self.nodes}
        dist[src] = 0
        # Min-heap: (cost, node)
        heap = [(0, src)]

        while heap:
            cost, node = heapq.heappop(heap)
            if cost > dist[node]:
                continue
            if node == dst:
                break
            for neighbor, edge_cost in adj.get(node, []):
                new_cost = dist[node] + edge_cost
                if new_cost < dist[neighbor]:
                    dist[neighbor] = new_cost
                    prev[neighbor] = node
                    heapq.heappush(heap, (new_cost, neighbor))

        # Reconstruct path
        if dist[dst] == float("inf"):
            logger.debug("shortest_path: no path from %s to %s", src, dst)
            return []

        path: list[str] = []
        current: str | None = dst
        while current is not None:
            path.append(current)
            current = prev[current]
        path.reverse()
        logger.debug("shortest_path: %s -> %s = %s", src, dst, path)
        return path

    def get_stats(self) -> dict:
        """Return topology statistics."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "metrics": dict(self._metrics),
        }
