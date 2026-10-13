"""Categoría de un archivo por su extensión y filtro de copia por tipos y extensiones excluidas."""
from __future__ import annotations

import os

from .contrato_uso import CATEGORIAS

OTROS = 'otros'
_POR_EXTENSION = {ext: nombre for nombre, exts in CATEGORIAS.items() for ext in exts}


def extension(nombre: str) -> str:
    """Extensión en minúsculas y sin punto; '' si no tiene (los ocultos como '.bashrc' tampoco)."""
    base = os.path.basename(nombre)
    punto = base.rfind('.')
    return base[punto + 1:].lower() if punto > 0 else ''


def categoria_de(nombre: str) -> str:
    return _POR_EXTENSION.get(extension(nombre), OTROS)


def _normalizar(extensiones) -> frozenset[str]:
    return frozenset(str(e).strip().lstrip('.').lower() for e in extensiones or () if str(e).strip())


def filtro(cfg):
    """Función ruta -> bool que dice si se copia según cfg.tipos y cfg.extensiones_excluidas."""
    tipos = frozenset(getattr(cfg, 'tipos', None) or ())
    excluidas = _normalizar(getattr(cfg, 'extensiones_excluidas', None))
    if not tipos and not excluidas:
        return lambda ruta: True

    def se_copia(ruta: str) -> bool:
        ext = extension(ruta)
        if ext in excluidas:
            return False
        return not tipos or _POR_EXTENSION.get(ext, OTROS) in tipos
    return se_copia
