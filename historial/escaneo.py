"""Recorrido de una carpeta protegida con os.scandir, sin cruzar sistemas de archivos."""
from __future__ import annotations

import fnmatch
import os
import stat


def _dispositivo(ruta: str, info: os.stat_result) -> int:
    """Identificador del sistema de archivos (punto único para simularlo en pruebas)."""
    return info.st_dev


def _coincide(nombre: str, patrones) -> bool:
    return any(fnmatch.fnmatchcase(nombre, patron) for patron in patrones)


def recorrer(raiz: str, excluir: set[str], patrones, inseguros: list[str]):
    """Genera (ruta, stat) de cada archivo regular bajo `raiz`.

    No sigue enlaces simbólicos y salta toda subcarpeta cuyo dispositivo difiera del de la raíz
    (montajes sshfs, rclone, nfs: igual que find -xdev). Lo que no se pudo leer se agrega a
    `inseguros` (también los montajes saltados) para que no se dé por borrado.
    """
    if raiz in excluir:
        return
    try:
        dev_raiz = _dispositivo(raiz, os.stat(raiz))
    except OSError:
        inseguros.append(raiz)
        return
    pendientes = [raiz]
    while pendientes:
        carpeta = pendientes.pop()
        try:
            with os.scandir(carpeta) as it:
                entradas = list(it)
        except OSError:
            inseguros.append(carpeta)
            continue
        for entrada in entradas:
            if _coincide(entrada.name, patrones) or entrada.path in excluir:
                continue
            try:
                if entrada.is_symlink():
                    continue
                info = entrada.stat(follow_symlinks=False)
            except OSError:
                inseguros.append(entrada.path)
                continue
            if stat.S_ISDIR(info.st_mode):
                if _dispositivo(entrada.path, info) == dev_raiz:
                    pendientes.append(entrada.path)
                else:
                    inseguros.append(entrada.path)     # montaje ajeno: no se copia ni se da por borrado
            elif stat.S_ISREG(info.st_mode):
                yield entrada.path, info
