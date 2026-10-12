"""Operaciones largas fuera del hilo de la interfaz."""
from .qt import C, Signal


class Tarea(C.QThread):
    """Ejecuta `funcion()` en un hilo y avisa con `listo(resultado)` o `fallo(texto)`."""

    listo = Signal(object)
    fallo = Signal(str)

    def __init__(self, funcion, padre=None):
        super().__init__(padre)
        self._funcion = funcion

    def run(self):
        try:
            resultado = self._funcion()
        except Exception as error:  # el motor decide qué es grave; la GUI solo informa
            self.fallo.emit(str(error) or error.__class__.__name__)
            return
        self.listo.emit(resultado)


def lanzar(padre, funcion, al_listo, al_fallar=None) -> Tarea:
    """Crea, conecta y arranca la tarea; el padre la conserva viva hasta que termine."""
    tarea = Tarea(funcion, padre)
    tarea.listo.connect(al_listo)
    if al_fallar:
        tarea.fallo.connect(al_fallar)
    tarea.finished.connect(tarea.deleteLater)
    tarea.start()
    return tarea
