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
