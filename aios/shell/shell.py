"""
VAIOSShell: Interactive shell for VAI-OS providing a command-line REPL
with history, banner display, and graceful Ctrl+C handling.
"""
import logging
import sys

from .commands import COMMANDS, _set_kernel

logger = logging.getLogger(__name__)

_BANNER = r"""
 __   ___   _    ___     ___  ____
 \ \ / / | | |  |_ _|  / _ \/ ___|
  \ V /| |_| |   | |  | | | \___ \
   \_/ |____/   |___|  |_| |_|___/

  Virtual AI-Native Operating System v0.1.0
  Type 'help' for available commands.
"""


class VAIOSShell:
    """VAI-OS interactive command shell."""

    def __init__(self, kernel):
        self._kernel = kernel
        self.history: list[str] = []
        _set_kernel(kernel)
        logger.info("VAIOSShell initialized")

    def _print_banner(self) -> None:
        """Print the shell welcome banner."""
        print(_BANNER)

    def execute_command(self, line: str) -> str:
        """
        Parse and execute a single command line.

        Returns the string result of the command.
        """
        line = line.strip()
        if not line:
            return ""
        self.history.append(line)

        parts = line.split()
        cmd_name = parts[0]
        args = parts[1:]

        if cmd_name in COMMANDS:
            try:
                result = COMMANDS[cmd_name](args)
                return result or ""
            except SystemExit:
                raise
            except Exception as exc:
                logger.error("Command %r raised: %s", cmd_name, exc)
                return f"Error: {exc}"
        return f"Command not found: {cmd_name!r}. Type 'help' for commands."

    def run_loop(self) -> None:
        """
        Start the interactive shell loop.

        Reads input, executes commands, and prints results.
        Handles Ctrl+C gracefully (continues loop) and Ctrl+D (exits).
        """
        self._print_banner()
        while True:
            try:
                line = input("[VAI-OS]$ ")
            except KeyboardInterrupt:
                print("\n(Use 'exit' to quit)")
                continue
            except EOFError:
                print("\nBye!")
                break

            try:
                result = self.execute_command(line)
                if result:
                    print(result)
            except SystemExit:
                print("Goodbye!")
                break
            except Exception as exc:
                logger.error("Shell loop error: %s", exc)
                print(f"Shell error: {exc}")
