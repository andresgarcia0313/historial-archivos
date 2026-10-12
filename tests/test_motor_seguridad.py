"""Un catálogo que viene del destino no es de fiar: copias y rutas fuera de lo permitido."""
import os
import pytest

from historial import api
from motor_utils import con_dos_versiones, entorno, entrada_de, envenenar, escribir  # noqa: F401


@pytest.mark.parametrize('archivo', ['relativo', 'absoluto'])
def test_copia_fuera_de_datos_no_se_lee_ni_se_borra(entorno, archivo):
    ruta, antigua, secreto = con_dos_versiones(entorno)
    malo = '../' * 12 + 'secreto.txt'
    if archivo == 'absoluto':
        malo = str(secreto)
    envenenar(entorno, 'UPDATE versiones SET archivo=? WHERE id=?', malo, antigua.id)
    assert [v.tam for v in api.versiones(entorno.cfg, ruta)] == [len('segunda mas larga')]
    salida = entorno.raiz / 'salida'
    assert api.restaurar(entorno.cfg, [entrada_de(ruta, antigua.id)], destino_dir=str(salida)) == []
    assert api.limpiar(entorno.cfg, None) == 0
    assert secreto.read_text() == 'no tocar'


def test_enlace_simbolico_que_sale_de_datos(entorno):
    ruta, antigua, secreto = con_dos_versiones(entorno)
    os.unlink(antigua.archivo)
    os.symlink(secreto, antigua.archivo)
    assert all(v.id != antigua.id for v in api.versiones(entorno.cfg, ruta))
    assert api.restaurar(entorno.cfg, [entrada_de(ruta, antigua.id)], destino_dir=str(entorno.raiz / 'o')) == []
    api.limpiar(entorno.cfg, None)
    assert secreto.read_text() == 'no tocar'


def test_carpeta_enlazada_dentro_de_datos_que_sale(entorno):
    ruta, antigua, secreto = con_dos_versiones(entorno)
    carpeta = os.path.dirname(antigua.archivo)
    os.rename(carpeta, carpeta + '_real')
    os.symlink(entorno.raiz, carpeta)                                # Datos/.../Documentos -> fuera
    assert api.versiones(entorno.cfg, ruta) == []
    assert secreto.read_text() == 'no tocar' and api.limpiar(entorno.cfg, None) == 0


@pytest.mark.parametrize('malo', ['/home/x/../../etc/passwd', 'relativa/x.txt'])
def test_ruta_original_invalida_en_el_catalogo_se_ignora(entorno, malo):
    ruta, antigua, _ = con_dos_versiones(entorno)
    envenenar(entorno, 'UPDATE versiones SET ruta=? WHERE id=?', malo, antigua.id)
    punto = api.puntos(entorno.cfg)[0].id
    assert api.versiones(entorno.cfg, malo) == []
    assert api.listar(entorno.cfg, punto, str(entorno.origen)) == []


def test_ruta_original_fuera_de_las_carpetas_protegidas_no_se_restaura(entorno):
    ruta, antigua, _ = con_dos_versiones(entorno)
    fuera = entorno.raiz / 'fuera' / 'x.txt'
    envenenar(entorno, 'UPDATE versiones SET ruta=? WHERE id=?', str(fuera), antigua.id)
    assert api.restaurar(entorno.cfg, [entrada_de(str(fuera), antigua.id, 'x.txt')]) == []
    assert not fuera.exists()
    assert api.restaurar(entorno.cfg, [entrada_de(str(fuera), antigua.id, 'x.txt')], destino_dir=str(entorno.raiz / 'ok')) \
        == [str(entorno.raiz / 'ok' / 'x.txt')]
