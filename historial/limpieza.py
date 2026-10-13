"""Limpieza filtrada por categoría y/o carpeta. Borra con retencion._borrar, que valida cada ruta
contra Datos (sin '..', sin rutas absolutas, sin enlaces que escapen): una fila envenenada no toca el disco."""
from __future__ import annotations

import os
import sqlite3
import time

from . import catalogo, destino, estado, retencion
from .tipos import categoria_de


def _en_carpeta(ruta: str, carpeta: str) -> bool:
    return ruta == carpeta or ruta.startswith(carpeta.rstrip(os.sep) + os.sep)


def _candidatas(cat, anteriores_a_dias: int | None, incluso_la_ultima: bool):
    condiciones, args = [], []
    if not incluso_la_ultima:
        condiciones.append(retencion.NO_ULTIMA)
    if anteriores_a_dias is not None:
        condiciones.append('v.mtime_ns < ?')
        args.append(int((time.time() - anteriores_a_dias * 86400) * 1e9))
    donde = ' WHERE ' + ' AND '.join(condiciones) if condiciones else ''
    return cat.db.execute(f'SELECT id, ruta, archivo, tam FROM versiones v{donde} ORDER BY id', args).fetchall()


def limpiar_filtrado(cfg, categoria: str | None = None, carpeta: str | None = None,
                     anteriores_a_dias: int | None = None, incluso_la_ultima: bool = False) -> int:
    """Borra versiones de esa categoría y/o carpeta; por defecto conserva la más reciente de cada
    archivo. Devuelve los bytes liberados (0 si el destino no está conectado)."""
    if not estado.conectado(cfg):
        return 0
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return 0
    carpeta = os.path.normpath(carpeta) if carpeta else None
    try:
        filas = [f for f in _candidatas(cat, anteriores_a_dias, incluso_la_ultima)
                 if (categoria is None or categoria_de(f['ruta']) == categoria)
                 and (carpeta is None or _en_carpeta(f['ruta'], carpeta))]
        liberado = retencion._borrar(cfg, cat, filas)[0]
        retencion._podar_puntos(cat)
        cat.db.commit()
        try:
            cat.exportar(destino.catalogo_remoto(cfg))
        except (OSError, sqlite3.Error):
            pass
        return liberado
    finally:
        cat.db.close()
