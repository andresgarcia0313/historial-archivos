"""Panel principal: estado, activar, ejecutar ahora y enlaces laterales."""
# ruff: noqa: F401
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, esperar, falso  # noqa: F401,E402
from historial.gui import avanzada, unidad, unidades  # noqa: E402
from historial.gui.excluir import Excluir  # noqa: E402
from historial.gui.limpiar import Limpiar  # noqa: E402
from historial.gui.panel import Panel  # noqa: E402
from historial.gui.panel_lateral import Lateral  # noqa: E402


def _elegir_primera_unidad(monkeypatch, ruta):
    monkeypatch.setattr(unidades, 'detectar', lambda *a, **k: [unidades.Unidad('USB', ruta, 50 * 10**9, 64 * 10**9)])
    monkeypatch.setattr(unidad.Unidad, 'exec', lambda self: (self.lista.setCurrentItem(self.lista.topLevelItem(0)), self.accept())[1])


def test_panel_desactivado_muestra_los_textos_de_windows(app, falso):
    p = Panel()
    d = p.derecha
    assert d.caja.title() == 'Historial de archivos desactivado'
    assert d.activar.text() == 'Activar' and not d.ejecutar.isEnabled()
    assert d.desde.text() == 'Documentos, Imagenes' and d.red.text() == 'Seleccionar una ubicación de red'
    assert d.hacia.text() == 'No se encontró ninguna unidad que se pueda usar.'
    assert d.caja_aviso.isVisibleTo(p)
    assert '12/10/2026 09:30' in d.ultima.text()


def test_activar_pide_unidad_guarda_y_lanza_la_copia(app, falso, monkeypatch, tmp_path):
    _elegir_primera_unidad(monkeypatch, str(tmp_path))
    p = Panel()
    p.sondeo.setInterval(10)
    p.derecha.activar.click()
    assert falso.cfg.activo and falso.cfg.destino == str(tmp_path)
    assert ('ejecutar',) in falso.llamadas
    assert p.derecha.progreso.isVisible() or p.derecha.progreso.isVisibleTo(p)
    assert esperar(app, lambda: not p.sondeo.isActive())          # la barra sigue hasta que en_curso baja
    assert p.derecha.caja.title() == 'Historial de archivos activado' and not p.derecha.caja_aviso.isVisibleTo(p)
    assert p.derecha.activar.text() == 'Desactivar' and p.derecha.ejecutar.isEnabled()
    assert not p.derecha.progreso.isVisibleTo(p)
    assert '400 GB disponibles de 465 GB' in p.derecha.hacia.text()


def test_activar_sin_unidad_no_activa(app, falso, monkeypatch):
    monkeypatch.setattr(unidad.Unidad, 'exec', lambda self: 0)
    p = Panel()
    p.derecha.activar.click()
    assert not falso.cfg.activo and falso.guardados == []


def test_desactivar_y_reconectar(app, falso):
    falso.cfg.activo, falso.cfg.destino = True, '/media/x/USB'
    p = Panel()
    assert p.derecha.activar.text() == 'Desactivar'
    p.derecha.activar.click()
    assert falso.cfg.activo is False and falso.guardados[-1][0] is False


def test_enlaces_laterales_abren_cada_ventana(app, falso, monkeypatch):
    abiertos = []
    for clase in (unidad.Unidad, Excluir, avanzada.Avanzada):
        monkeypatch.setattr(clase, 'exec', lambda self, c=clase: abiertos.append(c.__name__) or 0)
    p = Panel()
    lateral = p.findChildren(Lateral)[0]
    enlaces = {b.text(): b for b in lateral.findChildren(type(p.derecha.activar)) if b.objectName() == 'enlace'}
    assert list(enlaces) == ['Restaurar archivos personales', 'Seleccionar unidad', 'Excluir carpetas',
                             'Configuración avanzada']
    for texto in list(enlaces)[1:]:
        enlaces[texto].click()
    assert abiertos == ['Unidad', 'Excluir', 'Avanzada']
    p.derecha.red.click()                                            # el aviso amarillo también abre Seleccionar unidad
    assert abiertos[-1] == 'Unidad'
    enlaces['Restaurar archivos personales'].click()
    assert len(p.hijas) == 1 and p.hijas[0].windowTitle() == 'Página principal - Historial de archivos'
