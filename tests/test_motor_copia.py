"""Copia inicial, incremental, versiones, borrados, filtros y destino desconectado."""
import os
import re
import shutil

from historial import api, escaneo
from motor_utils import entorno, escribir, nombres_en  # noqa: F401

SELLO = r' \(\d{4}_\d\d_\d\d \d\d_\d\d_\d\d UTC\)'


def test_copia_inicial_con_nombre_estilo_windows(entorno):
    escribir(entorno.origen / 'a.txt', 'uno', 1_700_000_000)
    escribir(entorno.origen / 'sub' / 'b.md', 'dos', 1_700_000_100)
    resumen = api.ejecutar(entorno.cfg)
    assert (resumen.revisados, resumen.copiados, resumen.errores) == (2, 2, [])
    copias = nombres_en(entorno.destino / 'HistorialArchivos')
    assert any(re.fullmatch(rf'a{SELLO}\.txt', n) for n in copias)
    assert any(re.fullmatch(rf'b{SELLO}\.md', n) for n in copias)
    assert not [n for n in copias if n.endswith('.part')]
    version = api.versiones(entorno.cfg, str(entorno.origen / 'a.txt'))[0]
    assert os.stat(version.archivo).st_mtime == 1_700_000_000        # conserva la fecha
    assert (entorno.home / '.local/share/historial-archivos/catalogo.sqlite').exists()
    assert 'catalogo.sqlite' in copias


def test_incremental_sin_cambios_no_copia_nada(entorno):
    escribir(entorno.origen / 'a.txt', 'uno')
    api.ejecutar(entorno.cfg)
    puntos = len(api.puntos(entorno.cfg))
    resumen = api.ejecutar(entorno.cfg)
    assert (resumen.revisados, resumen.copiados) == (1, 0)
    assert len(api.puntos(entorno.cfg)) == puntos                    # sin cambios no hay punto nuevo


def test_cambio_crea_version_nueva(entorno):
    ruta = escribir(entorno.origen / 'a.txt', 'primera')
    api.ejecutar(entorno.cfg)
    escribir(entorno.origen / 'a.txt', 'segunda version')
    assert api.ejecutar(entorno.cfg).copiados == 1
    versiones = api.versiones(entorno.cfg, ruta)
    assert [v.tam for v in versiones] == [len('segunda version'), len('primera')]
    assert open(versiones[0].archivo).read() == 'segunda version'
    assert open(versiones[1].archivo).read() == 'primera'
    assert len(api.puntos(entorno.cfg)) == 2


def test_borrado_sigue_visible_en_puntos_anteriores(entorno):
    escribir(entorno.origen / 'a.txt', 'uno')
    escribir(entorno.origen / 'b.txt', 'dos')
    api.ejecutar(entorno.cfg)
    (entorno.origen / 'a.txt').unlink()
    assert api.ejecutar(entorno.cfg).copiados == 0
    antes, despues = api.puntos(entorno.cfg)
    carpeta = str(entorno.origen)
    assert [e.nombre for e in api.listar(entorno.cfg, antes.id, carpeta)] == ['a.txt', 'b.txt']
    assert [e.nombre for e in api.listar(entorno.cfg, despues.id, carpeta)] == ['b.txt']


def test_listar_raiz_y_carpetas_primero(entorno):
    escribir(entorno.origen / 'z.txt', 'z')
    escribir(entorno.origen / 'carpeta' / 'dentro.txt', 'x')
    api.ejecutar(entorno.cfg)
    punto = api.puntos(entorno.cfg)[-1].id
    raiz = api.listar(entorno.cfg, punto, '')
    assert [(e.nombre, e.es_carpeta) for e in raiz] == [('Documentos', True)]
    hijos = api.listar(entorno.cfg, punto, str(entorno.origen))
    assert [(e.nombre, e.es_carpeta, e.version_id is None) for e in hijos] == [
        ('carpeta', True, True), ('z.txt', False, False)]


def test_estado_tras_copiar(entorno):
    escribir(entorno.origen / 'a.txt', 'contenido')
    api.ejecutar(entorno.cfg)
    estado = api.estado(entorno.cfg)
    assert estado.destino_conectado and estado.ultima_copia is not None
    assert estado.tam_copias == len('contenido') and estado.libre > 0 and not estado.en_curso


def test_si_falta_el_catalogo_local_se_lee_el_del_destino(entorno):
    ruta = escribir(entorno.origen / 'a.txt', 'uno')
    api.ejecutar(entorno.cfg)
    (entorno.home / '.local/share/historial-archivos/catalogo.sqlite').unlink()
    assert len(api.versiones(entorno.cfg, ruta)) == 1
    assert api.ejecutar(entorno.cfg).copiados == 0


def test_cambiar_de_unidad_vuelve_a_copiar_todo(entorno):
    escribir(entorno.origen / 'a.txt', 'uno')
    api.ejecutar(entorno.cfg)
    nueva = entorno.raiz / 'otra'
    nueva.mkdir()
    entorno.cfg.destino = str(nueva)
    assert api.ejecutar(entorno.cfg).copiados == 1
