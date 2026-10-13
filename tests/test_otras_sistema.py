"""Timeshift, Time Machine, utilidades comunes y el despachador de historial.otras."""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from historial import otras
from historial.otras import comun, timemachine, timeshift

TMUTIL = """====================================================
Name          : Disco TM
Kind          : Local
Mount Point   : /Volumes/Disco TM
ID            : ABC-123
"""


def test_timeshift_solo_lectura(tmp_path, monkeypatch):
    ruta = tmp_path / 'timeshift.json'
    ruta.write_text(json.dumps({'backup_device_uuid': 'u-1', 'schedule_daily': 'true',
                                'schedule_hourly': 'false', 'exclude': ['/root/**']}), encoding='utf-8')
    monkeypatch.setattr(timeshift, 'RUTAS', (str(ruta),))
    monkeypatch.setattr(timeshift, 'SNAPSHOTS', (str(tmp_path / 'snaps'),))
    (tmp_path / 'snaps' / '2026-10-11_10-00-01').mkdir(parents=True)
    [c] = timeshift.detectar()
    assert (c.activa, c.frecuencia, c.frecuencia_min, c.editable) == (True, 'Diaria', 1440, False)
    assert c.destino == 'UUID=u-1' and c.excluir == ['/root/**'] and 'administrador' in c.nota
    assert c.ultima == datetime(2026, 10, 11, 10, 0, 1)
    with pytest.raises(RuntimeError):
        otras.guardar(c)


def test_timeshift_ausente_o_danado(tmp_path, monkeypatch):
    (tmp_path / 'malo.json').write_text('{no', encoding='utf-8')
    monkeypatch.setattr(timeshift, 'RUTAS', (str(tmp_path / 'malo.json'), str(tmp_path / 'falta.json')))
    assert timeshift.detectar() == []


def test_time_machine(monkeypatch):
    respuestas = {'destinationinfo': TMUTIL, 'read': '1\n',
                  'latestbackup': '/Volumes/Disco TM/2026-10-12-093000.backup\n'}
    monkeypatch.setattr(timemachine.sys, 'platform', 'darwin')
    monkeypatch.setattr(timemachine, 'ejecutar', lambda orden, **_: respuestas.get(orden[1]))
    [c] = timemachine.detectar()
    assert (c.id, c.nombre, c.destino) == ('timemachine:ABC-123', 'Disco TM', '/Volumes/Disco TM')
    assert c.activa and c.frecuencia == 'Cada hora' and not c.editable
    assert c.ultima == datetime(2026, 10, 12, 9, 30)


def test_time_machine_fuera_de_macos(monkeypatch):
    monkeypatch.setattr(timemachine.sys, 'platform', 'linux')
    assert timemachine.detectar() == []


def test_texto_frecuencia():
    casos = {None: 'Manual', 15: 'Cada 15 minutos', 60: 'Cada hora', 180: 'Cada 3 horas',
             1440: 'Diaria', 2880: 'Cada 2 días', 10080: 'Semanal'}
    for minutos, texto in casos.items():
        assert comun.texto_frecuencia(minutos) == texto


def test_montajes_de_red(tmp_path, monkeypatch):
    montajes = tmp_path / 'mounts'
    montajes.write_text('srv:/x /mnt/mi\\040red fuse.sshfs rw 0 0\n/dev/sda1 /media/u ext4 rw 0 0\n',
                        encoding='utf-8')
    monkeypatch.setattr(comun, 'MONTAJES', str(montajes))
    red = comun.puntos_de_red()
    assert red == {'/mnt/mi red'}
    assert comun.es_de_red('/mnt/mi red/a', red) and not comun.es_de_red('/mnt/mi redes', red)
    assert comun.du('/mnt/mi red') is None


def test_detectar_nunca_lanza(monkeypatch):
    def roto():
        raise OSError('falla')
    monkeypatch.setattr(otras, '_modulo', lambda _: type('M', (), {'detectar': staticmethod(roto)}))
    assert otras.detectar() == []


def test_tamano_y_abrir_desconocidos():
    c = otras.CopiaDetectada('rara:1', 'Rara', 'x', False, '/', 'Manual', None)
    assert otras.tamano(c) is None and otras.abrir_herramienta(c) is False
