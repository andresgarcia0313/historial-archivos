"""Rutas de configuración y datos del usuario; lectura y escritura de config.json."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, fields
from pathlib import Path

from .api import Config


def dir_config() -> Path:
    return Path.home() / '.config' / 'historial-archivos'


def dir_datos() -> Path:
    return Path.home() / '.local' / 'share' / 'historial-archivos'


def ruta_catalogo() -> Path:
    return dir_datos() / 'catalogo.sqlite'


def cargar() -> Config:
    """Lee la configuración; si falta o está dañada devuelve la predeterminada."""
    try:
        datos = json.loads((dir_config() / 'config.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return Config()
    if not isinstance(datos, dict):
        return Config()
    conocidos = {campo.name for campo in fields(Config)}
    return Config(**{k: v for k, v in datos.items() if k in conocidos})


def guardar(cfg: Config) -> None:
    """Escritura atómica del JSON y aplicación de la programación."""
    carpeta = dir_config()
    carpeta.mkdir(parents=True, exist_ok=True)
    temporal = carpeta / 'config.json.tmp'
    temporal.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(temporal, carpeta / 'config.json')
    from . import programador
    programador.aplicar(cfg)
