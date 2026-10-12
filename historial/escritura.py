"""Escritura de copias en el destino: atómica (.part y rename) y conservando la fecha."""
from __future__ import annotations

import errno
import os
import shutil

from . import destino
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


def copiar_pendientes(cfg: Config, cat, pendientes, vigentes, punto, hasta, resumen: Resumen,
                      marca: float, progreso=None) -> None:
    """Copia cada pendiente, cierra la versión que reemplaza y registra la nueva en el catálogo."""
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
