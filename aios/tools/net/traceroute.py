"""
VAI-OS Virtual Traceroute
Simulates hop-by-hop routing within the virtual network layer.
"""
import logging
import random

logger = logging.getLogger(__name__)

_VIRTUAL_HOPS = [
    "10.0.0.1",
    "10.0.1.1",
    "172.16.0.1",
    "203.0.113.1",
]


def traceroute(host: str, max_hops: int = 30) -> list:
    """Simulate traceroute to host. Returns list of hop dicts."""
    logger.debug("traceroute %s max_hops=%d", host, max_hops)
    hops = []
    hop_count = random.randint(3, min(max_hops, 8))
    for i in range(1, hop_count + 1):
        if i - 1 < len(_VIRTUAL_HOPS):
            ip = _VIRTUAL_HOPS[i - 1]
        else:
            # Generate synthetic hop IPs
            ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        rtt = round(random.uniform(1.0, 50.0) * i, 3)
        hops.append({"hop": i, "ip": ip, "rtt_ms": rtt})
    # Final hop is the destination
    hops.append({"hop": hop_count + 1, "ip": host, "rtt_ms": round(random.uniform(10.0, 200.0), 3)})
    return hops
