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
