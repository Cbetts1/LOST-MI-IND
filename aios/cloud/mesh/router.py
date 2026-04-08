"""
MeshRouter: Manages routing table for the VAI-OS virtual mesh network,
supporting route addition, removal, and packet annotation with next hops.
"""
import logging

logger = logging.getLogger(__name__)


class MeshRouter:
    """Virtual mesh network routing table manager."""

    def __init__(self):
        self.routes: dict[str, dict] = {}  # dest -> {next_hop, cost, iface}
        self._metrics: dict = {
            "routes_added": 0,
            "routes_removed": 0,
            "packets_routed": 0,
            "route_misses": 0,
        }
        logger.info("MeshRouter initialized")

    def add_route(
        self, dest: str, next_hop: str, cost: int = 1, iface: str = "mesh0"
    ) -> None:
        """Add or update a mesh route."""
        self.routes[dest] = {"next_hop": next_hop, "cost": cost, "iface": iface}
        self._metrics["routes_added"] += 1
        logger.debug("MeshRouter.add_route: %s -> %s cost=%d", dest, next_hop, cost)

    def remove_route(self, dest: str) -> bool:
        """Remove a route. Returns True if it existed."""
        if dest in self.routes:
            del self.routes[dest]
            self._metrics["routes_removed"] += 1
            logger.debug("MeshRouter.remove_route: %s", dest)
            return True
        return False

    def route_packet(self, packet: dict) -> dict:
        """
        Annotate a packet dict with next_hop and iface from the routing table.

        Returns the (possibly modified) packet.
        """
        self._metrics["packets_routed"] += 1
        dst = packet.get("dst", "")
        if dst in self.routes:
            route = self.routes[dst]
            packet = dict(packet)
            packet["next_hop"] = route["next_hop"]
            packet["iface"] = route["iface"]
            logger.debug("MeshRouter.route_packet: dst=%s next_hop=%s", dst, route["next_hop"])
        else:
            self._metrics["route_misses"] += 1
            packet = dict(packet)
            packet["next_hop"] = None
            logger.warning("MeshRouter: no route for dst=%s", dst)
        return packet

    def get_routing_table(self) -> list[dict]:
        """Return the routing table as a list of dicts."""
        return [{"dest": d, **r} for d, r in self.routes.items()]

    def get_stats(self) -> dict:
        """Return router statistics."""
        return {
            "route_count": len(self.routes),
            "metrics": dict(self._metrics),
        }
