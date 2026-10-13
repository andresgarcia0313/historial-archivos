"""Utilidades de las pruebas de la GUI: aplicación offscreen y un motor falso (monkeypatch de historial.api)."""
import os
import tempfile
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('HISTORIAL_IDIOMA', 'es')

import pytest

from historial.gui import estilo
from historial.gui.qt import C, W

# La elección de tema vive en QSettings: en pruebas, un directorio temporal (nunca la config real del usuario).
C.QSettings.setPath(C.QSettings.Format.IniFormat, C.QSettings.Scope.UserScope, tempfile.mkdtemp(prefix='hist-gui-'))


@pytest.fixture(scope='session')
def app():
    aplicacion = W.QApplication.instance() or W.QApplication(['pruebas'])
    estilo.aplicar(aplicacion)
    return aplicacion


def esperar(app, condicion, ms=3000):
    """Procesa eventos hasta que se cumple la condición (los hilos avisan por señales)."""
    limite = time.time() + ms / 1000
    while time.time() < limite:
        app.processEvents()
        if condicion():
            return True
        time.sleep(0.005)
    app.processEvents()
    return condicion()

from test_gui_falso import Falso, falso  # noqa: E402,F401  (se reexportan para los demás módulos)
