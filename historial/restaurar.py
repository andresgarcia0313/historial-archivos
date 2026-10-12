"""Restauración de archivos y carpetas (recursiva) con manejo de conflictos."""
from __future__ import annotations

import os
import shutil

from . import catalogo, consulta, copia
from .api import Config, Entrada, Version

RESOLUCIONES = ('reemplazar', 'omitir', 'renombrar')


def _nombre_libre(ruta: str) -> str:
    base, extension = os.path.splitext(ruta)
    n = 2
    while os.path.lexists(f'{base} ({n}){extension}'):
        n += 1
    return f'{base} ({n}){extension}'


def _trabajos(cfg: Config, cat, entradas, destino_dir, punto_id) -> list[tuple[Version, str]]:
    """Pares (versión, ruta de destino); las carpetas se expanden con su contenido en el punto."""
    trabajos = []
    for entrada in entradas:
        if entrada.es_carpeta:
            punto = consulta.ultimo_punto(cat) if punto_id is None else punto_id
            base = entrada.ruta if destino_dir is None else os.path.join(destino_dir, entrada.nombre)
            for v in consulta.en_punto(cfg, cat, entrada.ruta, punto):
                trabajos.append((v, os.path.join(base, os.path.relpath(v.ruta, entrada.ruta))))
        else:
            version = consulta.version_de(cfg, cat, entrada)
            if version:
                destino = entrada.ruta if destino_dir is None else os.path.join(destino_dir, entrada.nombre)
                trabajos.append((version, destino))
    return trabajos


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


def restaurar(cfg: Config, entradas: list[Entrada], destino_dir: str | None = None,
              conflicto: str = 'preguntar', decidir=None, punto_id: int | None = None) -> list[str]:
    cat = catalogo.abrir(cfg, crear=False)
    if cat is None:
        return []
    escritas = []
    for version, ruta in _trabajos(cfg, cat, entradas, destino_dir, punto_id):
        if os.path.lexists(ruta):
            accion = conflicto
            if accion == 'preguntar':
                accion = decidir(ruta, version) if decidir else 'renombrar'
            if accion == 'omitir' or accion not in RESOLUCIONES:
                continue
            if accion == 'renombrar' or os.path.isdir(ruta):
                ruta = _nombre_libre(ruta)
            elif not _versionar_actual(cfg, ruta):
                continue
        try:
            _escribir(version, ruta)
        except OSError:
            continue                      # copia ausente o destino sin permiso: se sigue con el resto
        escritas.append(ruta)
    cat.db.close()
    return escritas
