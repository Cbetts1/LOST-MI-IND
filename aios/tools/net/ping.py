"""
VAI-OS Virtual Ping
Simulates ICMP ping within the virtual network layer.
"""
import logging
import random
import time

logger = logging.getLogger(__name__)


def ping(host: str, count: int = 4) -> dict:
    """Simulate pinging a host. Returns stats dict."""
    logger.debug("ping %s count=%d", host, count)
    rtts = []
    received = 0
    for _ in range(count):
        # Simulate packet with random RTT between 1-100ms; 5% packet loss
        if random.random() > 0.05:
            rtt = round(random.uniform(1.0, 80.0), 3)
            rtts.append(rtt)
            received += 1
        time.sleep(0)  # yield
    avg_rtt = round(sum(rtts) / len(rtts), 3) if rtts else 0.0
    result = {
        "host": host,
        "sent": count,
        "received": received,
        "lost": count - received,
        "rtt_ms_min": round(min(rtts), 3) if rtts else 0.0,
        "rtt_ms_max": round(max(rtts), 3) if rtts else 0.0,
        "rtt_ms_avg": avg_rtt,
    }
    return result
