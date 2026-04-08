"""
firmware.py — Virtual Firmware / BIOS for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualFirmware simulates the device firmware/BIOS layer.
  - It owns the boot configuration table used by the OS Kernel at startup.
  - Provides power-on-self-test (POST) results, device enumeration hints, and
    hardware capability flags consumed by the OS and Security (TEE) layers.
  - The firmware version and configuration are loaded from:
      /aios/data/hardware/firmware_config.json

Integration Points:
  - Boot table read by: OS Kernel Core (boot sequence)
  - TEE region reserved by: Security Layer (Trusted Execution Environment)
  - Device hints used by: VirtualHardwareBus (device registration order)
  - Firmware version reported to: Cloud Layer (OTA update checks)
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("vaios.virt.firmware")

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "hardware", "firmware_config.json"
)

DEFAULT_FIRMWARE_CONFIG: Dict[str, Any] = {
    "firmware_version": "VAIOS-FW-1.0",
    "build_date": "2026-04-08",
    "arch": "ARM64",
    "secure_boot": True,
    "tee_region_mb": 64,
    "boot_devices": ["storage", "network"],
    "capabilities": {
        "virtualization": True,
        "crypto_accel": True,
        "trusted_platform": True,
        "secure_enclave": True,
    },
    "memory_map": {
        "rom_start": "0x00000000",
        "rom_size_mb": 4,
        "ram_start": "0x10000000",
        "ram_size_mb": 4096,
        "tee_start": "0xF0000000",
        "tee_size_mb": 64,
    },
}


class VirtualFirmware:
    """
    Simulates the device firmware (BIOS/UEFI equivalent).

    Responsibilities:
      - Provide the boot configuration table to the OS Kernel.
      - Report POST (Power-On Self-Test) results.
      - Expose hardware capability flags.
      - Manage TEE memory region reservation.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or _DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._post_results: Dict[str, bool] = {}
        self._initialized = False
        self._init_time: float = 0.0

    def initialize(self) -> None:
        """Load firmware config and run POST checks."""
        self._config = self._load_config()
        self._init_time = time.monotonic()
        self._post_results = self._run_post()
        self._initialized = True
        logger.info("[FW]  VirtualFirmware online — version=%s", self._config.get("firmware_version"))

    def _load_config(self) -> Dict[str, Any]:
        """Load firmware config from JSON file, falling back to defaults."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as fh:
                config = json.load(fh)
                logger.debug("[FW] Loaded firmware config from %s", self.config_path)
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            logger.debug("[FW] Config file not found, using defaults")
            return dict(DEFAULT_FIRMWARE_CONFIG)

    def _run_post(self) -> Dict[str, bool]:
        """Run Power-On Self-Test and return pass/fail per component."""
        results = {
            "cpu": True,
            "memory": True,
            "storage": True,
            "display": True,
            "radio": True,
            "sensors": True,
            "crypto": self._config.get("capabilities", {}).get("crypto_accel", False),
            "tee": self._config.get("capabilities", {}).get("secure_enclave", False),
        }
        passed = sum(results.values())
        total = len(results)
        logger.info("[FW] POST complete — %d/%d checks passed", passed, total)
        return results

    def get_boot_table(self) -> Dict[str, Any]:
        """
        Return the boot configuration table.

        The OS Kernel reads this during initialization to configure itself.
        """
        if not self._initialized:
            self.initialize()
        return {
            "firmware_version": self._config.get("firmware_version"),
            "arch": self._config.get("arch"),
            "secure_boot": self._config.get("secure_boot"),
            "boot_devices": self._config.get("boot_devices"),
            "memory_map": self._config.get("memory_map"),
            "capabilities": self._config.get("capabilities"),
            "post_results": self._post_results,
            "tee_region_mb": self._config.get("tee_region_mb"),
        }

    def get_version(self) -> str:
        """Return the firmware version string."""
        return self._config.get("firmware_version", "UNKNOWN")

    def get_capability(self, cap: str) -> bool:
        """Return True if the named hardware capability is available."""
        return bool(self._config.get("capabilities", {}).get(cap, False))

    def get_memory_map(self) -> Dict[str, Any]:
        """Return the physical memory map."""
        return self._config.get("memory_map", {})

    def get_post_results(self) -> Dict[str, bool]:
        """Return POST results dict."""
        if not self._initialized:
            self.initialize()
        return dict(self._post_results)

    def introspect(self) -> Dict[str, Any]:
        """Introspection hook — return full firmware state snapshot."""
        return {
            "initialized": self._initialized,
            "version": self.get_version(),
            "config": self._config,
            "post_results": self._post_results,
            "uptime_s": time.monotonic() - self._init_time if self._initialized else 0,
        }

    def __repr__(self) -> str:
        return f"<VirtualFirmware version={self.get_version()!r} initialized={self._initialized}>"
