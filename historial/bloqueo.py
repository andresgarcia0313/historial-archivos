"""Exclusión mutua entre ejecuciones con fcntl.flock."""
from __future__ import annotations

import fcntl
from contextlib import contextmanager

from . import config


@contextmanager
def tomar():
    """Entrega True si obtuvo el bloqueo (y lo suelta al salir), False si otra copia corre."""
    config.dir_datos().mkdir(parents=True, exist_ok=True)
    archivo = open(config.dir_datos() / 'ejecucion.lock', 'a+')
    try:
        fcntl.flock(archivo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        obtenido = True
    except OSError:
        obtenido = False
    try:
        yield obtenido
    finally:
        if obtenido:
            fcntl.flock(archivo, fcntl.LOCK_UN)
        archivo.close()


def ocupado() -> bool:
    with tomar() as obtenido:
        return not obtenido
