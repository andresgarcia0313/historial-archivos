"""Programación sin demonio: timer de systemd --user (Linux) o LaunchAgent (macOS)."""
from __future__ import annotations

import os
import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .api import Config

ETIQUETA = 'io.github.andresgarcia0313.historial-archivos'
UNIDAD = 'historial-archivos'


def comando() -> list[str]:
    """Orden que lanza una copia, según cómo esté instalada la aplicación."""
    instalado = shutil.which('historial-archivos')
    if instalado:
        return [instalado, '--ejecutar']
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--ejecutar']
    return [sys.executable, '-m', 'historial', '--ejecutar']


def _ejecutar(*orden: str) -> None:
    """Llama a systemctl/launchctl; se omite con HISTORIAL_SIN_PROGRAMAR=1 y si el programa falta."""
    if os.environ.get('HISTORIAL_SIN_PROGRAMAR') == '1':
        return
    try:
        subprocess.run(orden, check=False, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        pass


def _systemd(cfg: Config, activar: bool) -> None:
    carpeta = Path.home() / '.config' / 'systemd' / 'user'
    servicio, temporizador = carpeta / f'{UNIDAD}.service', carpeta / f'{UNIDAD}.timer'
    if not activar:
        _ejecutar('systemctl', '--user', 'disable', '--now', f'{UNIDAD}.timer')
        servicio.unlink(missing_ok=True)
        temporizador.unlink(missing_ok=True)
        _ejecutar('systemctl', '--user', 'daemon-reload')
        return
    carpeta.mkdir(parents=True, exist_ok=True)
    servicio.write_text(
        '[Unit]\nDescription=Historial de archivos: copia de versiones\n\n'
        f'[Service]\nType=oneshot\nExecStart={shlex.join(comando())}\n'
        'Nice=19\nIOSchedulingClass=idle\nCPUWeight=20\nIOWeight=20\nMemoryMax=512M\n', encoding='utf-8')
    temporizador.write_text(
        '[Unit]\nDescription=Historial de archivos: programación\n\n'
        f'[Timer]\nOnBootSec=5min\nOnUnitActiveSec={cfg.frecuencia_min}min\nPersistent=true\n\n'
        '[Install]\nWantedBy=timers.target\n', encoding='utf-8')
    _ejecutar('systemctl', '--user', 'daemon-reload')
    _ejecutar('systemctl', '--user', 'enable', '--now', f'{UNIDAD}.timer')


def _launchd(cfg: Config, activar: bool) -> None:
    plist = Path.home() / 'Library' / 'LaunchAgents' / f'{ETIQUETA}.plist'
    dominio = f'gui/{os.getuid()}'
    _ejecutar('launchctl', 'bootout', f'{dominio}/{ETIQUETA}')
    if not activar:
        plist.unlink(missing_ok=True)
        return
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plistlib.dumps({
        'Label': ETIQUETA, 'ProgramArguments': comando(), 'StartInterval': cfg.frecuencia_min * 60,
        'RunAtLoad': True, 'Nice': 19, 'LowPriorityIO': True, 'ProcessType': 'Background'}))
    _ejecutar('launchctl', 'bootstrap', dominio, str(plist))


def aplicar(cfg: Config) -> None:
    """Crea o quita la programación según cfg.activo (y exista un destino)."""
    activar = bool(cfg.activo and cfg.destino)
    (_launchd if sys.platform == 'darwin' else _systemd)(cfg, activar)
