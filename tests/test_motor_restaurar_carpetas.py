"""Restauración recursiva de carpetas."""
import os

from historial import api
from motor_utils import entorno, escribir  # noqa: F401


def test_carpeta_recursiva_en_un_punto_anterior(entorno):
    escribir(entorno.origen / 'p' / 'a.txt', 'a')
    escribir(entorno.origen / 'p' / 'hondo' / 'b.txt', 'bb')
    api.ejecutar(entorno.cfg)
    (entorno.origen / 'p' / 'a.txt').unlink()
    escribir(entorno.origen / 'p' / 'nuevo.txt', 'n')
    api.ejecutar(entorno.cfg)
    primero = api.puntos(entorno.cfg)[0].id
    carpeta = api.Entrada('p', str(entorno.origen / 'p'), True)
    destino = entorno.raiz / 'salida'
    escritas = api.restaurar(entorno.cfg, [carpeta], destino_dir=str(destino), punto_id=primero)
    relativas = sorted(os.path.relpath(r, destino) for r in escritas)
    assert relativas == ['p/a.txt', 'p/hondo/b.txt']
    reciente = api.restaurar(entorno.cfg, [carpeta], destino_dir=str(entorno.raiz / 'salida2'))
    assert sorted(os.path.basename(r) for r in reciente) == ['b.txt', 'nuevo.txt']


def test_carpeta_a_la_ubicacion_original_tras_borrarla(entorno):
    escribir(entorno.origen / 'p' / 'a.txt', 'a')
    api.ejecutar(entorno.cfg)
    os.unlink(entorno.origen / 'p' / 'a.txt')
    api.ejecutar(entorno.cfg)
    primero = api.puntos(entorno.cfg)[0].id
    api.restaurar(entorno.cfg, [api.Entrada('p', str(entorno.origen / 'p'), True)], punto_id=primero)
    assert (entorno.origen / 'p' / 'a.txt').read_text() == 'a'
