"""Restaurar archivos personales: línea de tiempo y navegación."""
# ruff: noqa: F401
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


def _nombres(v):
    return [e.nombre for e in v.entradas()]


def _entrar_en_documentos(falso, w):
    fila = next(i for i, e in enumerate(w.c.vista.entradas()) if e.nombre == 'Documentos')
    w.c.vista.doubleClicked.emit(w.c.vista.modelo.index(fila, 0))


def test_linea_de_tiempo_anterior_siguiente(app, falso):
    w = Restaurar()
    assert w.c.encabezado.text().endswith('3 de 3') and 'octubre de 2026' in w.c.encabezado.text()
    assert _nombres(w.c.vista) == ['Documentos', 'Imagenes']
    _entrar_en_documentos(falso, w)
    assert _nombres(w.c.vista) == ['foto.png', 'informe.txt', 'notas.md']
    assert w.c.ruta.text() == 'Página principal  ›  Documentos'
    w.c.barra.atras.click()
    assert w.c.encabezado.text().endswith('2 de 3') and _nombres(w.c.vista) == ['informe.txt', 'notas.md']
    w.c.barra.atras.click()
    assert w.c.encabezado.text().endswith('1 de 3') and _nombres(w.c.vista) == ['informe.txt']
    assert not w.c.barra.atras.isEnabled() and w.c.barra.adelante.isEnabled()
    w.c.barra.atras.click()                                          # en el límite no pasa nada
    assert w.c.encabezado.text().endswith('1 de 3')
    w.c.barra.adelante.click()
    w.c.barra.adelante.click()
    assert w.c.encabezado.text().endswith('3 de 3') and not w.c.barra.adelante.isEnabled()


def test_navegacion_atras_adelante_arriba_y_busqueda(app, falso):
    w = Restaurar()
    _entrar_en_documentos(falso, w)
    assert w.c.atras.isEnabled() and w.c.arriba.isEnabled() and not w.c.adelante.isEnabled()
    w.c.arriba.click()                                               # como el Explorador: Subir es un paso nuevo
    assert w.nav.carpeta == '' and w.c.ruta.text() == 'Página principal' and not w.c.adelante.isEnabled()
    w.c.atras.click()
    assert w.nav.carpeta == falso.docs and w.c.adelante.isEnabled()
    w.c.adelante.click()
    assert w.nav.carpeta == ''
    w.c.atras.click()
    w.c.buscar.setText('NOT')
    assert _nombres(w.c.vista) == ['notas.md']
    w.c.buscar.setText('')
    assert len(_nombres(w.c.vista)) == 3


def test_ayudas_de_navegacion():
    raices = ['/home/a/Documentos', '/home/a/Imagenes']
    assert padre_de('/home/a/Documentos', raices) == '' and padre_de('/home/a/Documentos/x/y', raices) == '/home/a/Documentos/x'
    assert miga('/home/a/Documentos/x/y', raices) == 'Página principal  ›  Documentos  ›  x  ›  y'
    assert miga('/otra/ruta', raices) == 'Página principal  ›  otra  ›  ruta'
    n = Navegacion('')
    n.ir('a')
    n.ir('b')
    n.atras()
    n.ir('c')
    assert n.pila == ['', 'a', 'c'] and not n.hay_adelante()
