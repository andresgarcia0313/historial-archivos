"""Entradas maliciosas al restaurar: nombres con subidas, rutas con .. y destinos enlazados."""
import os
import pytest

from historial import api
from motor_utils import con_dos_versiones, entorno, entrada_de, envenenar, escribir  # noqa: F401


@pytest.mark.parametrize('nombre', ['../escape.txt', '/tmp/escape.txt', '..', ''])
def test_nombre_deentrada_de_malicioso_no_escapa_de_destino_dir(entorno, nombre):
    ruta, antigua, _ = con_dos_versiones(entorno)
    salida = entorno.raiz / 'salida'
    assert api.restaurar(entorno.cfg, [entrada_de(ruta, antigua.id, nombre)], destino_dir=str(salida)) == []
    assert not (entorno.raiz / 'escape.txt').exists()


def test_carpeta_con_nombre_de_subida_no_restaura_nada(entorno):
    con_dos_versiones(entorno)
    carpeta = api.Entrada('..', str(entorno.origen), True)
    assert api.restaurar(entorno.cfg, [carpeta], destino_dir=str(entorno.raiz / 'salida'), conflicto='omitir') == []


def testentrada_de_original_con_subidas_se_rechaza(entorno):
    ruta, antigua, _ = con_dos_versiones(entorno)
    camino = str(entorno.origen) + '/../../../escape.txt'
    assert api.restaurar(entorno.cfg, [entrada_de(camino, antigua.id, 'escape.txt')]) == []
    assert not (entorno.raiz / 'escape.txt').exists()


def test_destino_enlace_que_sale_no_se_sigue_al_restaurar(entorno):
    ruta, antigua, secreto = con_dos_versiones(entorno)
    salida = entorno.raiz / 'salida'
    salida.mkdir()
    (salida / 'a.txt').symlink_to(secreto)
    assert api.restaurar(entorno.cfg, [entrada_de(ruta, antigua.id)], destino_dir=str(salida),
                         conflicto='reemplazar') == []
    assert secreto.read_text() == 'no tocar'
