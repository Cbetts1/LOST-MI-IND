"""
HardwareAgent: AI agent that monitors and optimizes VAI-OS virtual hardware
resources including CPU, RAM, and I/O subsystems.
"""
import logging

logger = logging.getLogger(__name__)


class HardwareAgent:
    """AI agent for virtual hardware monitoring and optimization."""

    def __init__(self, cpu, ram, io):
        self._cpu = cpu
        self._ram = ram
        self._io = io
        self._active = False
        self._metrics: dict = {"analyze_calls": 0, "optimize_calls": 0}
        logger.info("HardwareAgent initialized")

    def start(self) -> None:
        """Activate the hardware agent."""
        self._active = True
        logger.info("HardwareAgent started")

    def stop(self) -> None:
        """Deactivate the hardware agent."""
        self._active = False
        logger.info("HardwareAgent stopped")

    def analyze(self) -> dict:
        """
        Analyze current hardware resource utilization.

        Returns a dict with cpu, ram, and io metrics.
        """
        self._metrics["analyze_calls"] += 1
        cpu_stats = self._cpu.get_stats() if self._cpu else {}
        ram_stats = self._ram.get_stats() if self._ram else {}
        io_stats = self._io.get_stats() if self._io else {}

        analysis = {
            "cpu": cpu_stats,
            "ram": ram_stats,
            "io": io_stats,
            "cpu_pressure": cpu_stats.get("usage_pct", 0) > 80,
            "ram_pressure": ram_stats.get("usage_pct", 0) > 85,
        }
        logger.debug("HardwareAgent.analyze: cpu_pressure=%s ram_pressure=%s",
                     analysis["cpu_pressure"], analysis["ram_pressure"])
        return analysis

    def optimize(self) -> list[str]:
        """
        Recommend optimization actions based on current analysis.

        Returns a list of action strings.
        """
        self._metrics["optimize_calls"] += 1
        analysis = self.analyze()
        actions: list[str] = []

        if analysis["cpu_pressure"]:
            actions.append("throttle_background_tasks")
            actions.append("reduce_scheduler_frequency")

        if analysis["ram_pressure"]:
            actions.append("flush_caches")
            actions.append("swap_idle_processes")

        cpu_pct = analysis["cpu"].get("usage_pct", 0)
        ram_pct = analysis["ram"].get("usage_pct", 0)
        if cpu_pct < 10 and ram_pct < 20:
            actions.append("prefetch_common_models")

        if not actions:
            actions.append("no_action_needed")

        logger.info("HardwareAgent.optimize: actions=%s", actions)
        return actions

    def report(self) -> str:
        """Generate a human-readable hardware status report."""
        a = self.analyze()
        cpu = a.get("cpu", {})
        ram = a.get("ram", {})
        return (
            f"Hardware Report\n"
            f"  CPU: {cpu.get('cores', '?')} cores  "
            f"usage={cpu.get('usage_pct', 0):.1f}%  "
            f"{'⚠ HIGH' if a['cpu_pressure'] else 'OK'}\n"
            f"  RAM: {ram.get('used_mb', 0):.0f}/{ram.get('total_mb', 0):.0f}MB  "
            f"usage={ram.get('usage_pct', 0):.1f}%  "
            f"{'⚠ HIGH' if a['ram_pressure'] else 'OK'}"
        )
