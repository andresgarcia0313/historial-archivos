"""Copias de esta aplicación: la configurada aquí y las carpetas HistorialArchivos de unidades conectadas."""
from __future__ import annotations

import getpass
import os
import socket
from dataclasses import replace

from . import CopiaDetectada
from .comun import du, es_de_red, puntos_de_red, texto_frecuencia
from .comun import ultima_catalogo as _ultima

HERRAMIENTA = 'Historial de archivos'
PROPIA = 'historial:propia'
BASES = ('/media', '/run/media', '/mnt', '/Volumes')


def propia() -> list[CopiaDetectada]:
    from .. import config, destino
    cfg = config.cargar()
    if not cfg.destino:
        return []
    return [CopiaDetectada(
        id=PROPIA, herramienta=HERRAMIENTA, nombre='Esta aplicación', activa=cfg.activo,
        destino=cfg.destino, frecuencia=texto_frecuencia(cfg.frecuencia_min if cfg.activo else None),
        frecuencia_min=cfg.frecuencia_min, carpetas=list(cfg.carpetas), excluir=list(cfg.excluir),
        ultima=_ultima(str(config.ruta_catalogo())), editable=True,
        nota='' if os.path.isdir(destino.raiz_equipo(cfg)) else 'destino desconectado')]


def unidades(red: set[str]) -> list[str]:
    """Raíces candidatas: /mnt/x, /Volumes/x, /media/x y /media/<usuario>/x, sin montajes de red."""
    raices = []
    for base in BASES:
        for nombre in _hijos(base, red):
            ruta = os.path.join(base, nombre)
            raices.append(ruta)
            if os.path.basename(base) == 'media':  # /media/<usuario>/<unidad>, /run/media/<usuario>/<unidad>
                raices += [os.path.join(ruta, n) for n in _hijos(ruta, red)]
    return raices


def _hijos(carpeta: str, red: set[str]) -> list[str]:
    if es_de_red(carpeta, red):
        return []
    try:
        nombres = sorted(os.listdir(carpeta))
    except OSError:
        return []
    return [n for n in nombres if not es_de_red(os.path.join(carpeta, n), red)]


def encontradas(excluir: str = '') -> list[CopiaDetectada]:
    red, copias = puntos_de_red(), []
    yo, equipo_local = getpass.getuser(), socket.gethostname()
    for raiz in unidades(red):
        base = os.path.join(raiz, 'HistorialArchivos')
        for usuario in _hijos(base, red):
            for equipo in _hijos(os.path.join(base, usuario), red):
                ruta = os.path.join(base, usuario, equipo)
                if not os.path.isdir(ruta) or os.path.realpath(ruta) == excluir:
                    continue
                mia = usuario == yo and equipo == equipo_local
                copias.append(CopiaDetectada(
                    id=f'historial:{ruta}', herramienta=HERRAMIENTA, nombre=f'{equipo} ({usuario})',
                    activa=False, destino=raiz, frecuencia='Manual', frecuencia_min=None,
                    ultima=_ultima(os.path.join(ruta, 'Configuracion', 'catalogo.sqlite')),
                    nota='copia de este equipo: puede reutilizarla como destino' if mia
                    else 'copia de otro equipo'))
    return copias


def detectar() -> list[CopiaDetectada]:
    from .. import config, destino
    mias = propia()
    actual = os.path.realpath(destino.raiz_equipo(config.cargar())) if mias else ''
    return mias + encontradas(actual)


def guardar(c: CopiaDetectada) -> None:
    from .. import config
    cfg = config.cargar()
    config.guardar(replace(cfg, activo=c.activa, frecuencia_min=c.frecuencia_min or cfg.frecuencia_min,
                           carpetas=list(c.carpetas), excluir=list(c.excluir)))


def tamano(c: CopiaDetectada) -> int | None:
    from .. import config, destino
    return du(destino.raiz_equipo(config.cargar()) if c.id == PROPIA else c.id.split(':', 1)[1])
