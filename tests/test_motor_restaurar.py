"""Restauración: ubicación original, otra carpeta, conflictos y carpetas recursivas."""
import os

from historial import api
from motor_utils import entorno, escribir  # noqa: F401


def _entrada(cfg, ruta, version=0):
    return api.Entrada(os.path.basename(ruta), ruta, False, version_id=api.versiones(cfg, ruta)[version].id)


def _leer(ruta):
    with open(ruta, encoding='utf-8') as archivo:
        return archivo.read()


def test_restaurar_a_la_ubicacion_original_conserva_fecha(entorno):
    ruta = escribir(entorno.origen / 'a.txt', 'importante', 1_700_000_000)
    api.ejecutar(entorno.cfg)
    os.unlink(ruta)
    escritas = api.restaurar(entorno.cfg, [_entrada(entorno.cfg, ruta)])
    assert escritas == [ruta] and _leer(ruta) == 'importante'
    assert os.stat(ruta).st_mtime == 1_700_000_000


def test_restaurar_en_otra_carpeta(entorno):
    ruta = escribir(entorno.origen / 'sub' / 'a.txt', 'uno')
    api.ejecutar(entorno.cfg)
    otra = entorno.raiz / 'recuperado'
    escritas = api.restaurar(entorno.cfg, [_entrada(entorno.cfg, ruta)], destino_dir=str(otra))
    assert escritas == [str(otra / 'a.txt')] and _leer(otra / 'a.txt') == 'uno'
    assert _leer(ruta) == 'uno'


def test_restaurar_una_version_anterior(entorno):
    ruta = escribir(entorno.origen / 'a.txt', 'vieja')
    api.ejecutar(entorno.cfg)
    escribir(entorno.origen / 'a.txt', 'nueva y mas larga')
    api.ejecutar(entorno.cfg)
    api.restaurar(entorno.cfg, [_entrada(entorno.cfg, ruta, version=1)], conflicto='reemplazar')
    assert _leer(ruta) == 'vieja'


def test_conflicto_reemplazar_versiona_antes_el_archivo_actual(entorno):
    ruta = escribir(entorno.origen / 'a.txt', 'primera')
    api.ejecutar(entorno.cfg)
    escribir(entorno.origen / 'a.txt', 'edicion sin respaldar')       # cambió y aún no hay copia
    api.restaurar(entorno.cfg, [_entrada(entorno.cfg, ruta)], conflicto='reemplazar')
    assert _leer(ruta) == 'primera'
    textos = [_leer(v.archivo) for v in api.versiones(entorno.cfg, ruta)]
    assert 'edicion sin respaldar' in textos


def test_conflicto_omitir_y_renombrar(entorno):
    ruta = escribir(entorno.origen / 'a.txt', 'copia')
    api.ejecutar(entorno.cfg)
    escribir(entorno.origen / 'a.txt', 'actual distinto')
    entrada = _entrada(entorno.cfg, ruta)
    assert api.restaurar(entorno.cfg, [entrada], conflicto='omitir') == []
    assert _leer(ruta) == 'actual distinto'
    escritas = api.restaurar(entorno.cfg, [entrada], conflicto='renombrar')
    assert escritas == [str(entorno.origen / 'a (2).txt')]
    assert _leer(ruta) == 'actual distinto' and _leer(escritas[0]) == 'copia'
    assert api.restaurar(entorno.cfg, [entrada], conflicto='renombrar') == [str(entorno.origen / 'a (3).txt')]


def test_conflicto_preguntar_usa_la_decision(entorno):
    ruta = escribir(entorno.origen / 'a.txt', 'copia')
    api.ejecutar(entorno.cfg)
    escribir(entorno.origen / 'a.txt', 'actual')
    consultas = []

    def decidir(existente, version):
        consultas.append((existente, version.tam))
        return 'omitir'

    assert api.restaurar(entorno.cfg, [_entrada(entorno.cfg, ruta)], decidir=decidir) == []
    assert consultas == [(ruta, len('copia'))]
    sin_decidir = api.restaurar(entorno.cfg, [_entrada(entorno.cfg, ruta)])
    assert sin_decidir == [str(entorno.origen / 'a (2).txt')]         # sin decidir: no pierde nada
