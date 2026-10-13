"""Déjà Dup: lectura y escritura de su configuración en gsettings (org.gnome.DejaDup)."""
from __future__ import annotations

import ast
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from . import CopiaDetectada
from .comun import du, ejecutar, texto_frecuencia

ESQUEMA = 'org.gnome.DejaDup'
ID = 'dejadup:principal'
DESTINOS = {'local': ('Local', 'folder'), 'remote': ('Remote', 'uri'), 'drive': ('Drive', 'folder'),
            'google': ('Google', 'folder'), 'microsoft': ('Microsoft', 'folder')}


def leer(clave: str, esquema: str = ESQUEMA):
    """Valor de gsettings convertido a Python; None si la clave o el esquema no existen."""
    salida = ejecutar(['gsettings', 'get', esquema, clave])
    if salida is None:
        return None
    texto = salida.strip()
    for prefijo in ('@as ', 'uint32 ', 'int32 '):
        texto = texto.removeprefix(prefijo)
    texto = {'true': 'True', 'false': 'False'}.get(texto, texto)
    try:
        return ast.literal_eval(texto)
    except (ValueError, SyntaxError):
        return texto


def _casa(ruta: str) -> str:
    return ruta.replace('$HOME', str(Path.home()), 1) if ruta.startswith('$HOME') else ruta


def _a_variable(ruta: str) -> str:
    casa = str(Path.home())
    return '$HOME' + ruta[len(casa):] if ruta == casa or ruta.startswith(casa + '/') else ruta


def destino(backend: str) -> str:
    esquema, clave = DESTINOS.get(backend, ('Local', 'folder'))
    valor = leer(clave, f'{ESQUEMA}.{esquema}') or ''
    return valor if backend == 'remote' else f'{backend}:{valor}' if backend != 'local' else _casa(valor)


def detectar() -> list[CopiaDetectada]:
    if leer('periodic') is None or not (shutil.which('deja-dup') or leer('last-backup')):
        return []
    dias = int(leer('periodic-period') or 7)
    activa = bool(leer('periodic'))
    backend = str(leer('backend') or 'local')
    try:
        ultima = datetime.fromisoformat(str(leer('last-backup') or '')).astimezone().replace(tzinfo=None)
    except ValueError:
        ultima = None
    return [CopiaDetectada(
        id=ID, herramienta='Déjà Dup', nombre='Copia de seguridad', activa=activa,
        destino=destino(backend), frecuencia=texto_frecuencia(dias * 1440 if activa else None),
        frecuencia_min=dias * 1440, carpetas=[_casa(r) for r in leer('include-list') or []],
        excluir=[_casa(r) for r in leer('exclude-list') or []], ultima=ultima, editable=True,
        nota='' if backend in ('local', 'remote', 'drive') else 'destino en la nube')]


def _respaldar() -> str:
    copia = Path.home() / '.config' / 'historial-archivos' / f'dejadup.gsettings.bak-{int(time.time())}'
    copia.parent.mkdir(parents=True, exist_ok=True)
    copia.write_text(ejecutar(['gsettings', 'list-recursively', ESQUEMA]) or '', encoding='utf-8')
    return str(copia)


def guardar(c: CopiaDetectada) -> None:
    """Respalda los valores actuales y escribe los nuevos; lanza RuntimeError si gsettings falla."""
    _respaldar()
    dias = max(1, (c.frecuencia_min or 1440) // 1440)
    cambios = [('periodic', 'true' if c.activa else 'false'), ('periodic-period', str(dias)),
               ('include-list', _lista(c.carpetas)), ('exclude-list', _lista(c.excluir))]
    for clave, valor in cambios:
        if ejecutar(['gsettings', 'set', ESQUEMA, clave, valor]) is None:
            raise RuntimeError(f'gsettings no aceptó {clave}')


def _lista(rutas: list[str]) -> str:
    """Lista de cadenas en formato GVariant (la vacía necesita el tipo explícito)."""
    return repr([_a_variable(r) for r in rutas]) if rutas else '@as []'


def tamano(c: CopiaDetectada) -> int | None:
    return du(c.destino) if os.path.isabs(c.destino) else None
