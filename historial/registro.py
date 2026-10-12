"""Registro de eventos (como el visor de eventos del Historial de archivos de Windows)."""
from __future__ import annotations

import os
from datetime import datetime

MAX_BYTES = 512 * 1024          # al pasar de este tamaño se conserva solo la mitad más reciente


def ruta() -> str:
    base = os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
    return os.path.join(base, 'historial-archivos', 'historial.log')


def anotar(nivel: str, texto: str) -> None:
    texto = texto.encode('unicode_escape').decode('ascii') if any(c in texto for c in '\r\n\x1b') else texto
    archivo = ruta()
    os.makedirs(os.path.dirname(archivo), exist_ok=True)
    try:
        if os.path.getsize(archivo) > MAX_BYTES:
            with open(archivo, 'rb') as f:
                f.seek(-MAX_BYTES // 2, os.SEEK_END)
                cola = f.read()
            with open(archivo, 'wb') as f:
                f.write(cola[cola.find(b'\n') + 1:])
    except OSError:
        pass
    with open(archivo, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} {nivel:<11} {texto}\n')
