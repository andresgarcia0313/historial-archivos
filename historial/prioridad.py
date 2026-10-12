"""Baja la prioridad del proceso de copia (CPU y, en Linux, entrada/salida)."""
from __future__ import annotations

import os
import platform
import sys

_SYSCALL_IOPRIO_SET = {'x86_64': 251, 'aarch64': 30, 'i686': 289, 'armv7l': 314, 'riscv64': 30}


def bajar() -> None:
    try:
        os.nice(19)
    except OSError:
        pass
    numero = _SYSCALL_IOPRIO_SET.get(platform.machine())
    if not sys.platform.startswith('linux') or numero is None:
        return
    try:
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        clase_idle = 3 << 13                       # IOPRIO_CLASS_IDLE
        libc.syscall(numero, 1, 0, clase_idle)     # IOPRIO_WHO_PROCESS, proceso actual
    except (OSError, AttributeError):
        pass
