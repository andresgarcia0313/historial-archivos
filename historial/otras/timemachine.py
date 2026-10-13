"""Time Machine (macOS): destinos y última copia con tmutil; solo lectura."""
from __future__ import annotations

import re
import sys
from datetime import datetime

from . import CopiaDetectada
from .comun import ejecutar

PREFERENCIAS = '/Library/Preferences/com.apple.TimeMachine'


def destinos(texto: str) -> list[dict[str, str]]:
    """Bloques 'Clave : valor' de `tmutil destinationinfo`, separados por líneas de guiones."""
    bloques, actual = [], {}
    for linea in texto.splitlines():
        if linea.startswith('=') or linea.startswith('-'):
            if actual:
                bloques.append(actual)
            actual = {}
        elif ':' in linea:
            clave, valor = linea.split(':', 1)
            actual[clave.strip()] = valor.strip()
    if actual:
        bloques.append(actual)
    return [b for b in bloques if b.get('Name') or b.get('ID')]


def fecha(ruta: str | None) -> datetime | None:
    m = re.search(r'(\d{4}-\d{2}-\d{2}-\d{6})', ruta or '')
    return datetime.strptime(m.group(1), '%Y-%m-%d-%H%M%S') if m else None


def detectar() -> list[CopiaDetectada]:
    if sys.platform != 'darwin':
        return []
    info = ejecutar(['tmutil', 'destinationinfo'])
    if not info:
        return []
    automatica = (ejecutar(['defaults', 'read', PREFERENCIAS, 'AutoBackup']) or '').strip() in ('1', 'true')
    ultima = fecha(ejecutar(['tmutil', 'latestbackup']))
    copias = []
    for d in destinos(info):
        punto = d.get('Mount Point', '')
        copias.append(CopiaDetectada(
            id=f"timemachine:{d.get('ID') or d.get('Name')}", herramienta='Time Machine',
            nombre=d.get('Name', 'Time Machine'), activa=automatica,
            destino=punto or d.get('URL', '') or d.get('Name', ''),
            frecuencia='Cada hora' if automatica else 'Manual',
            frecuencia_min=60 if automatica else None, carpetas=['/'], ultima=ultima,
            editable=False, nota='' if punto else 'destino desconectado'))
    return copias


def tamano(c: CopiaDetectada) -> int | None:
    return None
