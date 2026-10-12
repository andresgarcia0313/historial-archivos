"""Conflictos al restaurar: un diálogo por archivo o una decisión para todos."""
# ruff: noqa: F401
import os
import stat
import sys
sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, esperar, falso  # noqa: F401,E402
from historial.gui import acciones, app as app_gui, conflicto, versiones  # noqa: E402
from historial.gui.qt import W  # noqa: E402
from historial.gui.restaurar import Restaurar  # noqa: E402
from historial.gui.restaurar_nav import Navegacion, miga, padre_de  # noqa: E402
from historial.gui.versiones import Versiones  # noqa: E402


def test_conflicto_para_todos_pregunta_una_sola_vez(app, falso, monkeypatch):
    vistos = []

    def fingir(self):
        vistos.append(self.windowTitle())
        self.todos.setChecked(True)
        self._elegir('renombrar')
        return 1
    monkeypatch.setattr(conflicto.DialogoConflicto, 'exec', fingir)
    falso.conflictos = True
    w = Restaurar(falso.docs)
    w.c.barra.verde.click()
    assert esperar(app, lambda: not w.ocupado and falso.respuestas)
    assert falso.respuestas == ['renombrar', 'renombrar', 'renombrar'] and len(vistos) == 1
    assert vistos == ['Reemplazar u omitir archivos']


def test_conflicto_cada_archivo_su_decision(app, falso, monkeypatch):
    elegidas = iter(['reemplazar', 'omitir', 'renombrar'])
    monkeypatch.setattr(conflicto.DialogoConflicto, 'exec', lambda self: (self._elegir(next(elegidas)), 1)[1])
    falso.conflictos = True
    w = Restaurar(falso.docs)
    w.c.barra.verde.click()
    assert esperar(app, lambda: not w.ocupado and falso.respuestas)
    assert falso.respuestas == ['reemplazar', 'omitir', 'renombrar']


def test_dialogo_conflicto_textos_y_cierre_equivale_a_omitir(app, falso):
    d = conflicto.DialogoConflicto(os.path.join(falso.docs, 'informe.txt'), falso.version(2))
    botones = [b.text() for b in d.findChildren(W.QPushButton)]
    assert botones == ['Reemplazar el archivo en el destino', 'Omitir este archivo', 'Conservar ambos archivos']
    assert d.todos.text() == 'Hacer esto para todos los conflictos' and d.resultado == 'omitir'
    assert not d.para_todos
