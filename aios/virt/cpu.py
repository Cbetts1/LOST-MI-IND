"""
cpu.py -- Virtual CPU for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualCPU models an ARM64-like multi-core processor.
  - Tracks clock cycles, per-core utilization, instruction count, cache state.
  - tick() advances the simulation by one cycle; execute() runs a named instruction.
  - CPU load metrics are exported to HardwareMetrics and read by the AI Control Plane
    for scheduling decisions.
  - Introspection hooks fire on tick and significant events.

Integration Points:
  - CPU load       -> AI Control Plane (task scheduling pressure)
  - CPU metrics    -> HardwareMetrics (telemetry)
  - Clock source   -> OS Kernel (scheduler timeslice)
  - Hooks          -> HardwareHooks (introspect, log, metrics)
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vaios.virt.cpu")

SUPPORTED_INSTRUCTIONS = frozenset([
    "NOP", "LOAD", "STORE", "ADD", "SUB", "MUL", "DIV",
    "JMP", "CALL", "RET", "CMP", "AND", "OR", "XOR", "SHIFT",
    "INT", "YIELD", "HLT",
])


class VirtualCore:
    """Simulates a single CPU core."""

    def __init__(self, core_id: int, freq_ghz: float = 2.4) -> None:
        self.core_id = core_id
        self.freq_ghz = freq_ghz
        self.cycles: int = 0
        self.instructions_executed: int = 0
        self.halted: bool = False
        self.utilization: float = 0.0  # 0.0 - 1.0
        self._last_tick = time.monotonic()

    def tick(self) -> None:
        """Advance this core by one cycle."""
        if not self.halted:
            self.cycles += 1
            now = time.monotonic()
            self._last_tick = now

    def execute(self, instruction: str, operands: Optional[List[Any]] = None) -> Any:
        """Execute a virtual instruction on this core."""
        if self.halted:
            raise RuntimeError(f"Core {self.core_id} is halted")
        instr = instruction.upper()
        if instr not in SUPPORTED_INSTRUCTIONS:
            raise ValueError(f"Unsupported instruction: {instr!r}")
        self.instructions_executed += 1
        self.cycles += 1
        if instr == "HLT":
            self.halted = True
            logger.debug("[CPU] Core %d halted", self.core_id)
        elif instr == "NOP":
            pass
        return None

    def set_utilization(self, util: float) -> None:
        """Set simulated utilization (0.0 to 1.0)."""
        self.utilization = max(0.0, min(1.0, util))

    def introspect(self) -> Dict[str, Any]:
        return {
            "core_id": self.core_id,
            "freq_ghz": self.freq_ghz,
            "cycles": self.cycles,
            "instructions_executed": self.instructions_executed,
            "halted": self.halted,
            "utilization": self.utilization,
        }

    def __repr__(self) -> str:
        return f"<VirtualCore id={self.core_id} freq={self.freq_ghz}GHz util={self.utilization:.1%}>"


class VirtualCPU:
    """
    Simulates a multi-core ARM64-like virtual processor.

    Attributes:
        num_cores:  Number of virtual cores (default 4).
        freq_ghz:   Clock frequency in GHz (default 2.4).
        arch:       CPU architecture string (default ARM64).
        cache_kb:   L1 cache size in KB per core (default 64).
    """

    def __init__(
        self,
        num_cores: int = 4,
        freq_ghz: float = 2.4,
        arch: str = "ARM64",
        cache_kb: int = 64,
        metrics=None,
        hooks=None,
    ) -> None:
        self.num_cores = num_cores
        self.freq_ghz = freq_ghz
        self.arch = arch
        self.cache_kb = cache_kb
        self._metrics = metrics
        self._hooks = hooks
        self.cores: List[VirtualCore] = [
            VirtualCore(i, freq_ghz) for i in range(num_cores)
        ]
        self._total_cycles: int = 0
        self._init_time = time.monotonic()
        logger.info(
            "[CPU]  VirtualCPU online -- cores=%d, freq=%.1fGHz, arch=%s",
            num_cores, freq_ghz, arch,
        )
        if self._hooks:
            self._hooks.fire("cpu.init", self.introspect())

    def tick(self) -> None:
        """Advance all cores by one cycle."""
        for core in self.cores:
            core.tick()
        self._total_cycles += 1
        avg_util = self._avg_utilization()
        if self._metrics:
            self._metrics.set_gauge("cpu.total_cycles", self._total_cycles)
            self._metrics.set_gauge("cpu.avg_utilization", avg_util)
        if self._hooks:
            self._hooks.fire("cpu.tick", {"cycles": self._total_cycles, "util": avg_util})

    def execute(self, instruction: str, core_id: int = 0, operands=None) -> Any:
        """Execute a virtual instruction on the specified core."""
        result = self.cores[core_id].execute(instruction, operands)
        if self._metrics:
            self._metrics.increment_counter("cpu.instructions_executed")
        if self._hooks:
            self._hooks.fire("cpu.execute", {"instr": instruction, "core": core_id})
        return result

    def set_core_utilization(self, core_id: int, util: float) -> None:
        """Set simulated utilization for a specific core."""
        self.cores[core_id].set_utilization(util)
        if self._metrics:
            self._metrics.set_gauge(f"cpu.core{core_id}.utilization", util)
            self._metrics.set_gauge("cpu.avg_utilization", self._avg_utilization())

    def get_load(self) -> float:
        """Return average CPU utilization across all cores (0.0 - 1.0)."""
        return self._avg_utilization()

    def get_total_cycles(self) -> int:
        return self._total_cycles

    def get_uptime_s(self) -> float:
        return time.monotonic() - self._init_time

    def _avg_utilization(self) -> float:
        return sum(c.utilization for c in self.cores) / self.num_cores

    def introspect(self) -> Dict[str, Any]:
        """Introspection hook -- return full CPU state snapshot."""
        return {
            "arch": self.arch,
            "num_cores": self.num_cores,
            "freq_ghz": self.freq_ghz,
            "cache_kb": self.cache_kb,
            "total_cycles": self._total_cycles,
            "avg_utilization": self._avg_utilization(),
            "uptime_s": self.get_uptime_s(),
            "cores": [c.introspect() for c in self.cores],
        }

    def __repr__(self) -> str:
        return (
            f"<VirtualCPU arch={self.arch} cores={self.num_cores} "
            f"freq={self.freq_ghz}GHz util={self._avg_utilization():.1%}>"
        )
