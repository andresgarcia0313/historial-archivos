"""Utilidades compartidas por las pruebas del motor: HOME falso, origen y destino en tmp_path."""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pytest

from historial import api


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    origen = home / 'Documentos'
    destino = tmp_path / 'unidad'
    for carpeta in (origen, destino):
        carpeta.mkdir(parents=True)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('HISTORIAL_SIN_PROGRAMAR', '1')
    cfg = api.Config(activo=True, destino=str(destino), carpetas=[str(origen)])
    return SimpleNamespace(home=home, origen=origen, destino=destino, cfg=cfg, raiz=tmp_path)


def escribir(ruta, texto: str, mtime: float | None = None) -> str:
    """Crea o reescribe un archivo; con mtime distinto cada llamada garantiza que se detecte el cambio."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding='utf-8')
    os.utime(ruta, (time.time(), mtime if mtime is not None else time.time() + len(texto) * 7))
    return str(ruta)


def nombres_en(carpeta) -> list[str]:
    return sorted(p.name for p in carpeta.rglob('*') if p.is_file())
