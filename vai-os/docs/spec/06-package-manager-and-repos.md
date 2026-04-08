### 5.0 Package Manager + Repository Layer

The package manager installs, updates, and removes VAI-OS components.

Components:

1. Package Manager Core
Files:
- `core/pkg/manager.py`
- `core/pkg/registry.json`

Requirements:
- install/remove/list packages
- dependency resolution
- versioning
- package metadata

2. Build System
Files:
- `tools/build_system.py`
- `tools/build-all.sh`

Requirements:
- build packages from source
- Python-based build pipeline
- no host compiler dependency
- integrate with AI builder agent

3. Repository System
Files:
- `core/pkg/repos.py`

Requirements:
- local repo under `/aios/pkg/`
- remote repo support (optional)
- host-assisted fetch allowed but not required

4. Package Format
Files:
- `.vpk` (VAI-OS Package)

Requirements:
- tar/zip archive
- metadata.json
- install script
- uninstall script

Expected output:
[VAI-OS] Package Manager Online
