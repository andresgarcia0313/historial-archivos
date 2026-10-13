"""Déjà Dup: gsettings simulado en memoria."""
from __future__ import annotations

from datetime import datetime

import pytest

from historial import otras
from historial.otras import dejadup


@pytest.fixture
def gsettings(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    monkeypatch.setenv('HOME', str(home))
    valores = {
        ('org.gnome.DejaDup', 'periodic'): 'true',
        ('org.gnome.DejaDup', 'periodic-period'): '7',
        ('org.gnome.DejaDup', 'include-list'): "['$HOME', '/datos']",
        ('org.gnome.DejaDup', 'exclude-list'): "['$HOME/.cache', '$TRASH']",
        ('org.gnome.DejaDup', 'backend'): "'local'",
        ('org.gnome.DejaDup', 'last-backup'): "'2026-10-12T15:30:00Z'",
        ('org.gnome.DejaDup.Local', 'folder'): "'$HOME/copias'",
    }

    def falso(orden, **_):
        if orden[:2] == ['gsettings', 'get']:
            return valores.get((orden[2], orden[3]))
        if orden[:2] == ['gsettings', 'set']:
            valores[(orden[2], orden[3])] = orden[4]
            return ''
        return 'volcado\n'
    monkeypatch.setattr(dejadup, 'ejecutar', falso)
    monkeypatch.setattr(dejadup.shutil, 'which', lambda _: '/usr/bin/deja-dup')
    return valores, home


def test_detecta_la_configuracion(gsettings):
    _, home = gsettings
    [c] = dejadup.detectar()
    assert c.id == 'dejadup:principal' and c.activa and c.editable
    assert (c.frecuencia, c.frecuencia_min) == ('Semanal', 10080)
    assert c.carpetas == [str(home), '/datos'] and c.excluir == [f'{home}/.cache', '$TRASH']
    assert c.destino == f'{home}/copias'
    assert isinstance(c.ultima, datetime)


def test_guardar_escribe_y_respalda(gsettings):
    valores, home = gsettings
    [c] = dejadup.detectar()
    c.activa, c.frecuencia_min, c.carpetas, c.excluir = False, 1440, [f'{home}/Fotos'], []
    otras.guardar(c)
    assert valores[('org.gnome.DejaDup', 'periodic')] == 'false'
    assert valores[('org.gnome.DejaDup', 'periodic-period')] == '1'
    assert valores[('org.gnome.DejaDup', 'include-list')] == "['$HOME/Fotos']"
    assert valores[('org.gnome.DejaDup', 'exclude-list')] == '@as []'
    assert len(list((home / '.config' / 'historial-archivos').glob('dejadup.gsettings.bak-*'))) == 1


def test_sin_esquema_no_detecta_nada(monkeypatch):
    monkeypatch.setattr(dejadup, 'ejecutar', lambda *a, **k: None)
    assert dejadup.detectar() == []


def test_gsettings_rechaza_un_cambio(gsettings, monkeypatch):
    [c] = dejadup.detectar()
    monkeypatch.setattr(dejadup, 'ejecutar', lambda orden, **_: None if orden[1] == 'set' else '')
    with pytest.raises(RuntimeError):
        dejadup.guardar(c)
