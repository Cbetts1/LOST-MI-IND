"""
PublicIPAbstraction: Simulates Network Address Translation (NAT) between
internal and external IP addresses for VAI-OS virtual networking.
"""
import logging

logger = logging.getLogger(__name__)


class PublicIPAbstraction:
    """Simulates a NAT gateway with inbound/outbound address translation."""

    def __init__(self, public_ip: str = "203.0.113.1"):
        self.public_ip = public_ip
        self.nat_table: dict = {}  # internal_ip -> external_ip
        self._reverse_table: dict = {}  # external_ip -> internal_ip
        self._port_counter: int = 10000
        self._metrics: dict = {
            "outbound_translations": 0,
            "inbound_translations": 0,
            "unknown_inbound": 0,
        }
        logger.info("PublicIPAbstraction initialized: public_ip=%s", public_ip)

    def add_mapping(self, internal_ip: str, external_port: int | None = None) -> int:
        """
        Create a NAT mapping for an internal IP.

        Returns the assigned external port.
        """
        if external_port is None:
            external_port = self._port_counter
            self._port_counter += 1
        external = f"{self.public_ip}:{external_port}"
        self.nat_table[internal_ip] = external
        self._reverse_table[external] = internal_ip
        logger.debug("NAT mapping: %s -> %s", internal_ip, external)
        return external_port

    def translate_outbound(self, packet: dict) -> dict:
        """Rewrite packet source from internal IP to public IP:port."""
        self._metrics["outbound_translations"] += 1
        src = packet.get("src", "")
        if src not in self.nat_table:
            self.add_mapping(src)
        translated = dict(packet)
        translated["src"] = self.nat_table[src]
        logger.debug("Outbound NAT: %s -> %s", src, translated["src"])
        return translated

    def translate_inbound(self, packet: dict) -> dict:
        """Rewrite packet destination from public IP:port to internal IP."""
        self._metrics["inbound_translations"] += 1
        dst = packet.get("dst", "")
        if dst in self._reverse_table:
            translated = dict(packet)
            translated["dst"] = self._reverse_table[dst]
            logger.debug("Inbound NAT: %s -> %s", dst, translated["dst"])
            return translated
        self._metrics["unknown_inbound"] += 1
        logger.warning("Inbound NAT: no mapping for dst=%s", dst)
        return packet

    def get_stats(self) -> dict:
        """Return NAT statistics."""
        return {
            "public_ip": self.public_ip,
            "mappings": len(self.nat_table),
            **self._metrics,
        }
