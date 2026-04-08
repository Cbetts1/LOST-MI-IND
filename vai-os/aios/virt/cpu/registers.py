"""
VAI-OS Virtual CPU Registers
=============================
Architecture: VAI-ISA-1
Layer: Virtual Hardware (Layer 1)

Purpose:
    Defines and manages the register file for the virtual CPU.
    Provides general-purpose, control, and flag registers.

Integration:
    - Used by virt/cpu/pipeline.py during instruction execution.
    - Exposed to AI via hardware_agent.py for introspection.
    - Exposed to OS core via hardware API.
"""

import logging

logger = logging.getLogger("vaios.virt.cpu.registers")


class Registers:
    """Virtual CPU register file for VAI-ISA-1."""

    GENERAL = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]
    CONTROL = ["pc", "sp", "lr"]
    FLAGS = ["zf", "cf", "sf", "of"]

    def __init__(self):
        """Initialise all registers to zero."""
        self._reg = {name: 0 for name in self.GENERAL + self.CONTROL}
        self._flags = {name: False for name in self.FLAGS}
        logger.debug("Register file initialised.")

    # ── General / Control access ──────────────────────────────────────────

    def read(self, name: str) -> int:
        """Read a register by name.

        Args:
            name: Register name (e.g. 'r0', 'pc').

        Returns:
            Current 32-bit integer value.

        Raises:
            KeyError: If the register name is invalid.
        """
        if name in self._reg:
            return self._reg[name]
        raise KeyError(f"Unknown register: {name!r}")

    def write(self, name: str, value: int) -> None:
        """Write a value to a register.

        Args:
            name: Register name.
            value: Integer value (masked to 32 bits).
        """
        if name not in self._reg:
            raise KeyError(f"Unknown register: {name!r}")
        self._reg[name] = value & 0xFFFF_FFFF
        logger.debug("REG %s = 0x%08X", name, self._reg[name])

    # ── Flag access ───────────────────────────────────────────────────────

    def get_flag(self, name: str) -> bool:
        """Read a CPU flag.

        Args:
            name: Flag name ('zf', 'cf', 'sf', 'of').
        """
        if name not in self._flags:
            raise KeyError(f"Unknown flag: {name!r}")
        return self._flags[name]

    def set_flags(self, result: int, carry: bool = False, overflow: bool = False) -> None:
        """Update flags based on an ALU result.

        Args:
            result: Raw (unbounded) integer result before masking.
            carry: Whether a carry occurred.
            overflow: Whether a signed overflow occurred.
        """
        masked = result & 0xFFFF_FFFF
        self._flags["zf"] = masked == 0
        self._flags["cf"] = carry
        self._flags["sf"] = bool(masked & 0x8000_0000)
        self._flags["of"] = overflow

    # ── Introspection ─────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Return a full snapshot of the register state (for AI / logging)."""
        return {
            "general": {k: self._reg[k] for k in self.GENERAL},
            "control": {k: self._reg[k] for k in self.CONTROL},
            "flags": dict(self._flags),
        }

    def reset(self) -> None:
        """Reset all registers and flags to zero."""
        for k in self._reg:
            self._reg[k] = 0
        for k in self._flags:
            self._flags[k] = False
        logger.debug("Registers reset.")

    def __repr__(self) -> str:  # pragma: no cover
        parts = [f"{k}=0x{v:08X}" for k, v in self._reg.items()]
        flags = [f"{k}={int(v)}" for k, v in self._flags.items()]
        return f"<Registers [{', '.join(parts)}] flags=[{', '.join(flags)}]>"
