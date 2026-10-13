"""Back In Time: lectura de perfiles de ejemplo y guardado simulado (sin tocar la config real)."""
from __future__ import annotations

import json
import os
from datetime import datetime

import pytest

from historial import otras
from historial.otras import backintime, backintime_guardar

CONFIG = """config.version=6
profiles=1:2
profile1.name=Local
profile1.schedule.mode=10
profile1.snapshots.mode=local
profile1.snapshots.path={destino}
profile1.snapshots.path.host=equipo
profile1.snapshots.path.user=ana
profile1.snapshots.path.profile=1
profile1.snapshots.include.size=1
profile1.snapshots.include.1.type=0
profile1.snapshots.include.1.value=/home/ana/Documentos
profile1.snapshots.exclude.size=2
profile1.snapshots.exclude.1.value=*.tmp
profile1.snapshots.exclude.2.value=.cache
profile2.schedule.mode=25
profile2.schedule.repeatedly.period=2
profile2.schedule.repeatedly.unit=20
profile2.snapshots.mode=ssh
profile2.snapshots.ssh.host=servidor
profile2.snapshots.ssh.user=ana
profile2.snapshots.ssh.path=/copias
"""


@pytest.fixture
def bit(tmp_path, monkeypatch):
    home, destino = tmp_path / 'home', tmp_path / 'unidad'
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'datos'))
    ruta = home / '.config' / 'backintime' / 'config'
    ruta.parent.mkdir(parents=True)
    ruta.write_text(CONFIG.format(destino=destino), encoding='utf-8')
    perfil = destino / 'backintime' / 'equipo' / 'ana' / '1'
    perfil.mkdir(parents=True)
    os.symlink('20261012-180003-953', perfil / 'last_snapshot')
    registro = tmp_path / 'datos' / 'backintime' / 'takesnapshot_2.log'
    registro.parent.mkdir(parents=True)
    registro.write_text('fin', encoding='utf-8')
    monkeypatch.setattr(backintime, 'API', str(tmp_path))
    monkeypatch.setattr(backintime_guardar, 'API', str(tmp_path))
    return ruta


def test_lee_perfiles_local_y_ssh(bit):
    local, remoto = backintime.detectar()
    assert (local.id, local.nombre, local.activa, local.frecuencia_min) == ('backintime:1', 'Local', True, 60)
    assert local.frecuencia == 'Cada hora' and local.ultima == datetime(2026, 10, 12, 18, 0, 3)
    assert local.carpetas == ['/home/ana/Documentos'] and local.excluir == ['*.tmp', '.cache']
    assert local.editable and local.nota == ''
    assert remoto.destino == 'ana@servidor:/copias' and remoto.frecuencia == 'Cada 2 días'
    assert remoto.nombre == 'Perfil 2' and remoto.ultima is not None
    assert backintime.tamano(remoto) is None


def test_modo_para_cada_frecuencia(bit):
    c = backintime.detectar()[0]
    casos = {60: (10, 1, 20), 1440: (20, 1, 20), 180: (25, 3, 10), 4320: (25, 3, 20), 30: (7, 1, 20)}
    for minutos, esperado in casos.items():
        c.frecuencia_min = minutos
        assert backintime_guardar.modo(c, 0) == esperado
    c.activa = False
    assert backintime_guardar.modo(c, 10)[0] == 0


def test_guardar_respalda_y_llama_a_la_api(bit, monkeypatch):
    llamadas = []

    def falso(orden, **_):
        llamadas.append(orden)
        return type('R', (), {'returncode': 0, 'stderr': ''})()
    monkeypatch.setattr(backintime_guardar.subprocess, 'run', falso)
    c = backintime.detectar()[0]
    c.frecuencia_min, c.carpetas, c.excluir = 1440, ['/home/ana/Fotos'], ['*.iso']
    otras.guardar(c)
    orden = llamadas[0]
    assert orden[:3] == ['/usr/bin/python3', '-I', '-c'] and 'setup_automation' in orden[3]
    carga = json.loads(orden[4])
    assert carga['perfil'] == '1' and carga['modo'] == 20 and carga['automatizar'] is True
    assert carga['incluir'] == [['/home/ana/Fotos', 0]] and carga['excluir'] == ['*.iso']
    assert len(list(bit.parent.glob('config.bak-*'))) == 1


def test_guardar_informa_el_fallo(bit, monkeypatch):
    monkeypatch.setattr(backintime_guardar.subprocess, 'run',
                        lambda *a, **k: type('R', (), {'returncode': 1, 'stderr': 'sin dbus'})())
    with pytest.raises(RuntimeError, match='sin dbus'):
        otras.guardar(backintime.detectar()[0])
