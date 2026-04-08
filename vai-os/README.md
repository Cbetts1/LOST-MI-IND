# VAI-OS

VAI-OS is a virtual, AI-native operating system designed to run from a portable rootfs (e.g. SD card) on arbitrary hosts.

Core principles:
- Host-agnostic: host is just CPU/RAM/I/O and an optional source fetcher.
- Self-contained: all critical tools live under `/aios`, not the host.
- AI-native: AI control plane is a first-class system brain.
- Virtualized: CPU, memory, storage, NIC, bus, and cloud are all virtual hardware.
- Operator-grade: numbered shell, command mode, AI help, logging, metrics, security.

See `docs/README-ARCHITECTURE.md` and `docs/spec/*.md` for the full architecture.
