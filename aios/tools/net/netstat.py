"""
VAI-OS Virtual Netstat
Displays virtual network connections and listening ports.
"""
import logging

logger = logging.getLogger(__name__)

_VIRTUAL_CONNECTIONS = [
    {"proto": "tcp", "local": "10.0.0.1:22", "remote": "0.0.0.0:*", "state": "LISTEN"},
    {"proto": "tcp", "local": "10.0.0.1:80", "remote": "0.0.0.0:*", "state": "LISTEN"},
    {"proto": "tcp", "local": "10.0.0.1:443", "remote": "0.0.0.0:*", "state": "LISTEN"},
    {"proto": "udp", "local": "10.0.0.1:53", "remote": "0.0.0.0:*", "state": ""},
    {"proto": "tcp", "local": "10.0.0.1:8080", "remote": "10.0.0.2:54321", "state": "ESTABLISHED"},
]


def netstat() -> list:
    """Return virtual network connection table."""
    logger.debug("netstat called")
    return list(_VIRTUAL_CONNECTIONS)


def format_netstat() -> str:
    """Return formatted netstat output string."""
    lines = ["Proto  Local Address          Remote Address         State"]
    lines.append("-" * 65)
    for c in netstat():
        lines.append(
            f"{c['proto']:<6} {c['local']:<22} {c['remote']:<22} {c['state']}"
        )
    return "\n".join(lines)
