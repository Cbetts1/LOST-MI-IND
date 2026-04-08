### 4.0 Shell Integration Layer

The shell is the primary user interface for VAI-OS.

Components:

1. Shell Entry
Files:
- `shell/aios.sh`
- `shell/main.py`

Requirements:
- numbered interactive shell
- command mode (bash, python, aios)
- AI-assisted command suggestions
- help integration

2. Menus
Files:
- `shell/menus/*.py`

Menus required:
- Filesystem
- Network & Cloud
- Virtual Hardware
- AI & Models
- Packages & Tools
- System Status & Logs
- Developer Tools
- Device Profile
- Command Mode

3. Command Parser
Files:
- `shell/parser.py`

Requirements:
- parse commands
- route to subsystems
- integrate with AI controller for ambiguous commands

4. Shell Status Bar
Files:
- `shell/ui/status_bar.py`

Requirements:
- show AI status
- cloud status
- security status
- mode (LIGHT/BALANCED/HEAVY)

Expected output:
[VAI-OS] Shell Online
