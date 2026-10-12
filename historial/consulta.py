"""Consultas de solo lectura: puntos, listados por punto y versiones de un archivo."""
from __future__ import annotations

import os
from datetime import datetime

from . import catalogo, destino
from .api import Config, Entrada, Punto, Version

_EN_PUNTO = 'desde <= ? AND (hasta IS NULL OR hasta >= ?)'


def _fecha(mtime_ns: int) -> datetime:
    return datetime.fromtimestamp(mtime_ns / 1e9)


def a_version(cfg: Config, fila) -> Version | None:
    """None si la fila no es de fiar: ruta original no absoluta o con '..', o copia fuera de Datos."""
    ruta = fila['ruta']
    archivo = destino.copia_segura(cfg, fila['archivo'])
    if archivo is None or not os.path.isabs(ruta) or not destino.sin_subidas(ruta):
        return None
    return Version(fila['id'], ruta, _fecha(fila['mtime_ns']), fila['tam'], archivo)


def _validas(cfg: Config, filas) -> list[Version]:
    return [v for v in (a_version(cfg, f) for f in filas) if v is not None]


def puntos(cfg: Config) -> list[Punto]:
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return []
    filas = cat.db.execute("SELECT id, fin FROM ejecuciones WHERE estado='ok' ORDER BY id")
    return [Punto(f['id'], datetime.fromtimestamp(f['fin'] or 0)) for f in filas]


def ultimo_punto(cat) -> int:
    return cat.db.execute("SELECT COALESCE(MAX(id), 0) FROM ejecuciones WHERE estado='ok'").fetchone()[0]


def _bajo(carpeta: str) -> tuple[str, str]:
    """Rango [inicio, fin) de las rutas que cuelgan de la carpeta."""
    prefijo = carpeta.rstrip('/') + '/'
    return prefijo, prefijo[:-1] + '0'


def en_punto(cfg: Config, cat, carpeta: str, punto: int) -> list[Version]:
    """Todas las versiones bajo una carpeta que existían en el punto."""
    inicio, fin = _bajo(carpeta)
    filas = cat.db.execute(f'SELECT * FROM versiones WHERE ruta >= ? AND ruta < ? AND {_EN_PUNTO}',
                           (inicio, fin, punto, punto))
    return _validas(cfg, filas)


def listar(cfg: Config, punto_id: int, carpeta: str) -> list[Entrada]:
    if carpeta == '':
        return [Entrada(os.path.basename(c.rstrip('/')) or c, c, True) for c in cfg.carpetas]
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return []
    inicio, _ = _bajo(carpeta)
    carpetas: dict[str, Entrada] = {}
    archivos: list[Entrada] = []
    for v in en_punto(cfg, cat, carpeta, punto_id):
        nombre, _, resto = v.ruta[len(inicio):].partition('/')
        if resto:
            carpetas.setdefault(nombre, Entrada(nombre, inicio + nombre, True))
        else:
            archivos.append(Entrada(nombre, v.ruta, False, v.tam, v.fecha, v.id))
    orden = lambda e: e.nombre.lower()
    return sorted(carpetas.values(), key=orden) + sorted(archivos, key=orden)


def versiones(cfg: Config, ruta: str) -> list[Version]:
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return []
    filas = cat.db.execute('SELECT * FROM versiones WHERE ruta=? ORDER BY id DESC', (ruta,))
    return _validas(cfg, filas)


def version_de(cfg: Config, cat, entrada: Entrada) -> Version | None:
    """La versión elegida en la entrada o, si no trae, la más reciente de esa ruta."""
    if entrada.version_id is not None:
        fila = cat.db.execute('SELECT * FROM versiones WHERE id=?', (entrada.version_id,)).fetchone()
    else:
        fila = cat.db.execute('SELECT * FROM versiones WHERE ruta=? ORDER BY id DESC', (entrada.ruta,)).fetchone()
    return a_version(cfg, fila) if fila else None
