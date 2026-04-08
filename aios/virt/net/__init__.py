"""
Virtual Network stack package.
Exposes VirtualNIC, VirtualRouter, VirtualFirewall, PublicIPAbstraction.
"""
from .nic import VirtualNIC
from .router import VirtualRouter
from .firewall import VirtualFirewall
from .public_ip import PublicIPAbstraction

__all__ = ["VirtualNIC", "VirtualRouter", "VirtualFirewall", "PublicIPAbstraction"]
