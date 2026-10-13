"""Categorías por extensión, filtros de copia por tipo y compatibilidad de config.json viejos."""
import json

from historial import api, config
from motor_utils import entorno, escribir, nombres_en  # noqa: F401


def test_categoria_por_extension():
    assert api.categoria_de('Informe.DOCX') == 'documentos'
    assert api.categoria_de('foto.jpeg') == 'imagenes'
    assert api.categoria_de('respaldo.tar.gz') == 'comprimidos'
    assert api.categoria_de('/home/x/Makefile') == 'otros'
    assert api.categoria_de('.bashrc') == 'otros'
    assert api.categoria_de('raro.xyz') == 'otros'
    assert set(api.CATEGORIAS) >= {'documentos', 'hojas', 'imagenes', 'codigo'}


def _copiados(entorno):
    return sorted(n.split(' (')[0] for n in nombres_en(entorno.destino / 'HistorialArchivos') if 'UTC' in n)


def test_filtro_por_tipos_copia_solo_las_categorias_elegidas(entorno):
    for nombre in ('a.docx', 'b.jpg', 'c.py', 'sin_ext'):
        escribir(entorno.origen / nombre, 'x')
    entorno.cfg.tipos = ['documentos', 'imagenes']
    api.ejecutar(entorno.cfg)
    assert _copiados(entorno) == ['a', 'b']


def test_tipo_otros_incluye_lo_sin_categoria(entorno):
    for nombre in ('a.docx', 'sin_ext'):
        escribir(entorno.origen / nombre, 'x')
    entorno.cfg.tipos = ['otros']
    api.ejecutar(entorno.cfg)
    assert _copiados(entorno) == ['sin_ext']


def test_extension_excluida_nunca_se_copia(entorno):
    for nombre in ('a.txt', 'b.ISO', 'c.log'):
        escribir(entorno.origen / nombre, 'x')
    entorno.cfg.extensiones_excluidas = ['iso', '.LOG']
    api.ejecutar(entorno.cfg)
    assert _copiados(entorno) == ['a']


def test_excluir_un_tipo_despues_no_da_por_borrado_lo_ya_copiado(entorno):
    ruta = escribir(entorno.origen / 'b.jpg', 'x')
    api.ejecutar(entorno.cfg)
    entorno.cfg.tipos = ['documentos']
    escribir(entorno.origen / 'a.txt', 'y')
    api.ejecutar(entorno.cfg)
    ultimo = api.puntos(entorno.cfg)[-1].id
    nombres = [e.nombre for e in api.listar(entorno.cfg, ultimo, str(entorno.origen))]
    assert 'b.jpg' in nombres and len(api.versiones(entorno.cfg, ruta)) == 1


def test_config_vieja_sin_campos_nuevos_carga_con_valores_por_defecto(entorno):
    carpeta = entorno.home / '.config' / 'historial-archivos'
    carpeta.mkdir(parents=True)
    (carpeta / 'config.json').write_text(json.dumps({'activo': True, 'destino': '/x', 'frecuencia_min': 60}))
    cfg = config.cargar()
    assert cfg.tipos == [] and cfg.extensiones_excluidas == [] and cfg.destino == '/x'


def test_config_con_campos_nuevos_ida_y_vuelta(entorno):
    entorno.cfg.tipos, entorno.cfg.extensiones_excluidas = ['hojas'], ['bak']
    config.guardar(entorno.cfg)
    cfg = config.cargar()
    assert cfg.tipos == ['hojas'] and cfg.extensiones_excluidas == ['bak']
