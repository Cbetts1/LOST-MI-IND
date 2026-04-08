# VAI-OS Architecture

This directory contains the canonical specification for VAI-OS.

The system is built in layers:

- 00: Host constraints and independence
- 01–05: Boot, shell, AI bootstrap, virtual hardware, virtual OS core, shell integration
- 06–12: Package manager, virtual cloud, networking tools, security, AI control plane, developer tools, system services
- 13–14: UX + capability-aware boot, first-run wizard + device profile
- 15: Host-assisted fetch with self-built runtime

Each `docs/spec/*.md` file is a contract for what must exist under `/aios/` in the runtime tree.
