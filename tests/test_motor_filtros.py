"""Filtros de escaneo, montajes, destino desconectado y bloqueo."""
import os
import shutil

from historial import api, escaneo
from motor_utils import entorno, escribir, nombres_en  # noqa: F401


def test_patrones_exclusiones_y_tamano(entorno):
    for nombre in ('ok.txt', 'basura.tmp', '~$doc.docx', 'node_modules/x.js', 'privado/s.txt', 'grande.bin'):
        escribir(entorno.origen / nombre, 'x' * 10)
    (entorno.origen / 'grande.bin').write_bytes(b'0' * (2 << 20))
    entorno.cfg.excluir = [str(entorno.origen / 'privado')]
    entorno.cfg.max_tam_mb = 1
    api.ejecutar(entorno.cfg)
    copiados = nombres_en(entorno.destino / 'HistorialArchivos')
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


def test_copia_en_curso_bloquea_otra(entorno):
    from historial import bloqueo
    escribir(entorno.origen / 'a.txt', 'uno')
    with bloqueo.tomar() as libre:
        assert libre and api.estado(entorno.cfg).en_curso
        assert api.ejecutar(entorno.cfg).errores == ['Ya hay una copia en curso']
    assert api.ejecutar(entorno.cfg).copiados == 1
