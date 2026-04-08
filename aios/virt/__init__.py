"""
__init__.py -- VAI-OS Virtual Hardware Layer Package

Architecture Notes:
  - This package provides the complete virtual hardware abstraction for VAI-OS.
  - All virtual hardware devices register on VirtualHardwareBus at init time.
  - The OS Kernel Core discovers hardware via bus.enumerate_devices().
  - Call initialize_hardware() to bring up the full virtual hardware layer.

Boot sequence within this package:
  1. HardwareHooks singleton created (introspection/logging/metrics hooks)
  2. HardwareMetrics singleton created
  3. VirtualFirmware initialized (loads boot table)
  4. VirtualHardwareBus created
  5. All devices instantiated and registered on bus:
     cpu, memory, storage, nic, display, io, sensors, radio
  6. Boot handoff ready for OS Kernel

Exports:
  - VirtualHardwareBus
  - VirtualCPU, VirtualMemory, VirtualStorage
  - VirtualNIC, VirtualDisplay, VirtualIO
  - VirtualFirmware, VirtualSensors, VirtualRadio
  - HardwareMetrics, HardwareHooks
  - initialize_hardware()
  - get_hardware_bus()
"""

import logging

logger = logging.getLogger("vaios.virt")

from .hooks import HardwareHooks, get_hooks, install_builtin_hooks
from .metrics import HardwareMetrics, get_metrics
from .firmware import VirtualFirmware
from .bus import VirtualHardwareBus
from .cpu import VirtualCPU
from .memory import VirtualMemory
from .storage import VirtualStorage
from .nic import VirtualNIC
from .display import VirtualDisplay
from .io import VirtualIO
from .sensors import VirtualSensors
from .radio import VirtualRadio

__all__ = [
    "VirtualHardwareBus",
    "VirtualCPU",
    "VirtualMemory",
    "VirtualStorage",
    "VirtualNIC",
    "VirtualDisplay",
    "VirtualIO",
    "VirtualFirmware",
    "VirtualSensors",
    "VirtualRadio",
    "HardwareMetrics",
    "HardwareHooks",
    "initialize_hardware",
    "get_hardware_bus",
]

_bus_instance = None


def initialize_hardware(
    cpu_cores: int = 4,
    cpu_freq_ghz: float = 2.4,
    memory_mb: int = 4096,
    storage_gb: int = 128,
    firmware_config_path: str = None,
) -> VirtualHardwareBus:
    """
    Initialize the complete Virtual Hardware Layer.

    Creates all virtual devices, registers them on the bus, and returns
    the VirtualHardwareBus ready for the OS Kernel to consume.

    Args:
        cpu_cores:           Number of virtual CPU cores.
        cpu_freq_ghz:        Virtual CPU clock frequency (GHz).
        memory_mb:           Virtual RAM capacity (MB).
        storage_gb:          Virtual storage capacity (GB).
        firmware_config_path: Optional path to firmware config JSON.

    Returns:
        Initialized VirtualHardwareBus with all devices registered.
    """
    global _bus_instance

    logger.info("[VIRT] Virtual Hardware Layer initializing...")

    # 1. Hooks and metrics singletons
    hooks = get_hooks()
    install_builtin_hooks(hooks)
    metrics = get_metrics()

    # 2. Firmware
    fw = VirtualFirmware(config_path=firmware_config_path)
    fw.initialize()

    # 3. Bus
    bus = VirtualHardwareBus(metrics=metrics, hooks=hooks)

    # 4. Instantiate all devices
    cpu = VirtualCPU(
        num_cores=cpu_cores,
        freq_ghz=cpu_freq_ghz,
        metrics=metrics,
        hooks=hooks,
    )
    memory = VirtualMemory(capacity_mb=memory_mb, metrics=metrics, hooks=hooks)
    storage = VirtualStorage(capacity_gb=storage_gb, metrics=metrics, hooks=hooks)
    nic = VirtualNIC(metrics=metrics, hooks=hooks)
    display = VirtualDisplay(metrics=metrics, hooks=hooks)
    io = VirtualIO(metrics=metrics, hooks=hooks)
    sensors = VirtualSensors(metrics=metrics, hooks=hooks)
    radio = VirtualRadio(metrics=metrics, hooks=hooks)

    # 5. Register all devices on bus
    bus.register_device("firmware", fw, "firmware")
    bus.register_device("cpu",      cpu,     "processor")
    bus.register_device("memory",   memory,  "ram")
    bus.register_device("storage",  storage, "storage")
    bus.register_device("nic",      nic,     "network")
    bus.register_device("display",  display, "display")
    bus.register_device("io",       io,      "input")
    bus.register_device("sensors",  sensors, "sensors")
    bus.register_device("radio",    radio,   "radio")

    devices = [d["name"] for d in bus.enumerate_devices()]
    logger.info("[BUS]  Devices registered: %s", ", ".join(devices))
    logger.info("[VIRT] Virtual Hardware Layer READY -- boot handoff to OS Kernel")

    hooks.fire("virt.ready", {"devices": devices})
    _bus_instance = bus
    return bus


def get_hardware_bus() -> VirtualHardwareBus:
    """Return the initialized hardware bus singleton."""
    if _bus_instance is None:
        raise RuntimeError(
            "Hardware not initialized. Call initialize_hardware() first."
        )
    return _bus_instance
