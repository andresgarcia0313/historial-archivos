"""La alternativa PyQt6 funciona igual: las pruebas de la GUI se repiten en otro proceso con HISTORIAL_QT=pyqt6."""
import importlib.util
import os
import subprocess
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


@pytest.mark.skipif(importlib.util.find_spec('PyQt6') is None, reason='PyQt6 no instalado')
def test_las_pruebas_de_la_gui_pasan_con_pyqt6():
    entorno = dict(os.environ, HISTORIAL_QT='pyqt6', QT_QPA_PLATFORM='offscreen')
    entorno['PYTHONPATH'] = os.pathsep.join(p for p in sys.path if p)      # el hijo ve lo mismo que este proceso
    entorno.pop('HISTORIAL_CAPTURAS', None)
    orden = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
             'tests/test_gui_panel.py', 'tests/test_gui_restaurar.py']
    r = subprocess.run(orden, env=entorno, capture_output=True, text=True, cwd=RAIZ, timeout=300)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:]
    assert ' passed' in r.stdout
    nombre = subprocess.run([sys.executable, '-c', 'from historial.gui import qt; print(qt.NOMBRE)'],
                            env=entorno, capture_output=True, text=True, cwd=RAIZ)
    assert nombre.stdout.strip() == 'PyQt6'
