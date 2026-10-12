"""Línea de órdenes: --ejecutar, --estado y apertura perezosa de la GUI."""
import json
import os
import subprocess
import sys
import types
from pathlib import Path

from historial import api, cli
from motor_utils import entorno, escribir  # noqa: F401

RAIZ_REPO = str(Path(__file__).resolve().parent.parent)


def test_cli_ejecutar_respeta_activo_y_copia(entorno, capsys):
    escribir(entorno.origen / 'a.txt', 'uno')
    entorno.cfg.activo = False
    api.guardar_config(entorno.cfg)
    assert cli.principal(['--ejecutar']) == 0 and capsys.readouterr().out == ''
    assert cli.principal(['--ejecutar', '--ahora']) == 0
    assert 'copiados 1' in capsys.readouterr().out


def test_cli_estado_imprime_json(entorno, capsys):
    api.guardar_config(entorno.cfg)
    assert cli.principal(['--estado']) == 0
    assert json.loads(capsys.readouterr().out)['destino_conectado'] is True


def test_cli_abre_la_gui_con_el_modo_correcto(monkeypatch):
    llamadas = []
    app = types.SimpleNamespace(main=lambda modo, ruta=None: llamadas.append((modo, ruta)))
    monkeypatch.setitem(sys.modules, 'historial.gui', types.SimpleNamespace(app=app))
    monkeypatch.setitem(sys.modules, 'historial.gui.app', app)
    for argumentos in ([], ['--restaurar'], ['--versiones', '/tmp/x']):
        assert cli.principal(argumentos) == 0
    assert llamadas == [('panel', None), ('restaurar', None), ('versiones', '/tmp/x')]


def test_ejecutar_no_carga_qt(entorno):
    api.guardar_config(entorno.cfg)
    codigo = ("import sys; from historial import cli; cli.principal(['--ejecutar']); "
              "print([m for m in sys.modules if m.startswith(('PySide6', 'PyQt6', 'historial.gui'))])")
    entorno_proc = {**os.environ, 'HOME': str(entorno.home), 'PYTHONPATH': RAIZ_REPO}
    salida = subprocess.run([sys.executable, '-c', codigo], env=entorno_proc, capture_output=True,
                            text=True, cwd=RAIZ_REPO, check=True).stdout
    assert salida.strip().endswith('[]')


def test_ejecutar_en_segundo_plano_lanza_proceso_independiente(monkeypatch):
    registro = {}
    monkeypatch.setattr(subprocess, 'Popen', lambda orden, **k: registro.update(orden=orden, **k))
    api.ejecutar_en_segundo_plano()
    assert registro['orden'][-2:] == ['--ejecutar', '--ahora'] and registro['start_new_session']
