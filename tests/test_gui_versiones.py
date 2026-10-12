"""Versiones anteriores y modos de entrada de la aplicación."""
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


def test_versiones_anteriores(app, falso, monkeypatch, tmp_path):
    d = Versiones(os.path.join(falso.docs, 'informe.txt'))
    cab = [d.tabla.horizontalHeaderItem(i).text() for i in range(3)]
    assert cab == ['Nombre', 'Fecha de modificación', 'Ubicación']
    assert d.tabla.rowCount() == 3 and d.tabla.item(0, 0).text() == 'informe.txt'
    assert d.tabla.item(0, 2).text() == 'Historial de archivos' and d.tabla.item(0, 1).text() == '12/10/2026 09:30'
    assert d.windowTitle() == 'Propiedades: informe.txt'
    d.tabla.selectRow(2)
    preguntas = []
    monkeypatch.setattr(versiones, 'confirmar', lambda padre, texto: preguntas.append(texto) or False)
    d.boton_restaurar.menu().actions()[0].trigger()                  # cancelado: no se restaura nada
    assert falso.restauradas == [] and '¿Está seguro de que desea restaurar la versión anterior de "informe.txt"' in preguntas[0]
    assert 'no se puede deshacer' in preguntas[0]
    monkeypatch.setattr(versiones, 'confirmar', lambda padre, texto: True)
    d.boton_restaurar.menu().actions()[0].trigger()
    assert esperar(app, lambda: falso.restauradas and not d.ocupado)
    assert falso.restauradas[0][0][0].version_id == 1 and falso.restauradas[0][1] is None
    assert falso.restauradas[0][2] == 'reemplazar'                   # ya confirmó: sin segundo diálogo
    assert d.estado.text() == 'El archivo se restauró correctamente a la versión anterior.'
    monkeypatch.setattr(acciones, 'elegir_destino', lambda padre: str(tmp_path))
    d.boton_restaurar.menu().actions()[1].trigger()
    assert esperar(app, lambda: len(falso.restauradas) == 2 and not d.ocupado)
    assert falso.restauradas[1][1] == str(tmp_path) and falso.restauradas[1][2] == 'preguntar'


def test_versiones_abrir_y_modos_de_app(app, falso, monkeypatch, tmp_path):
    abiertos = []
    monkeypatch.setattr(acciones.G.QDesktopServices, 'openUrl', lambda url: abiertos.append(url.toLocalFile()))
    d = Versiones(os.path.join(falso.docs, 'informe.txt'))
    d.tabla.selectRow(1)
    d.abrir_version()
    assert open(abiertos[0]).read() == 'contenido version 2'
    assert [a.text() for a in d.abrir.menu().actions()] == ['Abrir', 'Abrir en el historial de archivos']
    d.abrir_historial()
    assert d.ventana_historial.nav.carpeta == falso.docs
    assert type(app_gui.crear_ventana('panel')).__name__ == 'Panel'
    assert type(app_gui.crear_ventana('restaurar')).__name__ == 'Restaurar'
    carpeta = app_gui.crear_ventana('versiones', falso.docs)
    assert type(carpeta).__name__ == 'Restaurar' and carpeta.nav.carpeta == falso.docs
    assert type(app_gui.crear_ventana('versiones', str(tmp_path / 'borrado.txt'))).__name__ == 'Versiones'
    try:
        app_gui.crear_ventana('otro')
    except ValueError:
        pass
    else:
        raise AssertionError('debía rechazar el modo')


def test_main_abre_y_cierra(app, falso):
    from historial.gui.qt import C
    C.QTimer.singleShot(50, app.quit)
    assert app_gui.main('panel') == 0
