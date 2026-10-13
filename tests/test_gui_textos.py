"""Textos es/en, formatos y reglas de tamaño de los módulos de la GUI."""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app  # noqa: F401,E402

from historial.gui import formato, textos  # noqa: E402
from historial.gui.textos import EN, ES, t  # noqa: E402

RAIZ = os.path.join(os.path.dirname(__file__), '..', 'historial', 'gui')


def _fuentes():
    return [f for f in glob.glob(os.path.join(RAIZ, '*.py')) if not os.path.basename(f).startswith('textos_')]


def test_cada_texto_usado_existe_en_los_dos_idiomas():
    usadas = set()
    for ruta in _fuentes():
        usadas |= set(re.findall(r"\bt\('([a-z_]+)'", open(ruta, encoding='utf-8').read()))
    usadas |= set(re.findall(r"\(\s*'((?:enl|conflicto)_[a-z]+)'", ''.join(open(f).read() for f in _fuentes())))
    assert len(usadas) > 60
    assert not [k for k in usadas if k not in ES], 'faltan en español'
    assert not [k for k in usadas if k not in EN], 'faltan en inglés'


def test_no_hay_textos_muertos():
    codigo = ''.join(open(f, encoding='utf-8').read() for f in _fuentes())
    muertos = [k for k in ES if f"'{k}'" not in codigo]
    assert muertos == []


def test_los_dos_idiomas_tienen_las_mismas_claves_y_marcadores():
    assert set(ES) == set(EN)
    for clave in ES:
        assert set(re.findall(r'{(\w+)}', ES[clave])) == set(re.findall(r'{(\w+)}', EN[clave])), clave


def test_idioma_por_locale(monkeypatch):
    for var in ('HISTORIAL_IDIOMA', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        monkeypatch.delenv(var, raising=False)
    assert textos.idioma() == 'es'                                   # sin locale: español
    monkeypatch.setenv('LANG', 'en_US.UTF-8')
    assert textos.idioma() == 'en' and t('activar') == 'Turn on'
    monkeypatch.setenv('LANG', 'es_CO.UTF-8')
    assert textos.idioma() == 'es' and t('activar') == 'Activar'
    monkeypatch.setenv('HISTORIAL_IDIOMA', 'en')
    assert t('abrir') == 'Open' and t('no_existe') == 'no_existe'


def test_formatos(app, monkeypatch):
    from datetime import datetime
    monkeypatch.setenv('HISTORIAL_IDIOMA', 'es')
    assert [formato.tam_humano(n) for n in (0, 1536, 5 * 2**20, 465 * 2**30)] == ['0 B', '2 KB', '5,0 MB', '465 GB']
    assert formato.fecha_texto(datetime(2026, 10, 12, 9, 5)) == '12/10/2026 09:05'
    assert formato.fecha_texto(datetime(2026, 10, 12, 9, 5), True) == 'lunes, 12 de octubre de 2026  09:05'
    assert formato.fecha_texto(None) == ''
    monkeypatch.setenv('HISTORIAL_IDIOMA', 'en')
    assert formato.fecha_texto(datetime(2026, 10, 12, 15, 5), True) == 'Monday, October 12, 2026  3:05 PM'


def test_ningun_modulo_de_la_gui_pasa_de_100_lineas():
    largos = {os.path.basename(f): n for f in glob.glob(os.path.join(RAIZ, '*.py'))
              if (n := len(open(f, encoding='utf-8').read().splitlines())) > 100}
    assert largos == {}


def test_los_archivos_de_prueba_de_la_gui_tampoco_pasan_de_100_lineas():
    carpeta = os.path.dirname(__file__)
    largos = {os.path.basename(f): n for f in glob.glob(os.path.join(carpeta, 'test_gui*.py'))
              if (n := len(open(f, encoding='utf-8').read().splitlines())) > 100}
    assert largos == {}


def test_la_gui_solo_usa_la_api_publica():
    for ruta in _fuentes():
        for linea in open(ruta, encoding='utf-8'):
            if linea.startswith(('from historial', 'import historial')):
                patron = r'from historial( import (api|otras)$|\.(api|contrato_uso|otras) import \w+)'
                assert re.match(patron, linea.strip()), (ruta, linea)
