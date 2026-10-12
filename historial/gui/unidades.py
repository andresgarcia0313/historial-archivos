"""Detección de unidades externas y ubicaciones de red ya montadas."""
import os
import re
import shutil
import sys
from dataclasses import dataclass

TIPOS_RED = {'nfs', 'nfs4', 'cifs', 'smb3', 'smbfs', 'fuse.sshfs', 'davfs', 'fuse.rclone', 'afpfs'}
RAICES_LINUX = ('/media/', '/run/media/', '/mnt/')


@dataclass
class Unidad:
    nombre: str
    ruta: str
    libre: int
    total: int


def _leer_montajes() -> str:
    try:
        with open('/proc/mounts', encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return ''


def _desescapar(ruta: str) -> str:
    return re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), ruta)


def _rutas_linux(texto: str) -> list[str]:
    rutas = []
    for linea in texto.splitlines():
        campos = linea.split()
        if len(campos) < 3:
            continue
        ruta, tipo = _desescapar(campos[1]), campos[2]
        if ruta.startswith(RAICES_LINUX) or tipo in TIPOS_RED:
            rutas.append(ruta)
    return rutas


def _rutas_macos() -> list[str]:
    try:
        nombres = os.listdir('/Volumes')
    except OSError:
        return []
    rutas = [os.path.join('/Volumes', n) for n in nombres]
    return [r for r in rutas if not os.path.islink(r)]


def detectar(texto_montajes: str | None = None, plataforma: str | None = None) -> list[Unidad]:
    """Unidades montadas con espacio legible. Los parámetros permiten probarlo sin tocar el sistema."""
    if (plataforma or sys.platform) == 'darwin':
        rutas = _rutas_macos()
    else:
        rutas = _rutas_linux(_leer_montajes() if texto_montajes is None else texto_montajes)
    unidades = []
    for ruta in dict.fromkeys(rutas):
        try:
            uso = shutil.disk_usage(ruta)
        except OSError:
            continue
        unidades.append(Unidad(os.path.basename(ruta) or ruta, ruta, uso.free, uso.total))
    return unidades
