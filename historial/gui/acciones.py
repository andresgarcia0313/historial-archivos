"""Acciones comunes a Restaurar y Versiones anteriores: restaurar sin bloquear y abrir una copia."""
import os
import shutil
import tempfile

from historial import api

from .conflicto import Decisor
from .qt import C, G, W
from .textos import t
from .trabajo import lanzar


def restaurar_entradas(ventana, cfg, entradas, destino_dir, al_terminar) -> None:
    """Restaura en un hilo. `al_terminar(rutas, error)`: error es '' si todo salió bien."""
    decisor = Decisor(ventana)
    ventana.tarea = lanzar(
        ventana, lambda: api.restaurar(cfg, entradas, destino_dir, 'preguntar', decisor),
        lambda rutas: al_terminar(list(rutas), ''), lambda motivo: al_terminar([], motivo))


def elegir_destino(padre) -> str:
    """Carpeta para "Restaurar en..."; '' si se cancela."""
    return W.QFileDialog.getExistingDirectory(padre, t('restaurar_en'), os.path.expanduser('~'))


def abrir_copia(archivo: str, nombre: str) -> str:
    """Abre una copia temporal de solo lectura (nunca el archivo guardado). Devuelve la ruta temporal."""
    carpeta = tempfile.mkdtemp(prefix='historial-')
    temporal = os.path.join(carpeta, nombre)
    shutil.copyfile(archivo, temporal)
    os.chmod(temporal, 0o444)
    G.QDesktopServices.openUrl(C.QUrl.fromLocalFile(temporal))
    return temporal
