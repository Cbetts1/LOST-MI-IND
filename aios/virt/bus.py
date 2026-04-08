"""
bus.py -- Virtual System Bus for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualHardwareBus is the central device registry and communication bus.
  - All virtual hardware devices register with the bus at startup.
  - The bus provides device enumeration, discovery, and inter-device messaging.
  - The OS Kernel reads the bus to discover available hardware.
  - Acts as the single integration point between all virtual hardware components
    and the OS layer above.

Integration Points:
  - Device registry -> OS Kernel (hardware discovery)
  - Bus events      -> HardwareHooks (device attach/detach)
  - Bus metrics     -> HardwareMetrics
  - Boot handoff    -> OS Kernel Core (after all devices registered)
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("vaios.virt.bus")


class BusDevice:
    """Wrapper around a registered hardware device."""
    def __init__(self, name: str, device: Any, device_type: str) -> None:
        self.name = name
        self.device = device
        self.device_type = device_type
        self.registered_at = time.monotonic()

    def __repr__(self) -> str:
        return f"<BusDevice name={self.name!r} type={self.device_type!r}>"


class VirtualHardwareBus:
    """
    Central hardware bus — device registry and inter-device communication.

    All virtual hardware devices must register here before the OS boots.
    The bus exposes the device table to the OS Kernel for hardware discovery.
    """

    def __init__(self, metrics=None, hooks=None) -> None:
        self._metrics = metrics
        self._hooks = hooks
        self._devices: Dict[str, BusDevice] = {}
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._init_time = time.monotonic()
        logger.info("[BUS]  VirtualHardwareBus initialized")
        if self._hooks:
            self._hooks.fire("bus.init", {})

    def register_device(self, name: str, device: Any, device_type: str = "generic") -> None:
        """
        Register a hardware device on the bus.

        Args:
            name:        Unique device name (e.g. 'cpu', 'memory').
            device:      The device object instance.
            device_type: Category string for the device.
        """
        if name in self._devices:
            raise ValueError(f"Device {name!r} is already registered on the bus")
        bus_dev = BusDevice(name, device, device_type)
        self._devices[name] = bus_dev
        logger.info("[BUS]  Device registered: %s (%s)", name, device_type)
        if self._metrics:
            self._metrics.set_gauge("bus.device_count", len(self._devices))
        if self._hooks:
            self._hooks.fire("bus.device_attach", {"name": name, "type": device_type})

    def unregister_device(self, name: str) -> None:
        """Remove a device from the bus."""
        if name not in self._devices:
            raise ValueError(f"Device {name!r} not found on bus")
        del self._devices[name]
        logger.info("[BUS]  Device unregistered: %s", name)
        if self._hooks:
            self._hooks.fire("bus.device_detach", {"name": name})

    def get_device(self, name: str) -> Optional[Any]:
        """Return the device object for the given name, or None."""
        entry = self._devices.get(name)
        return entry.device if entry else None

    def enumerate_devices(self) -> List[Dict[str, Any]]:
        """
        Return a list of all registered devices with their metadata.
        Called by the OS Kernel during hardware discovery.
        """
        result = []
        for name, bd in self._devices.items():
            entry = {
                "name": name,
                "type": bd.device_type,
                "registered_at": bd.registered_at,
            }
            if hasattr(bd.device, "introspect"):
                entry["state"] = bd.device.introspect()
            result.append(entry)
        return result

    def send_message(self, target: str, message: Any, sender: str = "bus") -> None:
        """Send an inter-device message to a named device."""
        handlers = self._message_handlers.get(target, [])
        for handler in handlers:
            try:
                handler(sender, message)
            except Exception as exc:
                logger.warning("[BUS] Message handler error for %r: %s", target, exc)
        if self._hooks:
            self._hooks.fire("bus.message", {"target": target, "sender": sender})

    def subscribe(self, device_name: str, handler: Callable) -> None:
        """Subscribe a message handler for a device."""
        if device_name not in self._message_handlers:
            self._message_handlers[device_name] = []
        self._message_handlers[device_name].append(handler)

    def get_device_count(self) -> int:
        return len(self._devices)

    def is_device_registered(self, name: str) -> bool:
        return name in self._devices

    def introspect(self) -> Dict[str, Any]:
        return {
            "device_count": len(self._devices),
            "devices": [
                {"name": n, "type": d.device_type}
                for n, d in self._devices.items()
            ],
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        return f"<VirtualHardwareBus devices={list(self._devices.keys())}>"
