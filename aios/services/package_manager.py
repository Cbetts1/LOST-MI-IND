"""
VAI-OS Package Manager
Termux-compatible virtual package manager with install/remove/search/upgrade.
Architecture: index stored in VirtualFS; packages are Python-module stubs.
"""
import logging
import time

logger = logging.getLogger(__name__)

_BUILTIN_INDEX = {
    "vaios-core": {"version": "0.1.0", "deps": [], "description": "VAI-OS core utilities"},
    "vaios-net": {"version": "0.1.0", "deps": ["vaios-core"], "description": "Network tools"},
    "vaios-dev": {"version": "0.1.0", "deps": ["vaios-core"], "description": "Developer tools"},
    "vaios-ai": {"version": "0.1.0", "deps": ["vaios-core"], "description": "AI engine extras"},
    "vaios-cloud": {"version": "0.1.0", "deps": ["vaios-core"], "description": "Cloud utilities"},
    "vaios-security": {"version": "0.1.0", "deps": ["vaios-core"], "description": "Security tools"},
    "python3": {"version": "3.11.0", "deps": [], "description": "Python 3 runtime"},
    "curl": {"version": "7.88.0", "deps": [], "description": "HTTP client"},
    "git": {"version": "2.40.0", "deps": [], "description": "Version control"},
    "nano": {"version": "7.2.0", "deps": [], "description": "Text editor"},
    "vim": {"version": "9.0.0", "deps": [], "description": "Advanced text editor"},
    "htop": {"version": "3.2.2", "deps": [], "description": "Process monitor"},
    "ssh": {"version": "9.3.0", "deps": [], "description": "Secure shell client"},
    "tmux": {"version": "3.3.0", "deps": [], "description": "Terminal multiplexer"},
}


class PackageManager:
    """Virtual package manager modelled after Termux/apt."""

    def __init__(self, filesystem=None):
        self.filesystem = filesystem
        self.installed: dict = {}
        self.available: dict = dict(_BUILTIN_INDEX)

    def update_index(self) -> int:
        """Refresh package index. Returns package count."""
        self.available = dict(_BUILTIN_INDEX)
        logger.info("Package index updated: %d packages", len(self.available))
        return len(self.available)

    def install(self, name: str, version: str = None) -> bool:
        """Install a package by name."""
        if name in self.installed:
            logger.info("Package '%s' already installed", name)
            return True
        if name not in self.available:
            logger.warning("Package '%s' not found in index", name)
            return False
        pkg = self.available[name]
        # Install dependencies first
        for dep in pkg.get("deps", []):
            if dep not in self.installed:
                self.install(dep)
        self.installed[name] = {
            "version": version or pkg["version"],
            "installed_at": time.time(),
            "files": [f"/aios/pkg/{name}/"],
            "deps": pkg.get("deps", []),
        }
        logger.info("Installed %s==%s", name, self.installed[name]["version"])
        return True

    def remove(self, name: str) -> bool:
        """Remove an installed package."""
        if name not in self.installed:
            logger.warning("Package '%s' not installed", name)
            return False
        del self.installed[name]
        logger.info("Removed package '%s'", name)
        return True

    def search(self, query: str) -> list:
        """Search available packages by name or description."""
        q = query.lower()
        results = []
        for name, info in self.available.items():
            if q in name.lower() or q in info.get("description", "").lower():
                results.append({"name": name, **info})
        return results

    def list_installed(self) -> list:
        return [{"name": n, **v} for n, v in self.installed.items()]

    def upgrade(self, name: str = None) -> list:
        """Upgrade one or all packages."""
        upgraded = []
        targets = [name] if name else list(self.installed.keys())
        for pkg_name in targets:
            if pkg_name in self.available:
                new_ver = self.available[pkg_name]["version"]
                old_ver = self.installed.get(pkg_name, {}).get("version", "")
                if old_ver != new_ver:
                    self.installed[pkg_name]["version"] = new_ver
                    upgraded.append(pkg_name)
                    logger.info("Upgraded %s: %s -> %s", pkg_name, old_ver, new_ver)
        return upgraded
