"""Panel principal, selección de unidad, exclusiones, configuración avanzada y limpieza."""
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
    assert '400 GB libres de 465 GB' in p.derecha.hacia.text()


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


def test_detectar_unidades_linux(monkeypatch):
    montajes = ('/dev/sda1 / ext4 rw 0 0\n/dev/sdb1 /media/ana/USB\\040DISK ext4 rw 0 0\n'
                'srv:/datos /home/ana/red nfs4 rw 0 0\ntmpfs /run/user/1000 tmpfs rw 0 0\n')
    monkeypatch.setattr(unidades.shutil, 'disk_usage', lambda r: __import__('shutil')._ntuple_diskusage(100, 40, 60))
    lista = unidades.detectar(montajes, 'linux')
    assert [u.ruta for u in lista] == ['/media/ana/USB DISK', '/home/ana/red']
    assert lista[0].nombre == 'USB DISK' and lista[0].libre == 60 and lista[0].total == 100


def test_unidad_agrega_ubicacion_de_red(app, falso, monkeypatch, tmp_path):
    monkeypatch.setattr(unidades, 'detectar', lambda *a, **k: [])
    monkeypatch.setattr(unidad.W.QFileDialog, 'getExistingDirectory', lambda *a, **k: str(tmp_path))
    d = unidad.Unidad(falso.cfg)
    assert d.seleccion() == '' and d.windowTitle().startswith('Seleccionar una unidad')
    d.agregar_red()
    assert d.seleccion() == str(tmp_path)
    d.accept()
    assert falso.cfg.destino == str(tmp_path) and falso.guardados


def test_excluir_agrega_quita_y_guarda(app, falso, tmp_path):
    d = Excluir(falso.cfg)
    nueva = str(tmp_path / 'Descargas')
    d.excluidas.poner(nueva)
    d.excluidas.poner(nueva)                                        # sin duplicados
    d.incluidas.lista.setCurrentRow(1)
    d.incluidas.quitar_seleccion()
    assert d.excluidas.rutas() == [nueva] and d.incluidas.rutas() == [falso.docs]
    d.accept()
    assert falso.cfg.excluir == [nueva] and falso.cfg.carpetas == [falso.docs] and falso.guardados


def test_avanzada_opciones_como_windows(app, falso, monkeypatch, tmp_path):
    d = avanzada.Avanzada(falso.cfg)
    freq = [d.frecuencia.itemText(i) for i in range(d.frecuencia.count())]
    cons = [d.conservar.itemText(i) for i in range(d.conservar.count())]
    assert freq[0] == 'Cada 10 minutos' and 'Cada hora (predeterminado)' in freq and freq[-1] == 'Diariamente'
    assert cons == ['Hasta que se necesite espacio', '1 mes', '3 meses', '6 meses', '9 meses', '1 año', '2 años',
                    'Para siempre (predeterminado)']
    assert d.frecuencia.currentText() == 'Cada hora (predeterminado)'
    d.frecuencia.setCurrentIndex(d.frecuencia.findData(1440))
    d.conservar.setCurrentIndex(d.conservar.findData(365))
    d.accept()
    assert falso.cfg.frecuencia_min == 1440 and falso.cfg.conservar_dias == 365


def test_avanzada_registro_sin_archivo_avisa(app, falso, monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path))
    avisos = []
    monkeypatch.setattr(avanzada, 'aviso', lambda padre, texto: avisos.append(texto))
    abiertos = []
    monkeypatch.setattr(avanzada.G.QDesktopServices, 'openUrl', lambda url: abiertos.append(url.toLocalFile()))
    d = avanzada.Avanzada(falso.cfg)
    d.registro.click()
    assert avisos == ['Todavía no hay eventos registrados.']
    os.makedirs(os.path.dirname(avanzada.ruta_registro()))
    open(avanzada.ruta_registro(), 'w').close()
    d.registro.click()
    assert abiertos == [avanzada.ruta_registro()]


def test_limpiar_versiones_en_segundo_plano(app, falso):
    d = Limpiar(falso.cfg)
    opciones = [d.combo.itemText(i) for i in range(d.combo.count())]
    assert opciones[:2] == ['1 año', 'Todos excepto el más reciente'] and '2 años' in opciones
    d.boton.click()
    assert esperar(app, lambda: 'liberaron' in d.resultado.text())
    assert falso.llamadas == [('limpiar', 365)] and '2 KB' in d.resultado.text()
    d.combo.setCurrentIndex(1)
    d.boton.click()
    assert esperar(app, lambda: len(falso.llamadas) == 2) and falso.llamadas[1] == ('limpiar', None)
