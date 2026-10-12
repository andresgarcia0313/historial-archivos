"""Punto de entrada de la interfaz: main('panel' | 'restaurar' | 'versiones', ruta=None)."""
import os
import sys

from . import estilo
from .qt import W

MODOS = ('panel', 'restaurar', 'versiones')


def crear_ventana(modo: str, ruta: str | None = None):
    """Construye la ventana del modo pedido (sin mostrarla). Los imports son perezosos para arrancar rápido."""
    if modo == 'panel':
        from .panel import Panel
        return Panel()
    if modo == 'restaurar':
        from .restaurar import Restaurar
        return Restaurar(os.path.abspath(ruta) if ruta else '')
    if modo == 'versiones':
        if ruta and not os.path.isdir(ruta):
            from .versiones import Versiones
            return Versiones(os.path.abspath(ruta))
        from .restaurar import Restaurar          # una carpeta se explora como en Restaurar archivos personales
        return Restaurar(os.path.abspath(ruta) if ruta else '')
    raise ValueError(f'modo desconocido: {modo}')


def main(modo: str = 'panel', ruta: str | None = None) -> int:
    """Abre la ventana y devuelve el código de salida de la aplicación."""
    app = W.QApplication.instance() or W.QApplication(sys.argv[:1])
    app.setApplicationName('historial-archivos')
    estilo.aplicar(app)
    ventana = crear_ventana(modo, ruta)
    ventana.show()
    return app.exec()
