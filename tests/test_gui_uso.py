"""Página "Uso del espacio" y navegación del panel lateral."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, esperar, falso  # noqa: F401,E402

from historial.gui import uso_limpiar  # noqa: E402
from historial.gui.panel import Panel  # noqa: E402
from historial.gui.uso_pagina import UsoPagina  # noqa: E402


def _cargada(app, pagina):
    pagina.al_mostrar()
    assert esperar(app, lambda: pagina.tarea is None)
    return pagina


def test_el_lateral_lleva_a_cada_pagina_y_conserva_los_enlaces_de_windows(app, falso):
    p = Panel()
    nombres = [b.text() for b in p.lateral.paginas]
    assert nombres == ['Historial de archivos', 'Uso del espacio', 'Tipos de archivo', 'Otras copias de seguridad']
    assert p.lateral.paginas[0].isChecked() and p.paginas.currentWidget() is p.derecha
    p.lateral.paginas[1].click()
    assert p.paginas.currentWidget() is p.uso and p.lateral.paginas[1].isChecked()
    assert esperar(app, lambda: p.uso.tarea is None)
    p.lateral.paginas[0].click()
    assert p.paginas.currentWidget() is p.derecha


def test_cifras_graficos_y_tablas(app, falso):
    u = _cargada(app, UsoPagina(falso.cfg))
    assert u.cifras['cifra_copias'].valor.text() == '72,1 GB'
    assert u.cifras['cifra_libre'].detalle.text() == 'de 465 GB'
    assert u.cifras['cifra_archivos'].valor.text() == '18.508'
    assert u.cifras['cifra_versiones'].detalle.text() == '1,9 por archivo en promedio'
    assert u.cifras['cifra_primera'].valor.text() == '04/01/2026'
    assert [d[0] for d in u.por_tipo.datos][:3] == ['Imágenes', 'Videos', 'Documentos']
    assert [d[0] for d in u.por_carpeta.datos] == ['Imagenes', 'Documentos']
    assert u.por_mes.datos[0][0] == '01/26' and len(u.por_mes.datos) == 10
    assert 'Imágenes: 41,0 GB' in u.por_tipo.accessibleDescription()
    assert u.tablas.grandes.rowCount() == 6 and u.tablas.grandes.item(0, 0).text() == 'video-familia-0.mp4'
    assert u.tablas.versionados.item(0, 3).text() == '140'
    assert u.cifras.isVisibleTo(u) and not u.estado.isVisibleTo(u)


def test_sin_copias_muestra_estado_vacio(app, falso):
    falso.uso.versiones = 0
    u = _cargada(app, UsoPagina(falso.cfg))
    assert u.estado.text().startswith('Todavía no hay copias') and not u.cifras.isVisibleTo(u)


def test_limpiar_por_tipo_y_carpeta_confirma_y_recarga(app, falso, monkeypatch):
    preguntas = []
    monkeypatch.setattr(uso_limpiar, 'confirmar', lambda padre, texto: preguntas.append(texto) or len(preguntas) > 1)
    u = _cargada(app, UsoPagina(falso.cfg))
    lim = u.limpieza
    lim.tipo.setCurrentIndex(lim.tipo.findData('videos'))
    lim.carpeta.setCurrentIndex(lim.carpeta.findData(falso.imgs))
    lim.boton.click()                                              # primera vez: cancela
    assert falso.limpiezas == [] and 'Videos, Imagenes' in preguntas[0]
    lim.ultima.setChecked(True)
    lim.boton.click()
    assert esperar(app, lambda: falso.limpiezas and lim.boton.isEnabled() and u.tarea is None)
    assert falso.limpiezas == [{'categoria': 'videos', 'carpeta': falso.imgs, 'anteriores_a_dias': 365,
                                'incluso_la_ultima': True}]
    assert 'TODAS' in preguntas[1] and lim.resultado.text() == 'Se liberaron 3,0 GB.'
