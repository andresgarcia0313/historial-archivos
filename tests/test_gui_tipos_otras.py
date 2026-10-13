"""Páginas "Tipos de archivo" y "Otras copias de seguridad", y el filtro por tipo de Restaurar."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, esperar, falso  # noqa: F401,E402

from historial.gui import otras_pagina, tipos_pagina  # noqa: E402
from historial.gui.otras_editar import EditarCopia  # noqa: E402
from historial.gui.restaurar import Restaurar  # noqa: E402


def test_tipos_vacio_es_todos_y_guarda_lo_elegido(app, falso):
    p = tipos_pagina.TiposPagina(falso.cfg)
    assert p.todos.isChecked() and all(c.isChecked() for c in p.casillas.values())
    assert list(p.casillas)[-1] == 'otros' and p.casillas['imagenes'].text() == 'Imágenes'
    p.todos.setChecked(False)
    for categoria, casilla in p.casillas.items():
        casilla.setChecked(categoria in ('documentos', 'hojas'))
    p.extensiones.setText(' .ISO, vmdk;log iso ')
    p.guardar.click()
    assert falso.cfg.tipos == ['documentos', 'hojas'] and falso.cfg.extensiones_excluidas == ['iso', 'vmdk', 'log']
    assert falso.guardados and p.resultado.text() == 'Se guardaron los cambios.'
    for casilla in p.casillas.values():
        casilla.setChecked(False)
    p.guardar.click()
    assert p.resultado.text() == 'Elija al menos un tipo de archivo.' and falso.cfg.tipos == ['documentos', 'hojas']


def test_otras_copias_tarjetas_tamano_y_abrir(app, falso, monkeypatch):
    avisos = []
    monkeypatch.setattr(otras_pagina, 'aviso', lambda padre, texto: avisos.append(texto))
    p = otras_pagina.OtrasPagina()
    p.al_mostrar()
    assert esperar(app, lambda: len(p.tarjetas) == 3 and p.tarjetas[1].tam.text() == '12,0 GB')
    assert esperar(app, lambda: p.tarjetas[0].tam.text() == 'No se puede medir')
    t0, t1, t2 = p.tarjetas
    assert t1.titulo.text() == 'Back In Time - Servidor' and t1.pildora.text() == 'Activa'
    assert t0.pildora.objectName() == 'pildora_no' and not t2.boton_editar.isVisibleTo(t2)
    t2.boton_abrir.click()
    assert avisos == ['No se encontró la aplicación de Timeshift en este equipo.']
    t1.boton_abrir.click()
    assert falso.abiertas == ['timeshift', 'backintime:2']


def test_editar_copia_guarda_una_copia_nueva(app, falso, monkeypatch):
    avisos = []
    monkeypatch.setattr(otras_pagina, 'aviso', lambda padre, texto: avisos.append(texto))
    original = falso.otras_copias[1]
    d = EditarCopia(original)
    assert d.frecuencia.currentData() == 1440 and d.incluidas.rutas() == original.carpetas
    d.activa.setChecked(False)
    d.excluidas.poner('/home/usuario/Proyectos/tmp')
    nueva = d.resultado()
    assert nueva.activa is False and nueva.excluir == ['/home/usuario/Proyectos/tmp'] and original.activa
    monkeypatch.setattr(otras_pagina.EditarCopia, 'exec', lambda self: (self.activa.setChecked(False), 1)[1])
    p = otras_pagina.OtrasPagina()
    p.editar(original)
    assert falso.guardadas[-1].activa is False and avisos[-1].startswith('Se guardaron los cambios')
    assert esperar(app, lambda: not p.buscando)


def test_restaurar_filtra_por_tipo(app, falso):
    r = Restaurar(falso.docs)
    nombres = lambda: [e.nombre for e in r.c.vista.entradas()]  # noqa: E731
    assert nombres() == ['foto.png', 'informe.txt', 'notas.md']
    r.c.tipo.setCurrentIndex(r.c.tipo.findData('imagenes'))
    assert nombres() == ['foto.png']
    r.c.buscar.setText('inf')
    assert nombres() == []
    r.c.tipo.setCurrentIndex(0)
    assert nombres() == ['informe.txt']
