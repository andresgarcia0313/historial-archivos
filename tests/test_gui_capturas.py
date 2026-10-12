"""Abre cada pantalla contra el motor falso y guarda una captura (HISTORIAL_CAPTURAS = carpeta de salida)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, esperar, falso  # noqa: F401,E402

from historial.gui import avanzada, conflicto, textos, unidad, unidades  # noqa: E402
from historial.gui.excluir import Excluir  # noqa: E402
from historial.gui.limpiar import Limpiar  # noqa: E402
from historial.gui.panel import Panel  # noqa: E402
from historial.gui.restaurar import Restaurar  # noqa: E402
from historial.gui.versiones import Versiones  # noqa: E402


def _guardar(widget, nombre, destino):
    widget.show()
    widget.repaint()
    ruta = os.path.join(destino, f'gui-{nombre}.png')
    assert widget.grab().save(ruta), ruta
    assert os.path.getsize(ruta) > 2000
    widget.close()


def test_capturas_de_todas_las_pantallas(app, falso, monkeypatch, tmp_path):
    salida = os.environ.get('HISTORIAL_CAPTURAS') or str(tmp_path / 'capturas')
    os.makedirs(salida, exist_ok=True)
    monkeypatch.setattr(unidades, 'detectar', lambda *a, **k: [
        unidades.Unidad('Disco externo', '/media/usuario/Disco externo', 380 * 2**30, 465 * 2**30),
        unidades.Unidad('Respaldo', '/run/media/usuario/Respaldo', 1500 * 2**30, 1863 * 2**30)])
    falso.cfg.destino, falso.cfg.excluir = '/media/usuario/Disco externo', [falso.base + '/Documentos/Borradores']
    p = Panel()
    _guardar(p, 'panel-desactivado', salida)
    falso.cfg.activo = True
    p = Panel()
    _guardar(p, 'panel-activado', salida)
    p.ejecutar()
    assert esperar(app, lambda: p.derecha.progreso.isVisibleTo(p))
    _guardar(p, 'panel-copiando', salida)
    _guardar(unidad.Unidad(falso.cfg), 'seleccionar-unidad', salida)
    _guardar(Excluir(falso.cfg), 'excluir-carpetas', salida)
    _guardar(avanzada.Avanzada(falso.cfg), 'configuracion-avanzada', salida)
    _guardar(Limpiar(falso.cfg), 'limpiar-versiones', salida)
    r = Restaurar()
    _guardar(r, 'restaurar-inicio', salida)
    r = Restaurar(falso.docs)
    r.c.vista.setCurrentIndex(r.c.vista.modelo.index(0, 0))
    _guardar(r, 'restaurar-carpeta', salida)
    r.mover(-2)
    _guardar(r, 'restaurar-punto-1', salida)
    _guardar(conflicto.DialogoConflicto(os.path.join(falso.docs, 'informe.txt'), falso.version(2)), 'conflicto', salida)
    _guardar(Versiones(os.path.join(falso.docs, 'informe.txt')), 'versiones-anteriores', salida)
    textos.fijar('en')
    try:
        _guardar(Panel(), 'panel-ingles', salida)
        _guardar(Restaurar(falso.docs), 'restaurar-ingles', salida)
    finally:
        textos.fijar(None)
    assert len([f for f in os.listdir(salida) if f.startswith('gui-')]) >= 13
