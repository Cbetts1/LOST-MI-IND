### 0.0 Host Independence Constraint

You must treat the host (Android, Linux, macOS, Windows, WSL, Termux) as a **dumb execution shell only**.

1. No Host Tooling Dependency
   - Do NOT rely on:
     - host `git`
     - host `ssh`
     - host `curl`
     - host compilers (`gcc`, `clang`, etc.)
     - host package managers (`apt`, `brew`, `pkg`, `winget`, etc.)
   - If such tools exist, they are OPTIONAL accelerators, never requirements.

2. Self-Contained Toolchain
   - VAI-OS must provide its own:
     - minimal git-compatible client (pure Python or bundled binary)
     - minimal HTTP client (Python sockets/requests)
     - minimal SSH client (pure Python library or bundled)
     - build system (Python-based, no external compiler assumed unless explicitly bundled)
   - All critical functionality must work with:
     - Python standard library
     - files stored under `/aios`
     - virtual hardware + virtual OS only

3. Internal Build Pipeline
   - All "build" operations (packages, services, tools, OS modules) must:
     - run entirely inside VAI-OS
     - use only:
       - Python
       - bundled interpreters
       - bundled compilers (if any)
       - virtual hardware abstractions
   - If a native compiler is not available, you must:
     - prefer interpreted tools
     - generate Python-based tools
     - or use prebuilt binaries stored under `/aios/tools/`

4. Host as Transport Only
   - The host may:
     - launch `boot/launch-*.sh` or `.ps1`
     - provide CPU, RAM, and I/O
   - The host may NOT be required to:
     - install packages
     - provide system libraries
     - provide dev tools
     - provide network tools

5. Termux / Host Integration Reframed
   - Any mention of Termux or host integration is:
     - strictly OPTIONAL
     - treated as "bonus acceleration" if present
   - Core logic must always have a **pure VAI-OS path** that does not call host tools.

Result:
- VAI-OS must be **bootable, usable, and build-capable** on a bare host with:
  - Python + `/aios` tree only
  - no external package managers
  - no external compilers
  - no external git/ssh/curl.
