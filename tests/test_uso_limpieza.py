"""Limpieza filtrada por categoría y carpeta, conservando la última versión y sin path traversal."""
import os
import time

from historial import api
from motor_utils import entorno, envenenar, escribir  # noqa: F401


def _dos_versiones(entorno, ruta):
    escribir(ruta, 'v1', time.time() - 100)
    api.ejecutar(entorno.cfg)
    escribir(ruta, 'v1v2', time.time() - 50)
    api.ejecutar(entorno.cfg)
    return str(ruta)


def test_por_categoria_conserva_la_ultima_y_no_toca_otras(entorno):
    doc = _dos_versiones(entorno, entorno.origen / 'a.docx')
    jpg = _dos_versiones(entorno, entorno.origen / 'f.jpg')
    assert api.limpiar_filtrado(entorno.cfg, categoria='documentos') == 2
    restantes = api.versiones(entorno.cfg, doc)
    assert [v.tam for v in restantes] == [4] and os.path.exists(restantes[0].archivo)
    assert len(api.versiones(entorno.cfg, jpg)) == 2


def test_por_carpeta_e_incluso_la_ultima(entorno):
    dentro = _dos_versiones(entorno, entorno.origen / 'sub' / 'a.txt')
    fuera = _dos_versiones(entorno, entorno.origen / 'b.txt')
    carpeta = str(entorno.origen / 'sub')
    assert api.limpiar_filtrado(entorno.cfg, carpeta=carpeta, incluso_la_ultima=True) == 6
    assert api.versiones(entorno.cfg, dentro) == []
    assert len(api.versiones(entorno.cfg, fuera)) == 2
    assert api.uso(entorno.cfg).archivos == 1


def test_carpeta_con_prefijo_parecido_no_cuenta(entorno):
    _dos_versiones(entorno, entorno.origen / 'sub2' / 'a.txt')
    assert api.limpiar_filtrado(entorno.cfg, carpeta=str(entorno.origen / 'sub')) == 0


def test_anteriores_a_dias(entorno):
    ruta = entorno.origen / 'a.txt'
    escribir(ruta, 'v1', time.time() - 400 * 86400)
    api.ejecutar(entorno.cfg)
    escribir(ruta, 'v1v2', time.time() - 50)
    api.ejecutar(entorno.cfg)
    assert api.limpiar_filtrado(entorno.cfg, anteriores_a_dias=365, incluso_la_ultima=True) == 2
    assert [v.tam for v in api.versiones(entorno.cfg, str(ruta))] == [4]


def test_ruta_envenenada_no_borra_fuera_de_datos(entorno):
    _dos_versiones(entorno, entorno.origen / 'a.txt')
    secreto = entorno.raiz / 'secreto.txt'
    secreto.write_text('no tocar')
    envenenar(entorno, 'UPDATE versiones SET archivo=? WHERE id=1', '../../../../../secreto.txt')
    api.limpiar_filtrado(entorno.cfg, categoria='documentos')
    envenenar(entorno, 'UPDATE versiones SET archivo=? WHERE id=2', str(secreto))
    api.limpiar_filtrado(entorno.cfg, categoria='documentos', incluso_la_ultima=True)
    assert secreto.read_text() == 'no tocar'


def test_destino_desconectado_devuelve_cero(entorno):
    _dos_versiones(entorno, entorno.origen / 'a.txt')
    entorno.cfg.destino = str(entorno.raiz / 'no-existe')
    assert api.limpiar_filtrado(entorno.cfg, categoria='documentos') == 0
