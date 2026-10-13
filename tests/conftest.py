"""Al final de cada prueba, espera a los hilos de la interfaz que sigan corriendo."""
import pytest


@pytest.fixture(autouse=True)
def _esperar_hilos():
    yield
    try:
        from historial.gui import trabajo
    except ImportError:          # sin Qt instalado: no hay hilos que esperar
        return
    trabajo.esperar_todas()


def pytest_sessionfinish(session, exitstatus):
    """Libera ventanas e hilos de Qt en orden antes de que Python cierre.

    Sin esto, al salir el recolector destruye objetos de Qt en cualquier orden y en macOS el
    proceso cae ("shared QObject was deleted directly") aunque todas las pruebas pasen.
    """
    try:
        from historial.gui import trabajo
        from historial.gui.qt import C, W
    except ImportError:
        return
    app = W.QApplication.instance()
    if app is None:
        return
    trabajo.esperar_todas()
    for ventana in app.topLevelWidgets():
        ventana.close()
        ventana.deleteLater()
    C.QCoreApplication.sendPostedEvents(None, C.QEvent.Type.DeferredDelete)
    app.processEvents()
    import gc
    gc.collect()
