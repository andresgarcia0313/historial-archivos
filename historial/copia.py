"""Copia incremental: solo lo nuevo o cambiado (tamaño o mtime_ns), atómica y con sello UTC."""
from __future__ import annotations

import errno
import os
import shutil
import sqlite3
import time

from . import bloqueo, catalogo, destino, escaneo, estado, retencion
from .api import Config, Resumen


def copiar_archivo(origen: str, info: os.stat_result, final: str) -> None:
    """Copia a `final.part`, conserva la fecha de modificación y renombra (atómico)."""
    os.makedirs(os.path.dirname(final), exist_ok=True)
    parcial = final + '.part'
    try:
        with open(origen, 'rb') as entrada, open(parcial, 'wb') as salida:
            shutil.copyfileobj(entrada, salida, 1 << 20)
        os.utime(parcial, ns=(info.st_atime_ns, info.st_mtime_ns))
        os.replace(parcial, final)
    except BaseException:
        try:
            os.unlink(parcial)
        except OSError:
            pass
        raise


def _cambio(ruta: str, info: os.stat_result, vigentes: dict) -> bool:
    previa = vigentes.get(ruta)
    return previa is None or previa[1:] != (info.st_size, info.st_mtime_ns)


def _desaparecidos(vigentes: dict, vistos: set, escaneadas: list, inseguros: list) -> list[int]:
    """Versiones vigentes de archivos que ya no están, salvo bajo zonas ilegibles o montajes."""
    raices = tuple(c.rstrip(os.sep) + os.sep for c in escaneadas)
    veto = tuple(i.rstrip(os.sep) + os.sep for i in inseguros)
    sueltos = set(inseguros)
    return [v[0] for ruta, v in vigentes.items()
            if ruta not in vistos and ruta.startswith(raices) and ruta not in sueltos
            and not ruta.startswith(veto)]


def _copiar(cfg, cat, pendientes, vigentes, punto, hasta, resumen, marca, progreso) -> None:
    datos = destino.carpeta_datos(cfg)
    for i, (ruta, info) in enumerate(pendientes, 1):
        if progreso:
            progreso(ruta, i / len(pendientes))
        sello, relativa = destino.copia_libre(cfg, ruta, marca)
        try:
            copiar_archivo(ruta, info, os.path.join(datos, relativa))
        except OSError as error:
            resumen.errores.append(f'{ruta}: {error.strerror or error}')
            if error.errno == errno.ENOSPC:
                break
            continue
        if ruta in vigentes:
            cat.cerrar([vigentes[ruta][0]], hasta)
        cat.agregar(ruta, sello, info.st_size, info.st_mtime_ns, relativa, punto)
        resumen.copiados += 1
        resumen.bytes_copiados += info.st_size
        if i % 200 == 0:
            cat.db.commit()


def _trabajar(cfg: Config, cat, progreso, resumen: Resumen) -> None:
    marca = time.time()
    punto, anterior = cat.iniciar()
    hasta = anterior if anterior is not None else punto - 1
    vigentes = cat.vigentes()
    excluir = {os.path.normpath(x) for x in cfg.excluir} | {os.path.normpath(destino.raiz_historial(cfg))}
    limite = cfg.max_tam_mb * (1 << 20)
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
            vistos.add(ruta)
            if _cambio(ruta, info, vigentes) and not (limite and info.st_size > limite):
                pendientes.append((ruta, info))
    _copiar(cfg, cat, pendientes, vigentes, punto, hasta, resumen, marca, progreso)
    borradas = _desaparecidos(vigentes, vistos, escaneadas, inseguros)
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
        pendientes = [(r, i) for r, i in pendientes if _cambio(r, i, vigentes)]
        hasta = anterior if anterior is not None else punto - 1
        _copiar(cfg, cat, pendientes, vigentes, punto, hasta, resumen, time.time(), None)
        cat.terminar(punto, resumen.copiados, 0, 0)
        cat.db.commit()
        return resumen.copiados
    finally:
        cat.db.close()
