"""Back In Time: lectura de los perfiles de ~/.config/backintime/config (formato clave=valor)."""
from __future__ import annotations

import os
import re
import socket
from datetime import datetime
from pathlib import Path

from . import CopiaDetectada
from .backintime_modos import frecuencia, modo_actual
from .comun import du

HERRAMIENTA = 'Back In Time'
API = '/usr/share/backintime/common'


def ruta_config() -> Path:
    return Path.home() / '.config' / 'backintime' / 'config'


def ruta_datos() -> Path:
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share') / 'backintime'


def leer(ruta: Path) -> dict[str, str]:
    claves = {}
    for linea in ruta.read_text(encoding='utf-8', errors='replace').splitlines():
        if '=' in linea and not linea.lstrip().startswith('#'):
            clave, valor = linea.split('=', 1)
            claves[clave.strip()] = valor.strip()
    return claves


def _lista(cfg: dict[str, str], prefijo: str) -> list[str]:
    total = int(cfg.get(f'{prefijo}.size', '0') or 0)
    valores = (cfg.get(f'{prefijo}.{i}.value') for i in range(1, total + 1))
    return [v for v in valores if v]


def carpeta_perfil(cfg: dict[str, str], p: str, pid: str) -> str:
    """Carpeta local de las instantáneas: <ruta>/backintime/<equipo>/<usuario>/<perfil>."""
    base = cfg.get(f'{p}.snapshots.path', '')
    equipo = cfg.get(f'{p}.snapshots.path.host') or socket.gethostname()
    usuario = cfg.get(f'{p}.snapshots.path.user') or os.environ.get('USER', '')
    return os.path.join(base, 'backintime', equipo, usuario, cfg.get(f'{p}.snapshots.path.profile', pid))


def ultima(carpeta: str | None, pid: str) -> datetime | None:
    """Por el enlace last_snapshot si el destino es local; si no, por la fecha del registro."""
    if carpeta:
        try:
            m = re.match(r'(\d{8}-\d{6})', os.readlink(os.path.join(carpeta, 'last_snapshot')))
            if m:
                return datetime.strptime(m.group(1), '%Y%m%d-%H%M%S')
        except OSError:
            pass
    registro = ruta_datos() / f"takesnapshot_{'' if pid == '1' else pid}.log"
    try:
        return datetime.fromtimestamp(registro.stat().st_mtime)
    except OSError:
        return None


def _es_local(cfg: dict[str, str], p: str) -> bool:
    return cfg.get(f'{p}.snapshots.mode', 'local').startswith('local')


def perfil(cfg: dict[str, str], pid: str) -> CopiaDetectada:
    p = f'profile{pid}'
    minutos, texto = frecuencia(cfg, p)
    carpeta = carpeta_perfil(cfg, p, pid) if _es_local(cfg, p) else None
    if carpeta:
        destino = cfg.get(f'{p}.snapshots.path', '')
        nota = '' if os.path.isdir(carpeta) else 'destino desconectado'
    else:
        usuario, equipo = cfg.get(f'{p}.snapshots.ssh.user', ''), cfg.get(f'{p}.snapshots.ssh.host', '')
        destino = f"{usuario}@{equipo}:{cfg.get(f'{p}.snapshots.ssh.path', '')}"
        nota = 'destino por SSH: el tamaño no se mide sin conexión'
    return CopiaDetectada(
        id=f'backintime:{pid}', herramienta=HERRAMIENTA,
        nombre=cfg.get(f'{p}.name') or ('Perfil principal' if pid == '1' else f'Perfil {pid}'),
        activa=modo_actual(cfg, p) != 0, destino=destino, frecuencia=texto, frecuencia_min=minutos,
        carpetas=_lista(cfg, f'{p}.snapshots.include'), excluir=_lista(cfg, f'{p}.snapshots.exclude'),
        ultima=ultima(carpeta, pid), editable=os.path.isdir(API), nota=nota)


def detectar() -> list[CopiaDetectada]:
    ruta = ruta_config()
    if not ruta.is_file():
        return []
    cfg = leer(ruta)
    return [perfil(cfg, pid) for pid in (cfg.get('profiles') or '1').split(':') if pid]


def tamano(c: CopiaDetectada) -> int | None:
    pid = c.id.split(':', 1)[1]
    cfg = leer(ruta_config())
    return du(carpeta_perfil(cfg, f'profile{pid}', pid)) if _es_local(cfg, f'profile{pid}') else None
