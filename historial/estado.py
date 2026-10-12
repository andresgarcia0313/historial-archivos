"""Estado del destino y de la última copia."""
from __future__ import annotations

import os
import shutil
from datetime import datetime

from . import bloqueo, catalogo, config, destino
from .api import Config, Estado

MENSAJE_RECONECTAR = 'Reconecte la unidad'
MENSAJE_SIN_DESTINO = 'Seleccione una unidad'


def conectado(cfg: Config) -> bool:
    """El destino existe y, si ya había historial en él, sigue estando (no es un montaje vacío)."""
    if not cfg.destino or not os.path.isdir(cfg.destino):
        return False
    if os.path.isdir(destino.raiz_equipo(cfg)):
        return True
    local = config.ruta_catalogo()
    return not (local.exists() and catalogo.raiz_guardada(local) == destino.raiz_equipo(cfg))


def estado(cfg: Config) -> Estado:
    en_curso = bloqueo.ocupado()
    ok = conectado(cfg)
    resultado = Estado(cfg.activo, ok, None, 0, 0, 0, '', en_curso)
    if not cfg.destino:
        resultado.error = MENSAJE_SIN_DESTINO
        return resultado
    if not ok:
        resultado.error = MENSAJE_RECONECTAR
    else:
        uso = shutil.disk_usage(cfg.destino)
        resultado.libre, resultado.total = uso.free, uso.total
    cat = catalogo.abrir(cfg, crear=False)
    if cat is not None:
        marca = cat.meta('ultima_copia')
        resultado.ultima_copia = datetime.fromtimestamp(float(marca)) if marca else None
        resultado.tam_copias = cat.db.execute('SELECT COALESCE(SUM(tam), 0) FROM versiones').fetchone()[0]
        resultado.error = resultado.error or cat.meta('error', '')
    return resultado
