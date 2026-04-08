"""
VirtualFirewall: Simulates stateless packet filtering with ordered
rule evaluation (allow/deny) for the VAI-OS virtual network stack.
"""
import logging

logger = logging.getLogger(__name__)


class VirtualFirewall:
    """Simulates a virtual stateless firewall with ordered ACL rules."""

    def __init__(self):
        self.rules: list[dict] = []
        self._default_action: str = "allow"
        self._metrics: dict = {
            "allowed": 0,
            "denied": 0,
            "rule_hits": {},
        }
        logger.info("VirtualFirewall initialized, default_action=%s", self._default_action)

    def add_rule(
        self,
        action: str,
        proto: str = "*",
        src: str = "*",
        dst: str = "*",
        port: int | str = "*",
    ) -> int:
        """
        Append a firewall rule.

        Returns the index of the new rule.
        """
        rule = {"action": action, "proto": proto, "src": src, "dst": dst, "port": port}
        self.rules.append(rule)
        idx = len(self.rules) - 1
        self._metrics["rule_hits"][idx] = 0
        logger.debug("Firewall rule added [%d]: %s", idx, rule)
        return idx

    def remove_rule(self, idx: int) -> bool:
        """Remove the rule at the given index."""
        if 0 <= idx < len(self.rules):
            removed = self.rules.pop(idx)
            logger.debug("Firewall rule removed [%d]: %s", idx, removed)
            return True
        return False

    def check_packet(self, packet: dict) -> bool:
        """
        Evaluate packet against rules in order.

        Returns True if packet is allowed, False if denied.
        """
        proto = packet.get("proto", "*")
        src = packet.get("src", "*")
        dst = packet.get("dst", "*")
        port = packet.get("port", "*")

        for idx, rule in enumerate(self.rules):
            if self._match(rule, proto, src, dst, port):
                self._metrics["rule_hits"][idx] = self._metrics["rule_hits"].get(idx, 0) + 1
                allowed = rule["action"] == "allow"
                if allowed:
                    self._metrics["allowed"] += 1
                else:
                    self._metrics["denied"] += 1
                logger.debug(
                    "Packet %s by rule[%d]: src=%s dst=%s",
                    rule["action"],
                    idx,
                    src,
                    dst,
                )
                return allowed

        # Default action
        allowed = self._default_action == "allow"
        if allowed:
            self._metrics["allowed"] += 1
        else:
            self._metrics["denied"] += 1
        return allowed

    def _match(self, rule: dict, proto: str, src: str, dst: str, port) -> bool:
        """Return True if the rule matches the given packet attributes."""
        return all(
            [
                rule["proto"] in ("*", proto),
                rule["src"] in ("*", src),
                rule["dst"] in ("*", dst),
                str(rule["port"]) in ("*", str(port)),
            ]
        )

    def get_stats(self) -> dict:
        """Return firewall statistics."""
        return {
            "rule_count": len(self.rules),
            "default_action": self._default_action,
            **self._metrics,
        }
