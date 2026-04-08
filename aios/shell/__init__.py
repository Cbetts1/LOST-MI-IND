"""
Shell Integration Layer package.
Exposes VAIOSShell, AIRepl, CommandCenter, and COMMANDS registry.
"""
from .shell import VAIOSShell
from .repl import AIRepl
from .command_center import CommandCenter
from .commands import COMMANDS

__all__ = ["VAIOSShell", "AIRepl", "CommandCenter", "COMMANDS"]
