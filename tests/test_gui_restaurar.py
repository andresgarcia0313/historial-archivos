"""Restaurar archivos personales (línea de tiempo), conflictos y Versiones anteriores contra un motor falso."""
import os
import stat
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, esperar, falso  # noqa: F401,E402

from historial.gui import acciones, app as app_gui, conflicto  # noqa: E402
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
    assert w.c.ruta.text() == 'Inicio  ›  Documentos'
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
    assert w.nav.carpeta == '' and w.c.ruta.text() == 'Inicio' and not w.c.adelante.isEnabled()
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
    assert miga('/home/a/Documentos/x/y', raices) == 'Inicio  ›  Documentos  ›  x  ›  y'
    assert miga('/otra/ruta', raices) == 'Inicio  ›  otra  ›  ruta'
    n = Navegacion('')
    n.ir('a')
    n.ir('b')
    n.atras()
    n.ir('c')
    assert n.pila == ['', 'a', 'c'] and not n.hay_adelante()


def test_boton_verde_restaura_a_la_ubicacion_original(app, falso):
    w = Restaurar()
    _entrar_en_documentos(falso, w)
    w.c.barra.atras.click()
    assert w.c.barra.verde.toolTip() == 'Restaurar a la ubicación original'
    w.c.barra.verde.click()                                          # sin selección: toda la carpeta del punto
    assert esperar(app, lambda: 'Se restauraron 2' in w.c.estado.text())
    entradas, destino, modo = falso.restauradas[0]
    assert [e.nombre for e in entradas] == ['informe.txt', 'notas.md'] and destino is None and modo == 'preguntar'
    assert not w.ocupado


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
    assert w.c.estado.text() == 'Todavía no hay copias para restaurar.' and w.c.encabezado.text() == ''
    assert not w.c.barra.verde.isEnabled()


def test_versiones_anteriores(app, falso, monkeypatch, tmp_path):
    d = Versiones(os.path.join(falso.docs, 'informe.txt'))
    cab = [d.tabla.horizontalHeaderItem(i).text() for i in range(4)]
    assert cab == ['Nombre', 'Fecha de modificación', 'Tamaño', 'Ubicación']
    assert d.tabla.rowCount() == 3 and d.tabla.item(0, 0).text() == 'informe.txt'
    assert d.tabla.item(0, 3).text() == 'Historial de archivos' and d.tabla.item(0, 2).text() == '300 B'
    assert d.tabla.item(0, 1).text() == '12/10/2026 09:30'
    d.tabla.selectRow(2)
    d.boton_restaurar.menu().actions()[0].trigger()
    assert esperar(app, lambda: falso.restauradas and not d.ocupado)
    assert falso.restauradas[0][0][0].version_id == 1 and falso.restauradas[0][1] is None
    monkeypatch.setattr(acciones, 'elegir_destino', lambda padre: str(tmp_path))
    d.boton_restaurar.menu().actions()[1].trigger()
    assert esperar(app, lambda: len(falso.restauradas) == 2 and not d.ocupado)
    assert falso.restauradas[1][1] == str(tmp_path) and 'Se restauraron 1' in d.estado.text()


def test_versiones_abrir_y_modos_de_app(app, falso, monkeypatch, tmp_path):
    abiertos = []
    monkeypatch.setattr(acciones.G.QDesktopServices, 'openUrl', lambda url: abiertos.append(url.toLocalFile()))
    d = Versiones(os.path.join(falso.docs, 'informe.txt'))
    d.tabla.selectRow(1)
    d.abrir.click()
    assert open(abiertos[0]).read() == 'contenido version 2'
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
