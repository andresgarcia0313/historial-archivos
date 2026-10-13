"""Utilidades compartidas por los detectores: texto de frecuencia, órdenes acotadas, du y respaldos."""
from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import time
from datetime import datetime

RED = {'autofs', 'nfs', 'nfs4', 'cifs', 'smb3', 'smbfs', 'afpfs', 'webdav', 'davfs', 'fuse.sshfs',
       'fuse.rclone', 'fuse.gvfsd-fuse', 'fuse.s3fs', '9p'}
MONTAJES = '/proc/mounts'


def texto_frecuencia(minutos: int | None) -> str:
    """Texto legible para una frecuencia en minutos (None = sin programar)."""
    if not minutos:
        return 'Manual'
    nombres = {60: 'Cada hora', 1440: 'Diaria', 10080: 'Semanal', 43200: 'Mensual'}
    if minutos in nombres:
        return nombres[minutos]
    if minutos < 60:
        return f'Cada {minutos} minutos'
    if minutos % 1440 == 0:
        return f'Cada {minutos // 1440} días'
    if minutos % 60 == 0:
        return f'Cada {minutos // 60} horas'
    return f'Cada {minutos} minutos'


def ejecutar(orden: list[str], timeout: float = 2.0, entrada: str | None = None) -> str | None:
    """Salida estándar de la orden, o None si no existe, falla o tarda más de la cuenta."""
    try:
        hecho = subprocess.run(orden, capture_output=True, text=True, timeout=timeout,
                               input=entrada, check=False)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return hecho.stdout if hecho.returncode == 0 else None


def du(ruta: str) -> int | None:
    """Bytes ocupados por la ruta (sin cruzar sistemas de archivos); None si no se puede medir."""
    if not ruta or es_de_red(ruta) or not os.path.isdir(ruta):
        return None
    salida = ejecutar(['du', '-sxk', ruta], timeout=900)
    try:
        return int(salida.split()[0]) * 1024 if salida else None
    except (ValueError, IndexError):
        return None


def respaldar(ruta: str) -> str:
    """Copia la configuración original junto a ella como <ruta>.bak-<epoch> y devuelve esa ruta."""
    copia = f'{ruta}.bak-{int(time.time())}'
    shutil.copy2(ruta, copia)
    return copia


def puntos_de_red() -> set[str]:
    """Puntos de montaje de red o FUSE remotos: tocarlos puede colgar sin conexión."""
    try:
        with open(MONTAJES, encoding='utf-8') as f:
            lineas = f.read().splitlines()
    except OSError:
        return set()
    partes = (linea.split() for linea in lineas)
    return {_decodificar(p[1]) for p in partes if len(p) > 2 and p[2] in RED}


def es_de_red(ruta: str, red: set[str] | None = None) -> bool:
    red = puntos_de_red() if red is None else red
    ruta = os.path.abspath(ruta)
    return any(ruta == m or ruta.startswith(m.rstrip('/') + '/') for m in red)


def ultima_catalogo(catalogo: str) -> datetime | None:
    """Marca 'ultima_copia' de un catálogo de esta app, abierto en solo lectura."""
    if not os.path.isfile(catalogo):
        return None
    try:
        con = sqlite3.connect(f'file:{catalogo}?mode=ro', uri=True, timeout=1)
        fila = con.execute("SELECT valor FROM meta WHERE clave='ultima_copia'").fetchone()
        con.close()
        return datetime.fromtimestamp(float(fila[0])) if fila and fila[0] else None
    except (sqlite3.Error, ValueError, OSError):
        return None


def _decodificar(campo: str) -> str:
    return campo.replace('\\040', ' ').replace('\\011', '\t').replace('\\134', '\\')
