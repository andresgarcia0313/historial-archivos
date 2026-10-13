"""Copias de esta app: la configurada y las carpetas HistorialArchivos de unidades conectadas."""
from __future__ import annotations

import json
import socket

import pytest

from historial import otras
from historial.otras import comun, propias


@pytest.fixture
def unidades(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('USER', 'ana')
    monkeypatch.setenv('LOGNAME', 'ana')
    monkeypatch.setenv('HISTORIAL_SIN_PROGRAMAR', '1')
    monkeypatch.setattr(socket, 'gethostname', lambda: 'portatil')
    media, mnt = tmp_path / 'media', tmp_path / 'mnt'
    for ruta in (media / 'ana' / 'USB' / 'HistorialArchivos' / 'ana' / 'portatil',
                 media / 'ana' / 'USB' / 'HistorialArchivos' / 'luis' / 'oficina',
                 mnt / 'red' / 'HistorialArchivos' / 'ana' / 'servidor'):
        ruta.mkdir(parents=True)
    montajes = tmp_path / 'mounts'
    montajes.write_text(f'srv:/ {mnt / "red"} fuse.sshfs rw 0 0\n', encoding='utf-8')
    monkeypatch.setattr(comun, 'MONTAJES', str(montajes))
    monkeypatch.setattr(propias, 'BASES', (str(media), str(mnt)))
    return home, media / 'ana' / 'USB'


def _config(home, destino, **extra):
    carpeta = home / '.config' / 'historial-archivos'
    carpeta.mkdir(parents=True, exist_ok=True)
    datos = {'activo': True, 'destino': str(destino), 'carpetas': ['/home/ana/Documentos'], **extra}
    (carpeta / 'config.json').write_text(json.dumps(datos), encoding='utf-8')


def test_encuentra_carpetas_y_omite_montajes_de_red(unidades):
    _, usb = unidades
    copias = {c.nombre: c for c in propias.detectar()}
    assert set(copias) == {'portatil (ana)', 'oficina (luis)'}
    mia = copias['portatil (ana)']
    assert mia.destino == str(usb) and not mia.editable and 'reutilizarla' in mia.nota
    assert copias['oficina (luis)'].nota == 'copia de otro equipo'


def test_la_propia_no_se_repite_como_encontrada(unidades):
    home, usb = unidades
    _config(home, usb, frecuencia_min=180)
    copias = propias.detectar()
    assert [c.id for c in copias][0] == propias.PROPIA
    assert [c.nombre for c in copias] == ['Esta aplicación', 'oficina (luis)']
    assert copias[0].frecuencia == 'Cada 3 horas' and copias[0].editable and copias[0].nota == ''


def test_guardar_la_propia(unidades):
    home, usb = unidades
    _config(home, usb)
    c = propias.propia()[0]
    c.activa, c.frecuencia_min, c.excluir = False, 1440, ['/home/ana/Documentos/tmp']
    otras.guardar(c)
    datos = json.loads((home / '.config' / 'historial-archivos' / 'config.json').read_text('utf-8'))
    assert (datos['activo'], datos['frecuencia_min'], datos['excluir']) == (False, 1440, c.excluir)


def test_tamano_de_una_encontrada(unidades):
    _, usb = unidades
    archivo = usb / 'HistorialArchivos' / 'luis' / 'oficina' / 'a.bin'
    archivo.write_bytes(b'x' * 50_000)
    [c] = [c for c in propias.detectar() if c.nombre == 'oficina (luis)']
    assert otras.tamano(c) >= 50_000


def test_las_encontradas_no_son_editables(unidades):
    [c] = [c for c in propias.detectar() if c.nombre == 'oficina (luis)']
    with pytest.raises(RuntimeError):
        otras.guardar(c)
