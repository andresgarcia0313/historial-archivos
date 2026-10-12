"""Retención y limpieza. Nunca se borra la versión más reciente de cada archivo."""
from __future__ import annotations

import os
import shutil
import sqlite3
import time

from . import catalogo, destino, estado
from .api import Config

LIBRE_MINIMO = 0.10
NO_ULTIMA = 'EXISTS (SELECT 1 FROM versiones w WHERE w.ruta = v.ruta AND w.id > v.id)'


def _quitar_vacias(carpeta: str, tope: str) -> None:
    while carpeta.startswith(tope + os.sep):
        try:
            os.rmdir(carpeta)
        except OSError:
            return
        carpeta = os.path.dirname(carpeta)


def _borrar(cfg: Config, cat, filas) -> tuple[int, int]:
    """Borra copias y filas. Devuelve (bytes liberados, versiones borradas)."""
    datos = destino.carpeta_datos(cfg)
    liberado, ids = 0, []
    for fila in filas:
        ruta = os.path.join(datos, fila['archivo'])
        try:
            os.unlink(ruta)
        except FileNotFoundError:
            pass
        except OSError:
            continue
        ids.append((fila['id'],))
        liberado += fila['tam']
        _quitar_vacias(os.path.dirname(ruta), datos)
    cat.db.executemany('DELETE FROM versiones WHERE id=?', ids)
    return liberado, len(ids)


def _podar_puntos(cat) -> None:
    """Quita los puntos anteriores a toda versión que aún existe (quedarían vacíos)."""
    cat.db.execute("DELETE FROM ejecuciones WHERE estado='ok' AND id < (SELECT MIN(desde) FROM versiones)")


def _eliminar_antiguas(cfg: Config, cat, dias: int | None) -> int:
    condicion, args = NO_ULTIMA, ()
    if dias is not None:
        condicion += ' AND v.mtime_ns < ?'
        args = (int((time.time() - dias * 86400) * 1e9),)
    filas = cat.db.execute(f'SELECT id, archivo, tam FROM versiones v WHERE {condicion} ORDER BY id', args).fetchall()
    return _borrar(cfg, cat, filas)[0]


def _liberar_espacio(cfg: Config, cat) -> None:
    """Modo 'hasta que se necesite espacio': borra las más antiguas hasta tener 10 % libre."""
    while True:
        uso = shutil.disk_usage(cfg.destino)
        if uso.total == 0 or uso.free / uso.total >= LIBRE_MINIMO:
            return
        filas = cat.db.execute(f'SELECT id, archivo, tam FROM versiones v WHERE {NO_ULTIMA} '
                               'ORDER BY id LIMIT 1').fetchall()
        if not filas or _borrar(cfg, cat, filas)[1] == 0:
            return


def aplicar(cfg: Config, cat) -> None:
    """Retención configurada, al final de cada copia."""
    if cfg.conservar_dias > 0:
        _eliminar_antiguas(cfg, cat, cfg.conservar_dias)
    elif cfg.conservar_dias == -1:
        _liberar_espacio(cfg, cat)
    _podar_puntos(cat)
    cat.db.commit()


def limpiar(cfg: Config, anteriores_a_dias: int | None) -> int:
    """Limpiar versiones: None = todas menos la más reciente. Devuelve bytes liberados."""
    if not estado.conectado(cfg):
        return 0
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return 0
    try:
        liberado = _eliminar_antiguas(cfg, cat, anteriores_a_dias)
        _podar_puntos(cat)
        cat.db.commit()
        try:
            cat.exportar(destino.catalogo_remoto(cfg))
        except (OSError, sqlite3.Error):
            pass
        return liberado
    finally:
        cat.db.close()
