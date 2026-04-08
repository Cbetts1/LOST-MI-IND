"""
Built-in shell commands for VAI-OS shell.
Each command is a callable returning a string result.
The COMMANDS dict maps command names to their handler functions.
"""
import logging
import time

logger = logging.getLogger(__name__)

# Kernel reference injected at shell startup
_kernel = None


def _set_kernel(kernel) -> None:
    """Inject the kernel reference used by commands."""
    global _kernel  # noqa: PLW0603
    _kernel = kernel


# ------------------------------------------------------------------
# Command implementations
# ------------------------------------------------------------------

def _cmd_help(args: list[str]) -> str:
    """Display available commands."""
    lines = ["VAI-OS Built-in Commands", "=" * 40]
    for name, fn in sorted(COMMANDS.items()):
        doc = (fn.__doc__ or "").strip().splitlines()[0]
        lines.append(f"  {name:<12} {doc}")
    return "\n".join(lines)


def _cmd_ls(args: list[str]) -> str:
    """List directory contents."""
    if _kernel is None:
        return "Error: kernel not available"
    fs = _kernel.get_subsystem("filesystem")
    if fs is None:
        return "Error: filesystem not available"
    path = args[0] if args else "/"
    try:
        entries = fs.ls(path)
        return "\n".join(entries) if entries else "(empty)"
    except Exception as exc:
        return f"ls: {exc}"


def _cmd_cat(args: list[str]) -> str:
    """Display file contents."""
    if not args:
        return "Usage: cat <path>"
    if _kernel is None:
        return "Error: kernel not available"
    fs = _kernel.get_subsystem("filesystem")
    if fs is None:
        return "Error: filesystem not available"
    try:
        return fs.read(args[0])
    except Exception as exc:
        return f"cat: {exc}"


def _cmd_ps(args: list[str]) -> str:
    """List running processes."""
    if _kernel is None:
        return "Error: kernel not available"
    pm = _kernel.get_subsystem("process_mgr")
    if pm is None:
        return "Error: process_mgr not available"
    procs = pm.list_procs()
    if not procs:
        return "No processes running"
    lines = [f"{'PID':<6} {'STATE':<10} {'MEM(MB)':<10} NAME"]
    lines.append("-" * 40)
    for p in procs:
        lines.append(
            f"{p['pid']:<6} {p['state']:<10} {p['mem_mb']:<10.1f} {p['name']}"
        )
    return "\n".join(lines)


def _cmd_df(args: list[str]) -> str:
    """Show filesystem usage (stub)."""
    return "Filesystem      Size    Used    Avail   Use%\n/dev/vda0       1G      256M    768M    25%"


def _cmd_free(args: list[str]) -> str:
    """Show memory usage."""
    if _kernel is None:
        return "Error: kernel not available"
    ram = _kernel.get_subsystem("ram")
    if ram is None:
        return "Error: ram subsystem not available"
    s = ram.get_stats()
    lines = [
        f"{'':>16} {'total':>10} {'used':>10} {'free':>10}",
        f"{'Mem:':>16} {s['total_mb']:>10.0f} {s['used_mb']:>10.1f} {s['free_mb']:>10.1f}",
    ]
    return "\n".join(lines)


def _cmd_ifconfig(args: list[str]) -> str:
    """Show network interface configuration."""
    if _kernel is None:
        return "Error: kernel not available"
    nic = _kernel.get_subsystem("nic")
    if nic is None:
        return "Error: nic subsystem not available"
    s = nic.get_stats()
    return (
        f"eth0: flags=UP,BROADCAST,RUNNING\n"
        f"      inet {s['ip']}  netmask 255.255.255.0\n"
        f"      ether {s['mac']}\n"
        f"      RX packets {s['packets_received']}  bytes {s['bytes_received']}\n"
        f"      TX packets {s['packets_sent']}  bytes {s['bytes_sent']}"
    )


def _cmd_ping(args: list[str]) -> str:
    """Ping a virtual host."""
    if not args:
        return "Usage: ping <host>"
    from aios.tools.net.ping import ping as _ping
    result = _ping(args[0])
    return (
        f"PING {result['host']}: {result['sent']} packets transmitted, "
        f"{result['received']} received, rtt avg {result['rtt_ms_avg']:.1f}ms"
    )


def _cmd_pkg(args: list[str]) -> str:
    """Package manager interface. Usage: pkg <install|remove|search|list> [name]"""
    if not args:
        return "Usage: pkg <install|remove|search|list> [name]"
    if _kernel is None:
        return "Error: kernel not available"
    pm = _kernel.get_subsystem("pkg_mgr")
    if pm is None:
        return "Error: pkg_mgr not available"
    subcmd = args[0]
    name = args[1] if len(args) > 1 else None
    if subcmd == "install" and name:
        ok = pm.install(name)
        return f"Package '{name}' {'installed' if ok else 'not found or failed'}."
    if subcmd == "remove" and name:
        ok = pm.remove(name)
        return f"Package '{name}' {'removed' if ok else 'not found'}."
    if subcmd == "search" and name:
        results = pm.search(name)
        if not results:
            return f"No packages matching '{name}'"
        return "\n".join(f"  {r['name']} {r.get('version','')}" for r in results)
    if subcmd == "list":
        installed = pm.list_installed()
        if not installed:
            return "No packages installed"
        return "\n".join(f"  {p['name']} {p.get('version','')}" for p in installed)
    return f"pkg: unknown sub-command '{subcmd}'"


def _cmd_cloud(args: list[str]) -> str:
    """Cloud control. Usage: cloud <nodes|scale|status>"""
    if not args:
        return "Usage: cloud <nodes|scale|status>"
    if _kernel is None:
        return "Error: kernel not available"
    nm = _kernel.get_subsystem("node_manager")
    if nm is None:
        return "Error: node_manager not available"
    subcmd = args[0]
    if subcmd == "nodes":
        nodes = nm.list_nodes()
        if not nodes:
            return "No cloud nodes"
        lines = [f"{'ID':<20} {'TYPE':<12} {'STATUS'}"]
        for n in nodes:
            lines.append(f"{n.node_id:<20} {n.node_type:<12} {n.status}")
        return "\n".join(lines)
    if subcmd == "status":
        scaler = _kernel.get_subsystem("scaler")
        if scaler:
            return str(scaler.get_cluster_stats())
        return "Scaler not available"
    return f"cloud: unknown sub-command '{subcmd}'"


def _cmd_ai(args: list[str]) -> str:
    """AI inference interface. Usage: ai <prompt...>"""
    if not args:
        return "Usage: ai <prompt>"
    if _kernel is None:
        return "Error: kernel not available"
    engine = _kernel.get_subsystem("ai_engine")
    if engine is None:
        return "Error: ai_engine not available"
    prompt = " ".join(args)
    result = engine.infer("default", prompt, {})
    return result.get("response", "(no response)")


def _cmd_exit(args: list[str]) -> str:
    """Exit the shell."""
    raise SystemExit(0)


def _cmd_clear(args: list[str]) -> str:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")
    return ""


def _cmd_whoami(args: list[str]) -> str:
    """Print current user."""
    return "root"


def _cmd_uname(args: list[str]) -> str:
    """Print system information."""
    return "VAI-OS 0.1.0 virtual #1 SMP Python"


def _cmd_top(args: list[str]) -> str:
    """Show top processes by memory usage."""
    if _kernel is None:
        return "Error: kernel not available"
    pm = _kernel.get_subsystem("process_mgr")
    cpu = _kernel.get_subsystem("cpu")
    ram = _kernel.get_subsystem("ram")
    procs = sorted(
        pm.list_procs() if pm else [],
        key=lambda p: p["mem_mb"],
        reverse=True,
    )[:10]
    cpu_s = cpu.get_stats() if cpu else {}
    ram_s = ram.get_stats() if ram else {}
    lines = [
        f"CPU: {cpu_s.get('usage_pct', 0):.1f}%  "
        f"RAM: {ram_s.get('used_mb', 0):.1f}/{ram_s.get('total_mb', 0):.0f} MB",
        f"{'PID':<6} {'MEM(MB)':<10} NAME",
        "-" * 30,
    ]
    for p in procs:
        lines.append(f"{p['pid']:<6} {p['mem_mb']:<10.1f} {p['name']}")
    return "\n".join(lines)


# ------------------------------------------------------------------
# Command registry
# ------------------------------------------------------------------

COMMANDS: dict[str, callable] = {
    "help": _cmd_help,
    "ls": _cmd_ls,
    "cat": _cmd_cat,
    "ps": _cmd_ps,
    "df": _cmd_df,
    "free": _cmd_free,
    "ifconfig": _cmd_ifconfig,
    "ping": _cmd_ping,
    "pkg": _cmd_pkg,
    "cloud": _cmd_cloud,
    "ai": _cmd_ai,
    "exit": _cmd_exit,
    "clear": _cmd_clear,
    "whoami": _cmd_whoami,
    "uname": _cmd_uname,
    "top": _cmd_top,
}
