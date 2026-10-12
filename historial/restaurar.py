"""Restauración de archivos y carpetas (recursiva) con manejo de conflictos."""
from __future__ import annotations

import os
import shutil

from . import catalogo, copia, plan
from .api import Config, Version

RESOLUCIONES = ('reemplazar', 'omitir', 'renombrar')


def _versionar_actual(cfg: Config, ruta: str) -> bool:
    """Guarda como versión el archivo que se va a pisar, si está protegido y cambió."""
    protegido = any(ruta.startswith(c.rstrip(os.sep) + os.sep) for c in cfg.carpetas)
    if protegido and os.path.isfile(ruta):
        try:
            copia.guardar_archivos(cfg, [ruta])
        except OSError:
            return False
    return True


def _escribir(version: Version, ruta: str) -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    temporal = ruta + '.restaurando'
    try:
        shutil.copyfile(version.archivo, temporal)
        info = os.stat(version.archivo)
        os.utime(temporal, ns=(info.st_atime_ns, info.st_mtime_ns))
        os.replace(temporal, ruta)
    except BaseException:
        if os.path.lexists(temporal):
            os.unlink(temporal)
        raise


def _resolver(cfg: Config, ruta: str, version: Version, conflicto: str, decidir) -> str | None:
    """Ruta final tras aplicar la política de conflicto, o None si se omite."""
    if not os.path.lexists(ruta):
        return ruta
    accion = conflicto
    if accion == 'preguntar':
        accion = decidir(ruta, version) if decidir else 'renombrar'
    if accion == 'omitir' or accion not in RESOLUCIONES:
        return None
    if accion == 'renombrar' or os.path.isdir(ruta):
        return plan.nombre_libre(ruta)
    return ruta if _versionar_actual(cfg, ruta) else None


def restaurar(cfg: Config, entradas, destino_dir: str | None = None, conflicto: str = 'preguntar',
              decidir=None, punto_id: int | None = None) -> list[str]:
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return []
    bases = list(cfg.carpetas) if destino_dir is None else [destino_dir]
    escritas = []
    try:
        for version, ruta in plan.trabajos(cfg, cat, entradas, destino_dir, punto_id):
            if not plan.permitido(ruta, bases):
                continue
            ruta = _resolver(cfg, ruta, version, conflicto, decidir)
            try:
                if ruta is not None:
                    _escribir(version, ruta)
                    escritas.append(ruta)
            except OSError:
                continue                  # copia ausente o destino sin permiso: se sigue con el resto
    finally:
        cat.db.close()
    return escritas
