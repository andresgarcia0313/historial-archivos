"""uso() solo lee el catálogo: menos de 1 s con 50 mil versiones sintéticas."""
import time

from historial import api, catalogo
from motor_utils import entorno  # noqa: F401

EXTS = ('docx', 'jpg', 'py', 'mp4', 'zip', 'xlsx', 'bin')


def test_uso_con_50_mil_versiones_en_menos_de_un_segundo(entorno):
    cat = catalogo.abrir(entorno.cfg)
    filas = []
    for i in range(50_000):
        ruta = f'{entorno.origen}/c{i % 300}/archivo{i % 12_000}.{EXTS[i % 7]}'
        filas.append((ruta, f'2025_{1 + i % 12:02d}_01 10_00_00 UTC', i % 5000, i, f'x/{i}', 1))
    cat.db.executemany('INSERT INTO versiones(ruta, sello, tam, mtime_ns, archivo, desde) '
                       'VALUES(?,?,?,?,?,?)', filas)
    cat.db.commit()
    cat.db.close()
    duraciones = []
    for _ in range(3):                         # el mejor de 3: descarta el ruido de un equipo cargado
        inicio = time.perf_counter()
        uso = api.uso(entorno.cfg)
        duraciones.append(time.perf_counter() - inicio)
    duracion = min(duraciones)
    print(f'uso() con 50 mil versiones: {duracion:.3f} s')
    assert uso.versiones == 50_000 and uso.archivos > 10_000
    assert len(uso.por_mes) == 12 and len(uso.mas_grandes) == 20 and len(uso.mas_versionados) == 20
    assert sum(g.versiones for g in uso.por_categoria) == 50_000
    assert duracion < 1.0, f'uso() tardó {duracion:.2f} s'
