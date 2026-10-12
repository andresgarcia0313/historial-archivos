"""El registro de eventos anota cada copia y no crece sin límite."""
from historial import cli, registro


def test_ejecutar_anota_en_el_registro(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'datos'))
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'conf'))
    monkeypatch.setenv('HISTORIAL_SIN_PROGRAMAR', '1')
    docs = tmp_path / 'Documentos'
    docs.mkdir()
    (docs / 'informe.docx').write_bytes(b'v1')
    (tmp_path / 'usb').mkdir()
    cfg = cli.api.Config(activo=True, destino=str(tmp_path / 'usb'), carpetas=[str(docs)])
    cli.api.guardar_config(cfg)
    monkeypatch.setattr(cli.prioridad, 'bajar', lambda: None)
    assert cli.principal(['--ejecutar']) == 0
    texto = open(registro.ruta(), encoding='utf-8').read()
    assert 'INFORMACIÓN' in texto and 'copiados 1' in texto


def test_registro_se_recorta(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path))
    monkeypatch.setattr(registro, 'MAX_BYTES', 1000)
    for i in range(200):
        registro.anotar('INFORMACIÓN', f'linea {i}')
    import os
    assert os.path.getsize(registro.ruta()) < 1200
    assert 'linea 199' in open(registro.ruta(), encoding='utf-8').read()
