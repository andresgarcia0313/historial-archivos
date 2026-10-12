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


def test_patrones_exclusiones_y_tamano(entorno):
    for nombre in ('ok.txt', 'basura.tmp', '~$doc.docx', 'node_modules/x.js', 'privado/s.txt', 'grande.bin'):
        escribir(entorno.origen / nombre, 'x' * 10)
    (entorno.origen / 'grande.bin').write_bytes(b'0' * (2 << 20))
    entorno.cfg.excluir = [str(entorno.origen / 'privado')]
    entorno.cfg.max_tam_mb = 1
    api.ejecutar(entorno.cfg)
    copiados = nombres_en(entorno.destino / 'HistorialArchivos' / '..' / 'HistorialArchivos')
    assert [n.split(' (')[0] for n in copiados if 'UTC' in n] == ['ok']


def test_destino_dentro_de_la_carpeta_protegida_no_se_copia_a_si_mismo(entorno):
    entorno.cfg.destino = str(entorno.origen / 'respaldo')
    (entorno.origen / 'respaldo').mkdir()
    escribir(entorno.origen / 'a.txt', 'uno')
    api.ejecutar(entorno.cfg)
    assert api.ejecutar(entorno.cfg).copiados == 0
    assert len(nombres_en(entorno.origen / 'respaldo')) == 2         # copia de a.txt + catálogo


def test_no_cruza_sistemas_de_archivos_ni_sigue_enlaces(entorno, monkeypatch):
    escribir(entorno.origen / 'local.txt', 'l')
    escribir(entorno.origen / 'montaje' / 'remoto.txt', 'r')
    afuera = entorno.raiz / 'afuera'
    escribir(afuera / 'enlazado.txt', 'e')
    (entorno.origen / 'enlace').symlink_to(afuera, target_is_directory=True)
    original = escaneo._dispositivo
    monkeypatch.setattr(escaneo, '_dispositivo',
                        lambda ruta, info: 999 if ruta.endswith('montaje') else original(ruta, info))
    resumen = api.ejecutar(entorno.cfg)
    assert resumen.copiados == 1                                     # solo local.txt
    assert api.versiones(entorno.cfg, str(entorno.origen / 'montaje' / 'remoto.txt')) == []


def test_un_montaje_que_aparece_no_se_da_por_borrado(entorno, monkeypatch):
    escribir(entorno.origen / 'datos' / 'x.txt', 'x')
    api.ejecutar(entorno.cfg)
    original = escaneo._dispositivo
    monkeypatch.setattr(escaneo, '_dispositivo',
                        lambda ruta, info: 999 if ruta.endswith('datos') else original(ruta, info))
    api.ejecutar(entorno.cfg)
    assert len(api.puntos(entorno.cfg)) == 1
    punto = api.puntos(entorno.cfg)[0].id
    assert [e.nombre for e in api.listar(entorno.cfg, punto, str(entorno.origen / 'datos'))] == ['x.txt']
    vigentes = api.listar(entorno.cfg, punto + 1, str(entorno.origen / 'datos'))
    assert [e.nombre for e in vigentes] == ['x.txt']                 # sigue vigente en puntos futuros


def test_destino_inexistente_no_falla_ni_se_crea(entorno):
    entorno.cfg.destino = str(entorno.raiz / 'no_montada')
    escribir(entorno.origen / 'a.txt', 'uno')
    resumen = api.ejecutar(entorno.cfg)
    assert resumen.copiados == 0 and resumen.errores == ['Reconecte la unidad']
    assert not (entorno.raiz / 'no_montada').exists()
    estado = api.estado(entorno.cfg)
    assert not estado.destino_conectado and estado.error == 'Reconecte la unidad'


def test_punto_de_montaje_vacio_tras_haber_copiado(entorno):
    escribir(entorno.origen / 'a.txt', 'uno')
    api.ejecutar(entorno.cfg)
    shutil.rmtree(entorno.destino / 'HistorialArchivos')             # la unidad se desmontó: queda la carpeta vacía
    escribir(entorno.origen / 'a.txt', 'cambio')
    resumen = api.ejecutar(entorno.cfg)
    assert resumen.errores == ['Reconecte la unidad']
    assert list(entorno.destino.iterdir()) == []
    assert api.estado(entorno.cfg).error == 'Reconecte la unidad'


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


def test_copia_en_curso_bloquea_otra(entorno):
    from historial import bloqueo
    escribir(entorno.origen / 'a.txt', 'uno')
    with bloqueo.tomar() as libre:
        assert libre and api.estado(entorno.cfg).en_curso
        assert api.ejecutar(entorno.cfg).errores == ['Ya hay una copia en curso']
    assert api.ejecutar(entorno.cfg).copiados == 1
