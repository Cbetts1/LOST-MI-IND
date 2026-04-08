"""
VAI-OS Virtual ifconfig
Displays virtual network interface configuration.
"""
import logging

logger = logging.getLogger(__name__)


def ifconfig(nic=None) -> str:
    """Return interface configuration string for the virtual NIC."""
    logger.debug("ifconfig called, nic=%s", nic)
    interfaces = {
        "vaios0": {
            "ip": "10.0.0.1",
            "netmask": "255.255.255.0",
            "broadcast": "10.0.0.255",
            "mac": "02:VA:IO:S0:00:01",
            "mtu": 1500,
            "flags": "UP BROADCAST RUNNING MULTICAST",
            "rx_packets": 1024,
            "tx_packets": 896,
        },
        "lo": {
            "ip": "127.0.0.1",
            "netmask": "255.0.0.0",
            "broadcast": "",
            "mac": "00:00:00:00:00:00",
            "mtu": 65536,
            "flags": "UP LOOPBACK RUNNING",
            "rx_packets": 512,
            "tx_packets": 512,
        },
    }

    if nic and nic not in interfaces:
        return f"ifconfig: {nic}: interface not found"

    targets = {nic: interfaces[nic]} if nic else interfaces
    lines = []
    for name, info in targets.items():
        lines.append(f"{name}: flags={info['flags']}  mtu {info['mtu']}")
        lines.append(f"        inet {info['ip']}  netmask {info['netmask']}" +
                     (f"  broadcast {info['broadcast']}" if info['broadcast'] else ""))
        lines.append(f"        ether {info['mac']}")
        lines.append(f"        RX packets {info['rx_packets']}  TX packets {info['tx_packets']}")
        lines.append("")
    return "\n".join(lines)
