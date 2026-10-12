"""Motor falso de historial.api para las pruebas de la GUI: 3 copias, dos carpetas protegidas, llamadas anotadas."""
import os
from datetime import datetime

import pytest

from historial import api


class Falso:
    """Motor de mentira con 3 copias y dos carpetas protegidas; guarda las llamadas."""

    def __init__(self, base):
        self.base = str(base)
        self.docs, self.imgs = os.path.join(self.base, 'Documentos'), os.path.join(self.base, 'Imagenes')
        os.makedirs(self.docs)
        os.makedirs(self.imgs)
        self.cfg = api.Config(activo=False, destino='', carpetas=[self.docs, self.imgs])
        self.guardados, self.llamadas, self.restauradas, self.respuestas = [], [], [], []
        self.sondeos = 0
        self.puntos_pedidos = []
        self.conflictos = False                 # True: restaurar() consulta `decidir` por cada archivo
        self.fechas = [datetime(2026, 10, d, 9, 30) for d in (10, 11, 12)]
        self.copias = {}
        for n in (1, 2, 3):
            archivo = os.path.join(self.base, f'copia{n}.txt')
            with open(archivo, 'w') as f:
                f.write(f'contenido version {n}')
            self.copias[n] = archivo

    def version(self, n):
        return api.Version(n, os.path.join(self.docs, 'informe.txt'), self.fechas[n - 1], 100 * n, self.copias[n])

    def puntos(self, cfg):
        return [api.Punto(i + 1, f) for i, f in enumerate(self.fechas)]

    def listar(self, cfg, punto_id, carpeta):
        if carpeta == '':
            return [api.Entrada('Documentos', self.docs, True), api.Entrada('Imagenes', self.imgs, True)]
        if carpeta != self.docs:
            return []
        entradas = [api.Entrada('informe.txt', os.path.join(self.docs, 'informe.txt'), False, 100, None, punto_id)]
        if punto_id >= 2:
            entradas.append(api.Entrada('notas.md', os.path.join(self.docs, 'notas.md'), False, 50, None, punto_id))
        if punto_id >= 3:
            entradas.append(api.Entrada('foto.png', os.path.join(self.docs, 'foto.png'), False, 900, None, punto_id))
        return entradas

    def estado(self, cfg):
        en_curso = self.sondeos > 0
        self.sondeos = max(0, self.sondeos - 1)
        return api.Estado(cfg.activo, bool(cfg.destino), self.fechas[-1], 3 * 2**30, 400 * 2**30, 465 * 2**30,
                          en_curso=en_curso)

    def restaurar(self, cfg, entradas, destino_dir=None, conflicto='preguntar', decidir=None, punto_id=None):
        self.restauradas.append((list(entradas), destino_dir, conflicto))
        self.puntos_pedidos.append(punto_id)
        for e in entradas:
            if self.conflictos and decidir:
                self.respuestas.append(decidir(e.ruta, self.version(1)))
        return [e.ruta for e in entradas]

    def parchear(self, mp):
        mp.setattr(api, 'cargar_config', lambda: self.cfg)
        mp.setattr(api, 'guardar_config', lambda cfg: self.guardados.append((cfg.activo, cfg.destino)))
        mp.setattr(api, 'estado', self.estado)
        mp.setattr(api, 'puntos', self.puntos)
        mp.setattr(api, 'listar', self.listar)
        mp.setattr(api, 'versiones', lambda cfg, ruta: [self.version(n) for n in (3, 2, 1)])
        mp.setattr(api, 'restaurar', self.restaurar)
        mp.setattr(api, 'limpiar', lambda cfg, dias: self.llamadas.append(('limpiar', dias)) or 2048)
        mp.setattr(api, 'ejecutar_en_segundo_plano', lambda: self._lanzar())

    def _lanzar(self):
        self.llamadas.append(('ejecutar',))
        self.sondeos = 3


@pytest.fixture
def falso(tmp_path, monkeypatch):
    motor = Falso(tmp_path)
    motor.parchear(monkeypatch)
    return motor
