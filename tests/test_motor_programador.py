"""Configuración, unidades programadas (systemd y launchd) y CLI."""
import json
import os
import subprocess
import sys
import types
from pathlib import Path

from historial import api, cli, programador
from motor_utils import entorno, escribir  # noqa: F401

RAIZ_REPO = str(Path(__file__).resolve().parent.parent)


def test_config_ida_y_vuelta_y_tolerancia(entorno):
    assert api.cargar_config() == api.Config()
    entorno.cfg.frecuencia_min = 30
    api.guardar_config(entorno.cfg)
    assert api.cargar_config() == entorno.cfg
    ruta = entorno.home / '.config/historial-archivos/config.json'
    datos = json.loads(ruta.read_text())
    ruta.write_text(json.dumps({**datos, 'campo_futuro': 1}))
    assert api.cargar_config() == entorno.cfg
    ruta.write_text('{roto')
    assert api.cargar_config() == api.Config()


def test_unidades_systemd_al_guardar_y_al_desactivar(entorno, monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError('no debe llamar a systemctl con HISTORIAL_SIN_PROGRAMAR=1')

    monkeypatch.setattr(subprocess, 'run', prohibido)
    entorno.cfg.frecuencia_min = 30
    api.guardar_config(entorno.cfg)
    unidades = entorno.home / '.config/systemd/user'
    servicio = (unidades / 'historial-archivos.service').read_text()
    temporizador = (unidades / 'historial-archivos.timer').read_text()
    for linea in ('Type=oneshot', 'Nice=19', 'IOSchedulingClass=idle', 'CPUWeight=20', 'IOWeight=20',
                  'MemoryMax=512M', '--ejecutar'):
        assert linea in servicio
    for linea in ('OnBootSec=5min', 'OnUnitActiveSec=30min', 'Persistent=true'):
        assert linea in temporizador
    entorno.cfg.activo = False
    api.guardar_config(entorno.cfg)
    assert not list(unidades.glob('historial-archivos.*'))


def test_systemd_llama_a_systemctl_en_orden(entorno, monkeypatch):
    monkeypatch.delenv('HISTORIAL_SIN_PROGRAMAR')
    llamadas = []
    monkeypatch.setattr(subprocess, 'run', lambda orden, **k: llamadas.append(list(orden)))
    programador.aplicar(entorno.cfg)
    assert llamadas == [['systemctl', '--user', 'daemon-reload'],
                        ['systemctl', '--user', 'enable', '--now', 'historial-archivos.timer']]
    llamadas.clear()
    entorno.cfg.activo = False
    programador.aplicar(entorno.cfg)
    assert llamadas[0] == ['systemctl', '--user', 'disable', '--now', 'historial-archivos.timer']


def test_launchagent_de_macos(entorno, monkeypatch):
    import plistlib
    monkeypatch.setattr(sys, 'platform', 'darwin')
    entorno.cfg.frecuencia_min = 15
    programador.aplicar(entorno.cfg)
    plist = entorno.home / 'Library/LaunchAgents/io.github.andresgarcia0313.historial-archivos.plist'
    datos = plistlib.loads(plist.read_bytes())
    assert datos['StartInterval'] == 900 and datos['RunAtLoad'] and datos['Nice'] == 19
    assert datos['LowPriorityIO'] and datos['ProcessType'] == 'Background'
    assert datos['ProgramArguments'][-1] == '--ejecutar'
    llamadas = []
    monkeypatch.delenv('HISTORIAL_SIN_PROGRAMAR')
    monkeypatch.setattr(subprocess, 'run', lambda orden, **k: llamadas.append(list(orden)))
    programador.aplicar(entorno.cfg)
    assert [c[1] for c in llamadas] == ['bootout', 'bootstrap']
    assert llamadas[1][2] == f'gui/{os.getuid()}'


def test_comando_a_programar(monkeypatch):
    monkeypatch.setattr(programador.shutil, 'which', lambda nombre: '/usr/bin/historial-archivos')
    assert programador.comando() == ['/usr/bin/historial-archivos', '--ejecutar']
    monkeypatch.setattr(programador.shutil, 'which', lambda nombre: None)
    assert programador.comando() == [sys.executable, '-m', 'historial', '--ejecutar']
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    assert programador.comando() == [sys.executable, '--ejecutar']


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
    salida = subprocess.run([sys.executable, '-I', '-c', codigo], env=entorno_proc, capture_output=True,
                            text=True, cwd=RAIZ_REPO, check=True).stdout
    assert salida.strip().endswith('[]')


def test_ejecutar_en_segundo_plano_lanza_proceso_independiente(monkeypatch):
    registro = {}
    monkeypatch.setattr(subprocess, 'Popen', lambda orden, **k: registro.update(orden=orden, **k))
    api.ejecutar_en_segundo_plano()
    assert registro['orden'][-2:] == ['--ejecutar', '--ahora'] and registro['start_new_session']
