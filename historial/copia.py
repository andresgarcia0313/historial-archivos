"""Copia incremental: solo lo nuevo o cambiado (tamaño o mtime_ns), atómica y con sello UTC."""
from __future__ import annotations

import os
import sqlite3
import time

from . import bloqueo, catalogo, destino, escaneo, escritura, estado, retencion, tipos
from .api import Config, Resumen


def _trabajar(cfg: Config, cat, progreso, resumen: Resumen) -> None:
    marca = time.time()
    punto, anterior = cat.iniciar()
    hasta = anterior if anterior is not None else punto - 1
    vigentes = cat.vigentes()
    excluir = {os.path.normpath(x) for x in cfg.excluir} | {os.path.normpath(destino.raiz_historial(cfg))}
    limite = cfg.max_tam_mb * (1 << 20)
    se_copia = tipos.filtro(cfg)
    vistos, inseguros, pendientes, escaneadas = set(), [], [], []
    if progreso:
        progreso('Buscando cambios', 0.0)
    for carpeta in map(os.path.normpath, cfg.carpetas):
        if not os.path.isdir(carpeta):
            resumen.errores.append(f'No existe la carpeta {carpeta}')
            continue
        escaneadas.append(carpeta)
        for ruta, info in escaneo.recorrer(carpeta, excluir, cfg.patrones, inseguros):
            resumen.revisados += 1
            vistos.add(ruta)                   # filtrado por tipo sigue existiendo: no se da por borrado
            if not se_copia(ruta):
                continue
            if escaneo.cambio(ruta, info, vigentes) and not (limite and info.st_size > limite):
                pendientes.append((ruta, info))
    escritura.copiar_pendientes(cfg, cat, pendientes, vigentes, punto, hasta, resumen, marca, progreso)
    borradas = escaneo.desaparecidos(vigentes, vistos, escaneadas, inseguros)
    cat.cerrar(borradas, hasta)
    dejo_punto = cat.terminar(punto, resumen.copiados, len(borradas), len(resumen.errores))
    cat.poner_meta('raiz', destino.raiz_equipo(cfg))
    cat.poner_meta('ultima_copia', time.time())
    cat.poner_meta('error', resumen.errores[0] if resumen.errores else '')
    cat.db.commit()
    resumen.punto_id = punto if dejo_punto else (anterior or 0)
    retencion.aplicar(cfg, cat)
    try:
        cat.exportar(destino.catalogo_remoto(cfg))
    except (OSError, sqlite3.Error) as error:
        resumen.errores.append(f'Catálogo no copiado al destino: {error}')


def ejecutar(cfg: Config, progreso=None) -> Resumen:
    resumen = Resumen(0, 0, 0, 0)
    if not estado.conectado(cfg):
        resumen.errores.append(estado.MENSAJE_RECONECTAR if cfg.destino else estado.MENSAJE_SIN_DESTINO)
        return resumen
    with bloqueo.tomar() as libre:
        if not libre:
            resumen.errores.append('Ya hay una copia en curso')
            return resumen
        cat = catalogo.abrir(cfg)
        try:
            _trabajar(cfg, cat, progreso, resumen)
        finally:
            cat.db.close()
    return resumen


def guardar_archivos(cfg: Config, rutas: list[str]) -> int:
    """Versiona ahora los archivos dados si cambiaron (los usa restaurar antes de reemplazar)."""
    cat = catalogo.abrir(cfg)
    try:
        punto, anterior = cat.iniciar()
        vigentes, resumen = cat.vigentes(), Resumen(punto, 0, 0, 0)
        pendientes = [(r, os.lstat(r)) for r in rutas if os.path.isfile(r)]
        pendientes = [(r, i) for r, i in pendientes if escaneo.cambio(r, i, vigentes)]
        hasta = anterior if anterior is not None else punto - 1
        escritura.copiar_pendientes(cfg, cat, pendientes, vigentes, punto, hasta, resumen, time.time())
        cat.terminar(punto, resumen.copiados, 0, 0)
        cat.db.commit()
        return resumen.copiados
    finally:
        cat.db.close()
