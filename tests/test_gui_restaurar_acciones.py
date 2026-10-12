"""Restaurar desde la línea de tiempo: botón verde, Restaurar en..., hilo y vista previa."""
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


def test_boton_verde_restaura_a_la_ubicacion_original(app, falso):
    w = Restaurar()
    _entrar_en_documentos(falso, w)
    w.c.barra.atras.click()
    assert w.c.barra.verde.toolTip() == 'Restaurar a la ubicación original'
    w.c.barra.verde.click()                                          # sin selección: toda la carpeta del punto
    assert esperar(app, lambda: 'Se restauraron 2' in w.c.estado.text())
    entradas, destino, modo = falso.restauradas[0]
    assert [e.nombre for e in entradas] == ['informe.txt', 'notas.md'] and destino is None and modo == 'preguntar'
    assert not w.ocupado and falso.puntos_pedidos == [2]             # carpetas: del punto que se está viendo


def test_restaurar_seleccion_en_otra_carpeta(app, falso, monkeypatch, tmp_path):
    destino = str(tmp_path / 'salida')
    monkeypatch.setattr(acciones, 'elegir_destino', lambda padre: destino)
    w = Restaurar(falso.docs)
    w.c.vista.setCurrentIndex(w.c.vista.modelo.index(1, 0))
    w.c.accion_en.trigger()
    assert esperar(app, lambda: falso.restauradas)
    assert [e.nombre for e in falso.restauradas[0][0]] == ['informe.txt'] and falso.restauradas[0][1] == destino
    w.c.accion_todo.trigger()
    assert len(w.c.vista.seleccionadas()) == 3


def test_restaurar_no_bloquea_y_cierre_espera(app, falso, monkeypatch):
    import threading
    liberar = threading.Event()
    monkeypatch.setattr(falso, 'restaurar', lambda *a, **k: (liberar.wait(3), ['x'])[1])
    monkeypatch.setattr('historial.gui.acciones.api.restaurar', falso.restaurar)
    w = Restaurar(falso.docs)
    w.show()
    w.c.barra.verde.click()
    assert w.ocupado and w.c.estado.text() == 'Restaurando...'      # la interfaz sigue viva
    assert not w.close() and w.c.estado.text() == 'Espere a que termine la restauración.'
    liberar.set()
    assert esperar(app, lambda: not w.ocupado)
    assert w.close()


def test_doble_clic_en_archivo_abre_copia_temporal_de_solo_lectura(app, falso, monkeypatch):
    abiertos = []
    monkeypatch.setattr(acciones.G.QDesktopServices, 'openUrl', lambda url: abiertos.append(url.toLocalFile()))
    w = Restaurar(falso.docs)
    w.c.vista.doubleClicked.emit(w.c.vista.modelo.index(1, 0))      # informe.txt (punto 3)
    assert len(abiertos) == 1 and abiertos[0].endswith('informe.txt')
    assert open(abiertos[0]).read() == 'contenido version 3'
    assert not os.stat(abiertos[0]).st_mode & stat.S_IWUSR


def test_sin_copias(app, falso, monkeypatch):
    monkeypatch.setattr(falso, 'puntos', lambda cfg: [])
    monkeypatch.setattr('historial.gui.restaurar.api.puntos', falso.puntos)
    w = Restaurar()
    assert w.c.estado.text() == 'El Historial de archivos está desactivado actualmente. Configure el Historial de archivos.'
    falso.cfg.activo = True
    w = Restaurar()
    assert w.c.estado.text() == 'Todavía no hay copias para restaurar.' and w.c.encabezado.text() == ''
    assert not w.c.barra.verde.isEnabled()
