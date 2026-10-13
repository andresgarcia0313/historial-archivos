"""Operaciones largas fuera del hilo de la interfaz.

Los hilos no cuelgan de ningún widget: si la ventana se cierra mientras corren, Qt no los
destruye en marcha (eso tumbaba el proceso al salir). Se guardan aquí hasta que terminan y,
al cerrar la aplicación, se espera a que acaben. El resultado solo llega si el widget sigue vivo.
"""
from .qt import C, Signal, vivo

_vivas: set = set()


class Tarea(C.QThread):
    """Ejecuta `funcion()` en un hilo y avisa con `listo(resultado)` o `fallo(texto)`."""

    listo = Signal(object)
    fallo = Signal(str)

    def __init__(self, funcion):
        super().__init__()
        self._funcion = funcion

    def run(self):
        try:
            resultado = self._funcion()
        except Exception as error:  # el motor decide qué es grave; la GUI solo informa
            self.fallo.emit(str(error) or error.__class__.__name__)
            return
        self.listo.emit(resultado)


def _si_vive(padre, funcion):
    return lambda *args: funcion(*args) if vivo(padre) else None


def _terminar(tarea):
    _vivas.discard(tarea)
    tarea.deleteLater()


def esperar_todas(ms: int = 10000) -> None:
    """Espera a los hilos pendientes; se llama al salir de la aplicación y en las pruebas."""
    for tarea in list(_vivas):
        tarea.wait(ms)


def lanzar(padre, funcion, al_listo, al_fallar=None) -> Tarea:
    """Crea, conecta y arranca la tarea; la conserva viva hasta que termine."""
    tarea = Tarea(funcion)
    _vivas.add(tarea)
    tarea.listo.connect(_si_vive(padre, al_listo))
    if al_fallar:
        tarea.fallo.connect(_si_vive(padre, al_fallar))
    tarea.finished.connect(lambda: _terminar(tarea))
    app = C.QCoreApplication.instance()
    if app is not None and not app.property('espera_tareas'):
        app.setProperty('espera_tareas', True)
        app.aboutToQuit.connect(esperar_todas)
    tarea.start()
    return tarea
