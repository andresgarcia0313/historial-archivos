"""Capturas de cada pantalla en Drácula y en Alucard (HISTORIAL_CAPTURAS = carpeta de salida)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from test_gui_comun import app, esperar, falso  # noqa: F401,E402

import pytest  # noqa: E402

from historial.gui import avanzada, conflicto, estilo, tema, unidad, unidades  # noqa: E402
from historial.gui.excluir import Excluir  # noqa: E402
from historial.gui.limpiar import Limpiar  # noqa: E402
from historial.gui.otras_editar import EditarCopia  # noqa: E402
from historial.gui.panel import Panel  # noqa: E402
from historial.gui.restaurar import Restaurar  # noqa: E402
from historial.gui.versiones import Versiones  # noqa: E402


def _guardar(app, widget, nombre, destino):
    widget.show()
    app.processEvents()
    ruta = os.path.join(destino, f'gui-{nombre}.png')
    assert widget.grab().save(ruta), ruta
    assert os.path.getsize(ruta) > 2000
    widget.close()


def _pagina(app, indice):
    p = Panel()
    p.ir(indice)
    pagina = p.paginas.currentWidget()
    assert esperar(app, lambda: getattr(pagina, 'tarea', None) is None and not getattr(pagina, 'buscando', False))
    if pagina is p.otras:
        assert esperar(app, lambda: all(t.tam.text() != 'Calculando...' for t in pagina.tarjetas))
    return p


@pytest.mark.parametrize('nombre', ['dracula', 'alucard'])
def test_capturas_en_los_dos_temas(app, falso, monkeypatch, tmp_path, nombre):
    salida = os.environ.get('HISTORIAL_CAPTURAS') or str(tmp_path / 'capturas')
    os.makedirs(salida, exist_ok=True)
    monkeypatch.setattr(unidades, 'detectar', lambda *a, **k: [
        unidades.Unidad('Disco externo', '/media/usuario/Disco externo', 380 * 2**30, 465 * 2**30)])
    estilo.aplicar(app, nombre)
    try:
        falso.cfg.activo, falso.cfg.destino = True, '/media/usuario/Disco externo'
        falso.cfg.excluir = [falso.base + '/Documentos/Borradores']
        pantallas = {'panel': _pagina(app, 0), 'uso': _pagina(app, 1), 'tipos': _pagina(app, 2),
                     'otras': _pagina(app, 3), 'avanzada': avanzada.Avanzada(falso.cfg),
                     'unidad': unidad.Unidad(falso.cfg), 'excluir': Excluir(falso.cfg), 'limpiar': Limpiar(falso.cfg),
                     'editar-copia': EditarCopia(falso.otras_copias[1]),
                     'versiones': Versiones(os.path.join(falso.docs, 'informe.txt')),
                     'conflicto': conflicto.DialogoConflicto(os.path.join(falso.docs, 'informe.txt'), falso.version(2))}
        pantallas['uso-abajo'] = _pagina(app, 1)
        barra = pantallas['uso-abajo'].uso.verticalScrollBar()
        pantallas['uso-abajo'].show()
        app.processEvents()
        barra.setValue(barra.maximum())
        r = Restaurar(falso.docs)
        r.c.vista.setCurrentIndex(r.c.vista.modelo.index(0, 0))
        pantallas['restaurar'] = r
        for clave, widget in pantallas.items():
            _guardar(app, widget, f'{nombre}-{clave}', salida)
        falso.cfg.activo, falso.cfg.destino = False, ''
        _guardar(app, Panel(), f'{nombre}-panel-sin-unidad', salida)
    finally:
        estilo.aplicar(app, tema.PREDETERMINADO)
    assert len([f for f in os.listdir(salida) if f.startswith(f'gui-{nombre}-')]) >= 14
