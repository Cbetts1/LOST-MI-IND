"""
CommandCenter: A numbered menu-driven interface for VAI-OS providing
an interactive system overview dashboard and subsystem panels.
"""
import logging

logger = logging.getLogger(__name__)

_MENU = [
    ("System Overview", None),
    ("Virtual Hardware Monitor", None),
    ("Cloud Control Panel", None),
    ("AI Control Panel", None),
    ("Network Status", None),
    ("Security Dashboard", None),
    ("Package Manager", None),
    ("Developer Tools", None),
    ("System Services", None),
    ("Exit", None),
]


class CommandCenter:
    """Interactive numbered-menu command center for VAI-OS."""

    def __init__(self, kernel):
        self._kernel = kernel
        logger.info("CommandCenter initialized")

    # ------------------------------------------------------------------
    # Menu panels
    # ------------------------------------------------------------------

    def _panel_overview(self) -> str:
        """Build the System Overview panel."""
        k = self._kernel
        stats = k.get_stats()
        cpu = k.get_subsystem("cpu")
        ram = k.get_subsystem("ram")
        lines = [
            "┌─ System Overview ──────────────────────────┐",
            f"│ VAI-OS v{stats['version']:<38}│",
            f"│ Uptime:  {stats['uptime_s']:<38.2f}│",
            f"│ Subsystems: {stats['subsystem_count']:<35}│",
        ]
        if cpu:
            cs = cpu.get_stats()
            lines.append(f"│ CPU: {cs['cores']} cores @ {cs['clock_hz']//1_000_000}MHz  usage={cs['usage_pct']}%{'':<9}│")
        if ram:
            rs = ram.get_stats()
            lines.append(f"│ RAM: {rs['used_mb']:.0f}/{rs['total_mb']:.0f} MB used ({rs['usage_pct']}%){'':<14}│")
        lines.append("└────────────────────────────────────────────┘")
        return "\n".join(lines)

    def _panel_hardware(self) -> str:
        """Build the Virtual Hardware Monitor panel."""
        k = self._kernel
        cpu = k.get_subsystem("cpu")
        ram = k.get_subsystem("ram")
        io = k.get_subsystem("io")
        lines = ["── Virtual Hardware Monitor ──"]
        if cpu:
            s = cpu.get_stats()
            lines.append(f"  CPU  cores={s['cores']}  clock={s['clock_hz']//1_000_000}MHz  usage={s['usage_pct']}%")
        if ram:
            s = ram.get_stats()
            lines.append(f"  RAM  total={s['total_mb']}MB  used={s['used_mb']}MB  free={s['free_mb']}MB")
        if io:
            s = io.get_stats()
            lines.append(f"  IO   devices={list(s['devices'].keys())}")
        return "\n".join(lines)

    def _panel_cloud(self) -> str:
        """Build the Cloud Control Panel."""
        nm = self._kernel.get_subsystem("node_manager")
        if nm is None:
            return "  Cloud: node_manager not available"
        nodes = nm.list_nodes()
        lines = [f"── Cloud Control Panel ({len(nodes)} nodes) ──"]
        for n in nodes[:10]:
            lines.append(f"  {n.node_id:<20} {n.node_type:<12} {n.status}")
        if not nodes:
            lines.append("  (no nodes)")
        return "\n".join(lines)

    def _panel_ai(self) -> str:
        """Build the AI Control Panel."""
        engine = self._kernel.get_subsystem("ai_engine")
        if engine is None:
            return "  AI Engine: not available"
        s = engine.get_stats()
        controller = self._kernel.get_subsystem("ai_controller")
        agents = list(controller.agents.keys()) if controller else []
        lines = [
            "── AI Control Panel ──",
            f"  Initialized: {s.get('initialized', False)}",
            f"  Models: {s.get('model_count', 0)}",
            f"  Total inferences: {s.get('total_inferences', 0)}",
            f"  Agents: {', '.join(agents) if agents else 'none'}",
        ]
        return "\n".join(lines)

    def _panel_network(self) -> str:
        """Build the Network Status panel."""
        nic = self._kernel.get_subsystem("nic")
        fw = self._kernel.get_subsystem("firewall")
        lines = ["── Network Status ──"]
        if nic:
            s = nic.get_stats()
            lines.append(f"  NIC  ip={s['ip']}  mac={s['mac']}  up={s['up']}")
            lines.append(f"       RX={s['packets_received']}  TX={s['packets_sent']}")
        if fw:
            s = fw.get_stats()
            lines.append(f"  FW   rules={s['rule_count']}  allowed={s['allowed']}  denied={s['denied']}")
        return "\n".join(lines)

    def _panel_security(self) -> str:
        """Build the Security Dashboard."""
        audit = self._kernel.get_subsystem("audit_log")
        perm = self._kernel.get_subsystem("permission_mgr")
        lines = ["── Security Dashboard ──"]
        if perm:
            lines.append(f"  Subjects with policies: {len(perm.policies)}")
        if audit:
            recent = audit.tail(5)
            lines.append(f"  Recent audit events ({len(recent)}):")
            for e in recent:
                lines.append(
                    f"    [{e.get('event_type','?')}] {e.get('subject','?')} -> "
                    f"{e.get('resource','?')} : {e.get('outcome','?')}"
                )
        return "\n".join(lines)

    def _panel_packages(self) -> str:
        """Build the Package Manager panel."""
        pm = self._kernel.get_subsystem("pkg_mgr")
        if pm is None:
            return "  Package Manager: not available"
        installed = pm.list_installed()
        lines = [f"── Package Manager ({len(installed)} installed) ──"]
        for p in installed[:10]:
            lines.append(f"  {p['name']:<20} {p.get('version','')}")
        if not installed:
            lines.append("  (none installed)")
        return "\n".join(lines)

    def _panel_devtools(self) -> str:
        """Build the Developer Tools panel."""
        return (
            "── Developer Tools ──\n"
            "  builder   BuildSystem: compile/link stubs\n"
            "  debugger  Breakpoints, step, inspect\n"
            "  profiler  Profile functions\n"
            "  linter    Check syntax"
        )

    def _panel_services(self) -> str:
        """Build the System Services panel."""
        dm = self._kernel.get_subsystem("daemon_mgr")
        ts = self._kernel.get_subsystem("timer_svc")
        lines = ["── System Services ──"]
        if dm:
            daemons = dm.list_daemons()
            lines.append(f"  Daemons ({len(daemons)}):")
            for d in daemons[:5]:
                lines.append(f"    {d['name']:<20} {d['status']}")
        if ts:
            timers = ts.list_timers()
            lines.append(f"  Timers ({len(timers)}):")
            for t in timers[:5]:
                lines.append(f"    {t['name']:<20} interval={t['interval_s']}s")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Display the numbered menu with system status overview."""
        print("\n" + self._panel_overview())
        print("\n┌─ Command Center ─────────────────────────┐")
        for idx, (label, _) in enumerate(_MENU):
            print(f"│  {idx}. {label:<41}│")
        print("└───────────────────────────────────────────┘")

    def run(self) -> None:
        """
        Start the interactive Command Center loop.

        Displays the menu, reads numeric selection, and delegates to panels.
        Handles Ctrl+C gracefully.
        """
        logger.info("CommandCenter run loop started")
        _panels = [
            self._panel_overview,
            self._panel_hardware,
            self._panel_cloud,
            self._panel_ai,
            self._panel_network,
            self._panel_security,
            self._panel_packages,
            self._panel_devtools,
            self._panel_services,
        ]
        while True:
            try:
                self.show()
                choice_raw = input("\nSelect option: ").strip()
            except KeyboardInterrupt:
                print("\n(Ctrl+C — returning to shell)")
                break
            except EOFError:
                break

            if not choice_raw.isdigit():
                print("Please enter a number.")
                continue

            choice = int(choice_raw)
            if choice == len(_MENU) - 1:
                print("Exiting Command Center.")
                break
            if 0 <= choice < len(_panels):
                print()
                print(_panels[choice]())
            else:
                print(f"Invalid option: {choice}")
