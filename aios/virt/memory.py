"""
memory.py -- Virtual Memory for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualMemory simulates device RAM as a byte-addressable block.
  - Supports allocate/free (slab-style), read, write operations.
  - Tracks allocation pressure; fires hooks on threshold crossings.
  - Memory map zones: SYSTEM (kernel), USER, DMA, TEE (secure).
  - Consumed by: OS Kernel (heap/stack), AI Control Plane (model buffers),
    Security Layer (TEE region).

Integration Points:
  - Allocation pressure -> AI Control Plane (scheduling decisions)
  - Memory map          -> OS Kernel (mmap)
  - TEE region          -> Security Layer
  - Metrics             -> HardwareMetrics
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("vaios.virt.memory")

MB = 1024 * 1024
GB = 1024 * MB

# Memory zone identifiers
ZONE_SYSTEM = "system"
ZONE_USER   = "user"
ZONE_DMA    = "dma"
ZONE_TEE    = "tee"

ZONES = (ZONE_SYSTEM, ZONE_USER, ZONE_DMA, ZONE_TEE)


class MemoryBlock:
    """Represents an allocated block of virtual memory."""
    _next_id = 1

    def __init__(self, addr: int, size: int, zone: str, tag: str = "") -> None:
        self.block_id = MemoryBlock._next_id
        MemoryBlock._next_id += 1
        self.addr = addr
        self.size = size
        self.zone = zone
        self.tag = tag
        self.allocated_at = time.monotonic()

    def __repr__(self) -> str:
        return (
            f"<MemoryBlock id={self.block_id} addr=0x{self.addr:08X} "
            f"size={self.size // 1024}KB zone={self.zone} tag={self.tag!r}>"
        )


class VirtualMemory:
    """
    Simulates device RAM.

    Default layout (4 GB total):
      - System: 512 MB  (OS kernel, drivers)
      - User:   3264 MB (user processes, AI buffers)
      - DMA:    128 MB  (hardware DMA)
      - TEE:    64 MB   (secure enclave)
      - Reserved: remainder
    """

    ZONE_SIZES_MB = {
        ZONE_SYSTEM: 512,
        ZONE_USER:   3264,
        ZONE_DMA:    128,
        ZONE_TEE:    64,
    }
    ZONE_BASES_MB = {
        ZONE_SYSTEM: 256,
        ZONE_USER:   768,
        ZONE_DMA:    4096 - 256,
        ZONE_TEE:    4096 - 128,
    }

    def __init__(
        self,
        capacity_mb: int = 4096,
        metrics=None,
        hooks=None,
    ) -> None:
        self.capacity_mb = capacity_mb
        self.capacity_bytes = capacity_mb * MB
        self._metrics = metrics
        self._hooks = hooks
        self._allocations: Dict[int, MemoryBlock] = {}  # block_id -> block
        self._used_bytes: int = 0
        self._next_addr: int = self.ZONE_BASES_MB[ZONE_USER] * MB
        self._init_time = time.monotonic()
        logger.info("[MEM]  VirtualMemory online -- capacity=%dMB", capacity_mb)
        if self._hooks:
            self._hooks.fire("memory.init", {"capacity_mb": capacity_mb})

    def allocate(self, size: int, zone: str = ZONE_USER, tag: str = "") -> MemoryBlock:
        """
        Allocate a block of virtual memory.

        Args:
            size:  Number of bytes to allocate.
            zone:  Memory zone (system, user, dma, tee).
            tag:   Optional label for introspection.

        Returns:
            MemoryBlock representing the allocated region.

        Raises:
            MemoryError: If insufficient memory is available.
        """
        if zone not in ZONES:
            raise ValueError(f"Unknown memory zone: {zone!r}")
        available = self.capacity_bytes - self._used_bytes
        if size > available:
            raise MemoryError(
                f"VirtualMemory: cannot allocate {size} bytes "
                f"(available={available} bytes)"
            )
        block = MemoryBlock(self._next_addr, size, zone, tag)
        self._allocations[block.block_id] = block
        self._next_addr += size
        self._used_bytes += size
        pressure = self._used_bytes / self.capacity_bytes
        if self._metrics:
            self._metrics.set_gauge("memory.used_bytes", self._used_bytes)
            self._metrics.set_gauge("memory.pressure", pressure)
            self._metrics.increment_counter("memory.alloc_count")
        if self._hooks:
            self._hooks.fire("memory.alloc", {"size": size, "zone": zone, "pressure": pressure})
        return block

    def free(self, block: MemoryBlock) -> None:
        """Free a previously allocated memory block."""
        if block.block_id not in self._allocations:
            raise ValueError(f"Block {block.block_id} not found in allocations")
        self._used_bytes -= block.size
        del self._allocations[block.block_id]
        if self._metrics:
            self._metrics.set_gauge("memory.used_bytes", self._used_bytes)
            self._metrics.set_gauge("memory.pressure", self._used_bytes / self.capacity_bytes)
            self._metrics.increment_counter("memory.free_count")
        if self._hooks:
            self._hooks.fire("memory.free", {"block_id": block.block_id, "size": block.size})

    def read(self, addr: int, size: int = 1) -> bytes:
        """Simulate a memory read (returns zero-bytes for virtual memory)."""
        if self._metrics:
            self._metrics.increment_counter("memory.reads")
        if self._hooks:
            self._hooks.fire("memory.read", {"addr": addr, "size": size})
        return bytes(size)

    def write(self, addr: int, data: bytes) -> None:
        """Simulate a memory write."""
        if self._metrics:
            self._metrics.increment_counter("memory.writes")
        if self._hooks:
            self._hooks.fire("memory.write", {"addr": addr, "size": len(data)})

    def get_pressure(self) -> float:
        """Return memory pressure as fraction (0.0 = empty, 1.0 = full)."""
        return self._used_bytes / self.capacity_bytes

    def get_available_mb(self) -> float:
        return (self.capacity_bytes - self._used_bytes) / MB

    def get_used_mb(self) -> float:
        return self._used_bytes / MB

    def list_allocations(self) -> List[MemoryBlock]:
        return list(self._allocations.values())

    def introspect(self) -> Dict[str, Any]:
        return {
            "capacity_mb": self.capacity_mb,
            "used_mb": self.get_used_mb(),
            "available_mb": self.get_available_mb(),
            "pressure": self.get_pressure(),
            "allocation_count": len(self._allocations),
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        return (
            f"<VirtualMemory capacity={self.capacity_mb}MB "
            f"used={self.get_used_mb():.0f}MB "
            f"pressure={self.get_pressure():.1%}>"
        )
