"""Plan de restauración: qué versión va a qué ruta, validando que nada escape de lo permitido."""
from __future__ import annotations

import os

from . import consulta
from .api import Config, Version
from .destino import dentro, registro, sin_subidas


def nombre_libre(ruta: str) -> str:
    base, extension = os.path.splitext(ruta)
    n = 2
    while os.path.lexists(f'{base} ({n}){extension}'):
        n += 1
    return f'{base} ({n}){extension}'


def _nombre_valido(nombre: str) -> bool:
    return bool(nombre) and nombre not in ('.', '..') and os.sep not in nombre and '\0' not in nombre


def trabajos(cfg: Config, cat, entradas, destino_dir, punto_id) -> list[tuple[Version, str]]:
    """Pares (versión, ruta de destino); las carpetas se expanden con su contenido en el punto."""
    resultado = []
    for entrada in entradas:
        if (destino_dir is not None and not _nombre_valido(entrada.nombre)) or not sin_subidas(entrada.ruta):
            registro.warning('Entrada ignorada por nombre o ruta no válidos: %r', entrada.ruta)
            continue
        base = entrada.ruta if destino_dir is None else os.path.join(destino_dir, entrada.nombre)
        if entrada.es_carpeta:
            punto = consulta.ultimo_punto(cat) if punto_id is None else punto_id
            for v in consulta.en_punto(cfg, cat, entrada.ruta, punto):
                resultado.append((v, os.path.join(base, os.path.relpath(v.ruta, entrada.ruta))))
        elif (version := consulta.version_de(cfg, cat, entrada)):
            resultado.append((version, base))
    return resultado


def permitido(ruta: str, bases: list[str]) -> bool:
    """El destino, resueltos los enlaces, debe quedar dentro de la carpeta elegida o de una protegida."""
    if sin_subidas(ruta) and any(dentro(base, ruta) for base in bases):
        return True
    registro.warning('Restauración ignorada, el destino queda fuera de lo permitido: %r', ruta)
    return False
