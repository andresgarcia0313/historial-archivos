"""Excluir carpetas (y gestionar las carpetas incluidas en la copia)."""
from historial import api

from .estilo import margenes
from .lista_rutas import ListaRutas
from .qt import W
from .textos import t
from .widgets import botones_dialogo, etiqueta


class Excluir(W.QDialog):
    def __init__(self, cfg, padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.setWindowTitle(t('excluir_titulo'))
        self.resize(640, 600)
        self.excluidas = ListaRutas(t('excluir_lista'), t('agregar'), cfg.excluir, t('excluir_vacia'), 'excluir_elegir')
        self.incluidas = ListaRutas(t('incluir_lista'), t('incluir_agregar'), cfg.carpetas)
        total = W.QVBoxLayout(self)
        margenes(total, 24, 12)
        total.addWidget(etiqueta(t('excluir_titulo'), 'titulo'))
        total.addWidget(etiqueta(t('excluir_texto')))
        total.addWidget(self.excluidas, 1)
        total.addWidget(self.incluidas, 1)
        total.addWidget(botones_dialogo(self, t('guardar'), t('cancelar')))

    def accept(self):
        self.cfg.excluir = self.excluidas.rutas()
        self.cfg.carpetas = self.incluidas.rutas()
        api.guardar_config(self.cfg)
        super().accept()
