### 2.1 Virtual Hardware Bring-Up (CPU, Memory, Storage, NIC)

After the AI engine bootstrap is implemented, build the virtual hardware bring-up layer. This layer initializes all virtual hardware components and exposes them to the OS and AI.

1. Virtual CPU Initialization
Files:
- `virt/cpu/isa.json`
- `virt/cpu/interpreter.py`
- `virt/cpu/registers.py`
- `virt/cpu/pipeline.py`

Requirements:
- load instruction set from `isa.json`
- init registers (general, control, flags)
- init pipeline (fetch, decode, execute)
- expose CPU state to OS via hardware API
- expose CPU state to AI via `hardware_agent.py`

Expected output:
[VAI-OS] Virtual CPU: initialized
ISA loaded: <arch>
