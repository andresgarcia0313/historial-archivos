"""Falsos de la v1.1 para la GUI: uso del espacio (historial.api) y otras copias (historial.otras)."""
import os
from datetime import datetime

from historial import api, otras
from historial.contrato_uso import CATEGORIAS, Grupo, Uso
from historial.otras import CopiaDetectada

G = 2**30


def uso_falso(docs, imgs) -> Uso:
    categorias = [Grupo('imagenes', 41 * G, 5210, 6900), Grupo('videos', 23 * G, 88, 120),
                  Grupo('documentos', 6 * G, 3100, 9800), Grupo('hojas', int(1.5 * G), 410, 2900),
                  Grupo('codigo', int(0.4 * G), 9000, 15000), Grupo('otros', int(0.2 * G), 700, 800)]
    meses = [Grupo(f'2026-{m:02d}', (m * 7 % 11 + 2) * G, 0, 0) for m in range(1, 11)]
    grandes = [(os.path.join(imgs, f'video-familia-{i}.mp4'), (9 - i) * G, 2) for i in range(6)]
    versionados = [(os.path.join(docs, f'presupuesto-{i}.xlsx'), 80 * 2**20, 140 - 9 * i) for i in range(6)]
    return Uso(bytes_copias=int(72.1 * G), bytes_actual=int(48.7 * G), archivos=18508, versiones=35520,
               libre=380 * G, total=465 * G, primera=datetime(2026, 1, 4, 10, 0), ultima=datetime(2026, 10, 12, 9, 30),
               por_categoria=categorias, por_carpeta=[Grupo(imgs, 64 * G, 5300, 7020), Grupo(docs, 8 * G, 13208, 28500)],
               por_mes=meses, mas_grandes=grandes, mas_versionados=versionados)


def copias_falsas() -> list:
    return [CopiaDetectada('backintime:1', 'Back In Time', 'Principal', False, '/media/usuario/Respaldo',
                           'Manual', None, ['/home/usuario'], ['.cache'], None, True, ''),
            CopiaDetectada('backintime:2', 'Back In Time', 'Servidor', True, 'usuario@servidor:/copias',
                           'Diaria', 1440, ['/home/usuario/Documentos', '/home/usuario/Proyectos'], [],
                           datetime(2026, 10, 12, 3, 0), True, ''),
            CopiaDetectada('timeshift', 'Timeshift', 'Sistema', True, '/dev/sdb1', 'Diaria', 1440, ['/'], [],
                           datetime(2026, 10, 11, 23, 0), False, 'necesita permisos de administrador')]


def _categoria(nombre: str) -> str:
    ext = nombre.rsplit('.', 1)[-1].lower() if '.' in nombre else ''
    return next((c for c, exts in CATEGORIAS.items() if ext in exts), 'otros')


def parchear_v11(motor, mp) -> None:
    motor.uso = uso_falso(motor.docs, motor.imgs)
    motor.otras_copias, motor.medidas = copias_falsas(), {'backintime:2': 12 * G, 'backintime:1': None}
    motor.guardadas, motor.abiertas, motor.limpiezas = [], [], []
    mp.setattr(api, 'uso', lambda cfg: motor.uso, raising=False)
    mp.setattr(api, 'categoria_de', _categoria, raising=False)
    mp.setattr(api, 'limpiar_filtrado', lambda cfg, **k: motor.limpiezas.append(k) or 3 * G, raising=False)
    mp.setattr(otras, 'detectar', lambda: list(motor.otras_copias))
    mp.setattr(otras, 'tamano', lambda c: motor.medidas.get(c.id, 5 * G))
    mp.setattr(otras, 'guardar', lambda c: motor.guardadas.append(c))
    mp.setattr(otras, 'abrir_herramienta', lambda c: motor.abiertas.append(c.id) or c.herramienta != 'Timeshift')
