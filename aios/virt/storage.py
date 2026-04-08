"""
storage.py -- Virtual Storage (eMMC/Flash) for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualStorage simulates 128 GB eMMC flash storage.
  - Block-level I/O: read_block(lba) / write_block(lba, data).
  - Partition table with pre-defined partitions: system, user, data, recovery.
  - Backing store is in-memory (dict of LBA -> bytes) for simulation.
  - Consumed by: OS Kernel (VFS mount), System Services (file storage),
    Cloud Layer (cache/sync), AI Control Plane (model storage).

Integration Points:
  - Block I/O    -> OS Kernel (VFS layer)
  - Partition map -> System Services
  - Metrics       -> HardwareMetrics
  - Hooks         -> HardwareHooks
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vaios.virt.storage")

BLOCK_SIZE = 4096  # 4 KB LBA blocks
GB = 1024 * 1024 * 1024
MB = 1024 * 1024


class Partition:
    def __init__(self, name: str, start_lba: int, num_blocks: int, ptype: str = "ext4") -> None:
        self.name = name
        self.start_lba = start_lba
        self.num_blocks = num_blocks
        self.ptype = ptype

    @property
    def size_mb(self) -> float:
        return (self.num_blocks * BLOCK_SIZE) / MB

    def __repr__(self) -> str:
        return f"<Partition {self.name!r} start={self.start_lba} blocks={self.num_blocks} size={self.size_mb:.0f}MB>"


class VirtualStorage:
    """
    Simulates eMMC block storage device.

    Default partition layout (128 GB):
      - system:    4 GB   (OS / firmware)
      - user:      96 GB  (user data)
      - data:      24 GB  (app data, AI models)
      - recovery:  4 GB   (recovery image)
    """

    DEFAULT_CAPACITY_GB = 128
    PARTITIONS = [
        Partition("system",   start_lba=0,        num_blocks=1_048_576,   ptype="ext4"),
        Partition("user",     start_lba=1_048_576, num_blocks=25_165_824, ptype="ext4"),
        Partition("data",     start_lba=26_214_400, num_blocks=6_291_456, ptype="ext4"),
        Partition("recovery", start_lba=32_505_856, num_blocks=1_048_576, ptype="raw"),
    ]

    def __init__(
        self,
        capacity_gb: int = DEFAULT_CAPACITY_GB,
        metrics=None,
        hooks=None,
    ) -> None:
        self.capacity_gb = capacity_gb
        self.total_blocks = (capacity_gb * GB) // BLOCK_SIZE
        self._metrics = metrics
        self._hooks = hooks
        self._blocks: Dict[int, bytes] = {}  # LBA -> block data (in-memory)
        self._read_count: int = 0
        self._write_count: int = 0
        self._init_time = time.monotonic()
        logger.info("[STG]  VirtualStorage online -- capacity=%dGB type=eMMC", capacity_gb)
        if self._hooks:
            self._hooks.fire("storage.init", {"capacity_gb": capacity_gb})

    def read_block(self, lba: int) -> bytes:
        """Read a 4KB block at the given Logical Block Address."""
        if lba < 0 or lba >= self.total_blocks:
            raise ValueError(f"LBA {lba} out of range (max={self.total_blocks - 1})")
        self._read_count += 1
        data = self._blocks.get(lba, bytes(BLOCK_SIZE))
        if self._metrics:
            self._metrics.increment_counter("storage.reads")
            self._metrics.set_gauge("storage.read_total", self._read_count)
        if self._hooks:
            self._hooks.fire("storage.read_block", {"lba": lba})
        return data

    def write_block(self, lba: int, data: bytes) -> None:
        """Write a 4KB block at the given Logical Block Address."""
        if lba < 0 or lba >= self.total_blocks:
            raise ValueError(f"LBA {lba} out of range (max={self.total_blocks - 1})")
        if len(data) != BLOCK_SIZE:
            raise ValueError(f"Block data must be exactly {BLOCK_SIZE} bytes, got {len(data)}")
        self._write_count += 1
        self._blocks[lba] = data
        if self._metrics:
            self._metrics.increment_counter("storage.writes")
            self._metrics.set_gauge("storage.write_total", self._write_count)
            self._metrics.set_gauge("storage.blocks_used", len(self._blocks))
        if self._hooks:
            self._hooks.fire("storage.write_block", {"lba": lba})

    def get_partitions(self) -> List[Partition]:
        """Return the partition table."""
        return list(self.PARTITIONS)

    def find_partition(self, name: str) -> Optional[Partition]:
        """Return a partition by name."""
        for p in self.PARTITIONS:
            if p.name == name:
                return p
        return None

    def get_used_blocks(self) -> int:
        return len(self._blocks)

    def get_free_blocks(self) -> int:
        return self.total_blocks - len(self._blocks)

    def get_utilization(self) -> float:
        return len(self._blocks) / self.total_blocks

    def introspect(self) -> Dict[str, Any]:
        return {
            "capacity_gb": self.capacity_gb,
            "total_blocks": self.total_blocks,
            "used_blocks": self.get_used_blocks(),
            "free_blocks": self.get_free_blocks(),
            "utilization": self.get_utilization(),
            "read_count": self._read_count,
            "write_count": self._write_count,
            "partitions": [repr(p) for p in self.PARTITIONS],
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        return (
            f"<VirtualStorage capacity={self.capacity_gb}GB "
            f"type=eMMC used={self.get_used_blocks()} blocks>"
        )
