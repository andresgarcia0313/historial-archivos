"""Retención y limpieza de versiones."""
import os
import time
from types import SimpleNamespace

from historial import api, retencion
from motor_utils import entorno, escribir  # noqa: F401

DIA = 86400


def _versiones_con_edades(entorno, dias_atras):
    """Una versión por cada edad (en días), de la más vieja a la más reciente."""
    ruta = str(entorno.origen / 'a.txt')
    for i, dias in enumerate(dias_atras):
        escribir(entorno.origen / 'a.txt', 'v' * (i + 1), time.time() - dias * DIA)
        api.ejecutar(entorno.cfg)
    return ruta


def test_limpiar_todas_menos_la_mas_reciente(entorno):
    ruta = _versiones_con_edades(entorno, [30, 20, 10])
    otra = escribir(entorno.origen / 'sub' / 'unica.txt', 'sola')
    api.ejecutar(entorno.cfg)
    liberado = api.limpiar(entorno.cfg, None)
    assert liberado == 1 + 2
    restantes = api.versiones(entorno.cfg, ruta)
    assert [v.tam for v in restantes] == [3] and os.path.exists(restantes[0].archivo)
    assert len(api.versiones(entorno.cfg, otra)) == 1


def test_limpiar_anteriores_a_n_dias(entorno):
    ruta = _versiones_con_edades(entorno, [500, 400, 5])
    assert api.limpiar(entorno.cfg, 365) == 1 + 2
    assert [v.tam for v in api.versiones(entorno.cfg, ruta)] == [3]
    assert api.limpiar(entorno.cfg, 365) == 0


def test_limpiar_quita_carpetas_vacias_y_puntos_sin_contenido(entorno):
    _versiones_con_edades(entorno, [50, 40])
    api.limpiar(entorno.cfg, None)
    assert len(api.puntos(entorno.cfg)) == 1
    datos = [p for p in (entorno.destino / 'HistorialArchivos').rglob('*') if p.is_file()]
    assert len(datos) == 2                                           # última copia + catálogo


def test_conservar_dias_se_aplica_al_terminar_la_copia(entorno):
    entorno.cfg.conservar_dias = 30
    ruta = _versiones_con_edades(entorno, [200, 100, 3])
    assert [v.tam for v in api.versiones(entorno.cfg, ruta)] == [3]


def test_siempre_conserva_todo(entorno):
    entorno.cfg.conservar_dias = 0
    ruta = _versiones_con_edades(entorno, [900, 800, 3])
    assert len(api.versiones(entorno.cfg, ruta)) == 3


def test_hasta_que_se_necesite_espacio_borra_las_mas_antiguas(entorno, monkeypatch):
    entorno.cfg.conservar_dias = -1

    def disco(ruta):                                                 # cada copia ocupa 10 de 100
        copias = sum(len(archivos) for _, _, archivos in os.walk(entorno.destino / 'HistorialArchivos'))
        return SimpleNamespace(total=100, used=10 * copias, free=100 - 10 * copias)

    monkeypatch.setattr(retencion.shutil, 'disk_usage', disco)
    ruta = _versiones_con_edades(entorno, [60, 50, 40, 30, 20, 10, 5, 4, 3, 2, 1])
    versiones = api.versiones(entorno.cfg, ruta)
    assert versiones and versiones[0].tam == 11                      # la más reciente nunca se borra
    assert len(versiones) < 11                                       # se borraron antiguas hasta tener 10 % libre
    assert [v.tam for v in versiones] == sorted((v.tam for v in versiones), reverse=True)


def test_limpiar_con_destino_desconectado_no_toca_el_catalogo(entorno):
    ruta = _versiones_con_edades(entorno, [30, 5])
    entorno.cfg.destino = str(entorno.raiz / 'ausente')
    assert api.limpiar(entorno.cfg, None) == 0
    entorno.cfg.destino = str(entorno.destino)
    assert len(api.versiones(entorno.cfg, ruta)) == 2
