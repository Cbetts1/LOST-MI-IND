"""
HelpAgent: AI agent providing user assistance and documentation lookup
for VAI-OS subsystems, commands, and concepts.
"""
import logging

logger = logging.getLogger(__name__)

KNOWLEDGE: dict[str, str] = {
    "shell": (
        "The VAI-OS shell supports built-in commands: help, ls, cat, ps, df, "
        "free, ifconfig, ping, pkg, cloud, ai, exit, clear, whoami, uname, top."
    ),
    "kernel": (
        "The VAIOSKernel manages subsystem registration, boot, and shutdown. "
        "Access subsystems via kernel.get_subsystem(name)."
    ),
    "filesystem": (
        "VirtualFS is an in-memory filesystem. Use mkdir, write, read, ls, exists, rm."
    ),
    "cloud": (
        "Cloud layer provides CloudNode, CloudNodeManager, CloudScaler, "
        "ComputeService, StorageService, MessageBus, AIInferenceService."
    ),
    "ai": (
        "AIEngine provides simulated inference. Use infer(model, prompt, context) "
        "to query models. Models are registered in ModelRegistry."
    ),
    "security": (
        "Security layer: PermissionManager for RBAC, Sandbox for isolation, "
        "AuditLog for event tracking."
    ),
    "networking": (
        "Virtual network: VirtualNIC, VirtualRouter, VirtualFirewall, "
        "PublicIPAbstraction. Tools: ping, traceroute, netstat, ifconfig, curl."
    ),
    "packages": (
        "PackageManager: install/remove/search/list packages. "
        "Use 'pkg install <name>' in the shell."
    ),
    "boot": (
        "Boot sequence: DeviceProfile.detect_capabilities() -> UXLayer.adapt_to_device() "
        "-> Bootloader.stage1/2() -> Kernel.boot() -> BootBrain.run_boot_sequence()."
    ),
    "processes": (
        "ProcessManager: spawn(name, mem_mb), kill(pid), list_procs(). "
        "Use 'ps' in shell to view processes."
    ),
}


class HelpAgent:
    """AI agent providing contextual help and documentation."""

    def __init__(self):
        self._metrics: dict = {"queries": 0, "misses": 0}
        logger.info("HelpAgent initialized with %d topics", len(KNOWLEDGE))

    def start(self) -> None:
        """Activate the help agent."""
        logger.info("HelpAgent started")

    def stop(self) -> None:
        """Deactivate the help agent."""

    def answer(self, question: str) -> str:
        """
        Answer a user question by searching the knowledge base.

        Returns the best-matching help text or a default message.
        """
        self._metrics["queries"] += 1
        question_lower = question.lower()

        # Direct topic match
        for topic, text in KNOWLEDGE.items():
            if topic in question_lower:
                logger.debug("HelpAgent.answer: matched topic=%s", topic)
                return f"[{topic.upper()}] {text}"

        # Keyword search within knowledge values
        for topic, text in KNOWLEDGE.items():
            for word in question_lower.split():
                if len(word) > 3 and word in text.lower():
                    return f"[{topic.upper()}] {text}"

        self._metrics["misses"] += 1
        available = ", ".join(sorted(KNOWLEDGE.keys()))
        return (
            f"I don't have specific information about that. "
            f"Available topics: {available}"
        )

    def list_topics(self) -> list[str]:
        """Return a sorted list of available help topics."""
        return sorted(KNOWLEDGE.keys())
