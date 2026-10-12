"""Disposición de las copias en el destino y nombres con sello UTC estilo Windows."""
from __future__ import annotations

import getpass
import logging
import os
import socket
import time

from .api import Config

registro = logging.getLogger('historial')


def _usuario() -> str:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return 'usuario'


def raiz_historial(cfg: Config) -> str:
    return os.path.join(cfg.destino, 'HistorialArchivos')


def raiz_equipo(cfg: Config) -> str:
    return os.path.join(raiz_historial(cfg), _usuario(), socket.gethostname())


def carpeta_datos(cfg: Config) -> str:
    return os.path.join(raiz_equipo(cfg), 'Datos')


def catalogo_remoto(cfg: Config) -> str:
    return os.path.join(raiz_equipo(cfg), 'Configuracion', 'catalogo.sqlite')


def sin_subidas(ruta: str) -> bool:
    """True si la ruta no trae NUL ni componentes '..' (el catálogo puede venir de un destino ajeno)."""
    return '\0' not in ruta and '..' not in ruta.replace('\\', '/').split('/')


def dentro(base: str, ruta: str) -> bool:
    """True si `ruta`, resueltos los enlaces simbólicos, queda dentro de `base`."""
    base, real = os.path.realpath(base), os.path.realpath(ruta)
    return real == base or real.startswith(base.rstrip(os.sep) + os.sep)


def copia_segura(cfg: Config, relativa: str) -> str | None:
    """Ruta absoluta de una copia si queda dentro de Datos; si no, la registra y devuelve None."""
    datos = carpeta_datos(cfg)
    if relativa and not os.path.isabs(relativa) and sin_subidas(relativa):
        ruta = os.path.join(datos, relativa)
        if dentro(datos, ruta):
            return ruta
    registro.warning('Copia ignorada, queda fuera de Datos: %r', relativa)
    return None


def sello_utc(marca: float) -> str:
    return time.strftime('%Y_%m_%d %H_%M_%S UTC', time.gmtime(marca))


def nombre_con_sello(nombre: str, sello: str) -> str:
    """'informe.txt' -> 'informe (2026_10_12 15_30_00 UTC).txt'."""
    base, extension = os.path.splitext(nombre)
    return f'{base} ({sello}){extension}'


def copia_libre(cfg: Config, ruta: str, marca: float) -> tuple[str, str]:
    """Devuelve (sello, ruta relativa a Datos) sin pisar una copia existente."""
    carpeta, nombre = os.path.split(ruta.lstrip(os.sep))
    datos = carpeta_datos(cfg)
    while True:
        sello = sello_utc(marca)
        relativa = os.path.join(carpeta, nombre_con_sello(nombre, sello))
        if not os.path.lexists(os.path.join(datos, relativa)):
            return sello, relativa
        marca += 1
