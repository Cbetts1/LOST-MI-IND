"""
VirtualRouter: Simulates an IP routing table with route management and
packet forwarding for the VAI-OS virtual network stack.
"""
import logging

logger = logging.getLogger(__name__)


class VirtualRouter:
    """Simulates a virtual IP router with a routing table."""

    def __init__(self):
        self.table: list[dict] = []
        self._metrics: dict = {"forwards": 0, "no_route": 0, "route_adds": 0}
        # Default route
        self.add_route("0.0.0.0", "0.0.0.0", "10.0.0.254", "eth0")
        logger.info("VirtualRouter initialized")

    def add_route(self, network: str, netmask: str, gateway: str, iface: str) -> None:
        """Add a route to the routing table."""
        entry = {
            "network": network,
            "netmask": netmask,
            "gateway": gateway,
            "iface": iface,
        }
        self.table.append(entry)
        self._metrics["route_adds"] += 1
        logger.debug("Route added: %s/%s via %s dev %s", network, netmask, gateway, iface)

    def remove_route(self, network: str) -> bool:
        """Remove the first route matching the given network."""
        before = len(self.table)
        self.table = [r for r in self.table if r["network"] != network]
        removed = len(self.table) < before
        if removed:
            logger.debug("Route removed: network=%s", network)
        return removed

    def forward(self, packet: dict) -> str:
        """
        Look up the routing table and return the next-hop gateway.

        Returns the gateway IP string, or '0.0.0.0' if no route found.
        """
        dst = packet.get("dst", "")
        self._metrics["forwards"] += 1
        for route in reversed(self.table):
            if route["network"] == "0.0.0.0":
                logger.debug("Packet forwarded via default route gw=%s", route["gateway"])
                return route["gateway"]
            if dst.startswith(route["network"].rstrip("0").rstrip(".")):
                logger.debug("Packet forwarded: dst=%s gw=%s", dst, route["gateway"])
                return route["gateway"]
        self._metrics["no_route"] += 1
        logger.warning("No route to host: %s", dst)
        return "0.0.0.0"

    def get_table(self) -> list[dict]:
        """Return a copy of the routing table."""
        return list(self.table)
