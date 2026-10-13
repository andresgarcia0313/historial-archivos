"""Timeshift: lectura de /etc/timeshift/timeshift.json (cambiarla necesita administrador)."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime

from . import CopiaDetectada
from .comun import texto_frecuencia

RUTAS = ('/etc/timeshift/timeshift.json', '/etc/timeshift.json')
SNAPSHOTS = ('/run/timeshift/backup/timeshift/snapshots', '/timeshift/snapshots')
NIVELES = (('hourly', 60), ('daily', 1440), ('weekly', 10080), ('monthly', 43200))


def _si(valor) -> bool:
    return str(valor).lower() == 'true'


def frecuencia(cfg: dict) -> tuple[bool, int | None, str]:
    for nivel, minutos in NIVELES:
        if _si(cfg.get(f'schedule_{nivel}')):
            return True, minutos, texto_frecuencia(minutos)
    if _si(cfg.get('schedule_boot')):
        return True, None, 'Al iniciar el equipo'
    return False, None, 'Manual'


def destino(uuid: str) -> str:
    if not uuid:
        return ''
    enlace = f'/dev/disk/by-uuid/{uuid}'
    return os.path.realpath(enlace) if os.path.exists(enlace) else f'UUID={uuid}'


def ultima() -> datetime | None:
    for carpeta in SNAPSHOTS:
        try:
            nombres = sorted(n for n in os.listdir(carpeta) if re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', n))
        except OSError:
            continue
        if nombres:
            return datetime.strptime(nombres[-1][:19], '%Y-%m-%d_%H-%M-%S')
    return None


def detectar() -> list[CopiaDetectada]:
    for ruta in RUTAS:
        try:
            with open(ruta, encoding='utf-8') as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(cfg, dict):
            continue
        activa, minutos, texto = frecuencia(cfg)
        btrfs = _si(cfg.get('btrfs_mode'))
        carpetas = ['/'] + (['/home'] if _si(cfg.get('include_btrfs_home_for_backup')) else [])
        return [CopiaDetectada(
            id='timeshift:sistema', herramienta='Timeshift',
            nombre='Instantáneas del sistema (BTRFS)' if btrfs else 'Instantáneas del sistema (RSYNC)',
            activa=activa, destino=destino(str(cfg.get('backup_device_uuid', ''))), frecuencia=texto,
            frecuencia_min=minutos, carpetas=carpetas, excluir=list(cfg.get('exclude') or []),
            ultima=ultima(), editable=False, nota='necesita permisos de administrador')]
    return []


def tamano(c: CopiaDetectada) -> int | None:
    return None
