### 1.0 Boot Flow + Shell Entry

Define the boot scripts and shell entry that bring VAI-OS online from the SD-card rootfs.

Boot scripts under `boot/` must:
- detect `/aios` root
- start Python runtime
- launch AI engine bootstrap
- launch shell entry

Shell entry:
- `shell/aios.sh` as the main entry point
- numbered interactive shell by default
- command mode (bash/aios/python) as an option

The shell must show:

- system status (AI engine, virtual hardware, OS core)
- menus for:
  - filesystem & storage
  - network & cloud
  - virtual hardware
  - AI & models
  - packages & tools
  - system status & logs
  - command mode
