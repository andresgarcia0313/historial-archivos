"""Carpetas personales que se protegen al activar por primera vez (las "bibliotecas")."""
import os

from .qt import C

_UBICACIONES = ('DocumentsLocation', 'DesktopLocation', 'PicturesLocation', 'MusicLocation', 'MoviesLocation')


def predeterminadas() -> list[str]:
    """Documentos, Escritorio, Imágenes, Música y Vídeos que existan, sin la carpeta personal."""
    casa = os.path.expanduser('~')
    rutas = []
    for nombre in _UBICACIONES:
        tipo = getattr(C.QStandardPaths.StandardLocation, nombre)
        for ruta in C.QStandardPaths.standardLocations(tipo):
            if os.path.isdir(ruta) and ruta != casa and ruta not in rutas:
                rutas.append(ruta)
    return rutas
