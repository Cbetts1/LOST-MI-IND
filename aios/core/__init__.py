"""
VAI-OS Core kernel package.
Exposes VAIOSKernel, ProcessManager, VirtualFS, SyscallDispatcher, RoundRobinScheduler.
"""
from .kernel import VAIOSKernel
from .process import ProcessManager
from .filesystem import VirtualFS
from .syscall import SyscallDispatcher
from .scheduler import RoundRobinScheduler

__all__ = [
    "VAIOSKernel",
    "ProcessManager",
    "VirtualFS",
    "SyscallDispatcher",
    "RoundRobinScheduler",
]
