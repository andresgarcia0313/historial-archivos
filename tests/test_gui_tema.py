"""Tema Drácula (predeterminado), Alucard y "Según el sistema": elección, aplicación y contraste WCAG."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, falso  # noqa: F401,E402

import pytest  # noqa: E402

from historial.gui import avanzada, estilo, tema  # noqa: E402
from historial.gui.boton_verde import BotonVerde  # noqa: E402
from historial.gui.qt import C, G  # noqa: E402


def _luminancia(hexa: str) -> float:
    canales = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lineal = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lineal[0] + 0.7152 * lineal[1] + 0.0722 * lineal[2]


def contraste(a: str, b: str) -> float:
    claro, oscuro = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


@pytest.fixture
def limpio(app):
    tema.guardar('dracula')
    yield app
    tema.guardar('dracula')
    estilo.aplicar(app)


def test_drakula_es_el_predeterminado_y_se_guarda_fuera_de_la_config_real(limpio):
    assert tema.eleccion() == 'dracula'
    assert estilo.aplicar(limpio) == 'dracula'
    assert limpio.palette().color(G.QPalette.ColorRole.Window).name() == '#282a36'
    ajustes = C.QSettings(C.QSettings.Format.IniFormat, C.QSettings.Scope.UserScope, 'historial-archivos', 'gui')
    assert 'hist-gui-' in ajustes.fileName()                     # directorio temporal de las pruebas
    assert not ajustes.fileName().startswith(os.path.expanduser('~/.config'))


def test_alucard_y_sistema(limpio):
    tema.guardar('alucard')
    assert tema.eleccion() == 'alucard' and estilo.aplicar(limpio) == 'alucard'
    assert limpio.palette().color(G.QPalette.ColorRole.Window).name() == '#fffbeb'
    assert '#644ac9' in limpio.styleSheet()
    assert tema.resolver('sistema', limpio) in ('dracula', 'alucard')
    with pytest.raises(ValueError):
        tema.guardar('rosado')


def test_configuracion_avanzada_cambia_el_tema_sin_tocar_el_motor(limpio, falso):
    d = avanzada.Avanzada(falso.cfg)
    assert [d.tema.itemText(i) for i in range(d.tema.count())] == ['Drácula (oscuro)', 'Alucard (claro)',
                                                                   'Según el sistema']
    d.tema.setCurrentIndex(d.tema.findData('alucard'))
    d.accept()
    assert tema.eleccion() == 'alucard' and tema.actual() == 'alucard'
    assert not hasattr(falso.cfg, 'tema')


def test_boton_verde_usa_el_verde_de_dracula(limpio):
    estilo.aplicar(limpio, 'dracula')
    boton = BotonVerde(76)
    imagen = boton.grab().toImage()
    assert imagen.pixelColor(38, 10).name() == '#50fa7b'
    estilo.aplicar(limpio, 'alucard')
    assert BotonVerde(76).grab().toImage().pixelColor(38, 10).name() == '#14710a'


@pytest.mark.parametrize('nombre', ['dracula', 'alucard'])
def test_contraste_aa_de_los_textos(nombre):
    c = tema.tokens(nombre)
    for superficie in ('fondo', 'tarjeta', 'lateral', 'campo'):
        assert contraste(c['texto'], c[superficie]) >= 7, superficie
        assert contraste(c['secundario'], c[superficie]) >= 4.5, superficie
        assert contraste(c['cian'], c[superficie]) >= 4.5, superficie
        assert contraste(c['naranja'], c[superficie]) >= 4.5, superficie
        assert contraste(c['borde_control'], c[superficie]) >= 3, superficie
    assert contraste(c['sobre_acento'], c['acento']) >= 4.5
    assert contraste(c['sobre_verde'], c['verde']) >= 4.5
    assert contraste(c['texto'], c['acento_suave']) >= 4.5
    assert contraste(c['texto'], c['seleccion']) >= 4.5
