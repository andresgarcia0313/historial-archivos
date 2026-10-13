"""Uso del espacio: cifras clave y agrupaciones por categoría, carpeta, mes y archivo."""
import time

from historial import api
from motor_utils import entorno, escribir  # noqa: F401


def _historial(entorno):
    otra = entorno.home / 'Imagenes'
    entorno.cfg.carpetas.append(str(otra))
    escribir(entorno.origen / 'a.docx', 'uno', time.time() - 50)
    escribir(otra / 'f.jpg', 'imagen')
    api.ejecutar(entorno.cfg)
    escribir(entorno.origen / 'a.docx', 'uno y dos', time.time() - 40)
    api.ejecutar(entorno.cfg)
    escribir(entorno.origen / 'a.docx', 'uno dos tres!', time.time() - 30)
    api.ejecutar(entorno.cfg)
    return str(entorno.origen / 'a.docx'), str(otra / 'f.jpg'), str(otra)


def test_cifras_clave(entorno):
    _historial(entorno)
    uso = api.uso(entorno.cfg)
    assert (uso.archivos, uso.versiones) == (2, 4)
    assert uso.bytes_copias == 3 + 9 + 13 + 6 and uso.bytes_actual == 13 + 6
    assert uso.total > 0 and uso.libre > 0
    assert uso.primera is not None and uso.primera <= uso.ultima


def test_agrupaciones(entorno):
    doc, jpg, imagenes = _historial(entorno)
    uso = api.uso(entorno.cfg)
    cat = {g.nombre: (g.bytes, g.archivos, g.versiones) for g in uso.por_categoria}
    assert cat == {'documentos': (25, 1, 3), 'imagenes': (6, 1, 1)}
    assert [g.nombre for g in uso.por_categoria] == ['documentos', 'imagenes']     # de mayor a menor
    carp = {g.nombre: (g.bytes, g.archivos, g.versiones) for g in uso.por_carpeta}
    assert carp == {str(entorno.origen): (25, 1, 3), imagenes: (6, 1, 1)}
    mes = time.strftime('%Y-%m', time.gmtime())
    assert [(g.nombre, g.bytes, g.archivos, g.versiones) for g in uso.por_mes] == [(mes, 31, 2, 4)]
    assert uso.mas_grandes[:2] == [(doc, 25, 3), (jpg, 6, 1)]
    assert uso.mas_versionados[0] == (doc, 25, 3)


def test_sin_catalogo_devuelve_vacio(entorno):
    uso = api.uso(entorno.cfg)
    assert (uso.archivos, uso.versiones, uso.bytes_copias) == (0, 0, 0)
    assert uso.primera is None and uso.por_categoria == [] and uso.mas_grandes == []


def test_destino_desconectado_no_falla(entorno):
    _historial(entorno)
    entorno.cfg.destino = str(entorno.raiz / 'no-existe')
    uso = api.uso(entorno.cfg)
    assert uso.libre == 0 and uso.total == 0
