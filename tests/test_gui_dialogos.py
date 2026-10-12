"""Seleccionar unidad, exclusiones, configuración avanzada y limpieza."""
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
    assert opciones == ['Hace más de 1 mes', 'Hace más de 3 meses', 'Hace más de 6 meses', 'Hace más de 9 meses',
                        'Hace más de 1 año (predeterminado)', 'Hace más de 2 años', 'Todos excepto el último']
    assert d.windowTitle() == 'Limpieza del Historial de archivos' and d.boton.text() == 'Limpieza'
    assert d.combo.currentData() == 365                              # el predeterminado de Windows
    d.boton.click()
    assert esperar(app, lambda: 'liberaron' in d.resultado.text())
    assert falso.llamadas == [('limpiar', 365)] and '2 KB' in d.resultado.text()
    d.combo.setCurrentIndex(d.combo.findData(None))
    d.boton.click()
    assert esperar(app, lambda: len(falso.llamadas) == 2) and falso.llamadas[1] == ('limpiar', None)
