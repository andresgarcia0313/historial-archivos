"""La alternativa PyQt6 funciona igual: humo en un proceso aparte con HISTORIAL_QT=pyqt6."""
import importlib.util
import os
import subprocess
import sys

import pytest

RAIZ = os.path.join(os.path.dirname(__file__), '..')
GUION = r'''
import os, sys
sys.path.insert(0, os.path.join(%(raiz)r, 'tests'))
sys.path.insert(0, %(raiz)r)
import pytest
sys.exit(pytest.main(['-q', '-p', 'no:cacheprovider', '-k', 'not pyqt6 and not capturas and not textos',
                      os.path.join(%(raiz)r, 'tests', 'test_gui_panel.py'),
                      os.path.join(%(raiz)r, 'tests', 'test_gui_restaurar.py')]))
'''


@pytest.mark.skipif(importlib.util.find_spec('PyQt6') is None, reason='PyQt6 no instalado')
def test_las_pruebas_de_la_gui_pasan_con_pyqt6():
    entorno = dict(os.environ, HISTORIAL_QT='pyqt6', QT_QPA_PLATFORM='offscreen')
    codigo = (GUION % {'raiz': os.path.abspath(RAIZ)}).replace("import pytest\n", "import pytest\n" + "".join(
        f"sys.path.append({p!r})\n" for p in sys.path if 'site-packages' in p or 'dist-packages' in p), 1)
    r = subprocess.run([sys.executable, '-c', codigo], env=entorno, capture_output=True, text=True, timeout=240)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:]
    assert ' passed' in r.stdout
    verifica = subprocess.run([sys.executable, '-c', 'from historial.gui import qt; print(qt.NOMBRE)'],
                              env=entorno, capture_output=True, text=True, cwd=os.path.abspath(RAIZ))
    assert verifica.stdout.strip() == 'PyQt6'
