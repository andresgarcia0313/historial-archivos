"""Seleccionar unidad: unidades detectadas más "Agregar ubicación de red"."""
import os

from historial import api

from . import unidades
from .estilo import margenes
from .formato import tam_humano
from .qt import Qt, W
from .textos import t
from .widgets import botones_dialogo, etiqueta


class Unidad(W.QDialog):
    def __init__(self, cfg, padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.setWindowTitle(t('unidad_titulo'))
        self.resize(620, 420)
        self.lista = W.QListWidget()
        self.vacia = etiqueta(t('unidad_ninguna'), 'gris')
        red = W.QPushButton(t('unidad_red'))
        red.clicked.connect(self.agregar_red)
        total = W.QVBoxLayout(self)
        margenes(total, 24, 14)
        total.addWidget(etiqueta(t('unidad_titulo'), 'titulo'))
        total.addWidget(etiqueta(t('unidad_texto')))
        total.addWidget(self.lista, 1)
        total.addWidget(self.vacia)
        total.addWidget(red)
        total.addWidget(botones_dialogo(self, t('aceptar'), t('cancelar')))
        for u in unidades.detectar():
            self._poner(u.nombre, u.ruta, u.libre, u.total)
        if cfg.destino and not self.lista.findItems(cfg.destino, Qt.MatchFlag.MatchContains):
            self._poner(os.path.basename(cfg.destino) or cfg.destino, cfg.destino)
        self._elegir_actual()

    def _poner(self, nombre, ruta, libre=None, total=None):
        texto = ruta if libre is None else t('unidad_item', nombre=nombre, ruta=ruta,
                                             libre=tam_humano(libre), total=tam_humano(total))
        item = W.QListWidgetItem(texto)
        item.setData(Qt.ItemDataRole.UserRole, ruta)
        self.lista.addItem(item)
        self.vacia.setVisible(False)
        return item

    def _elegir_actual(self):
        for i in range(self.lista.count()):
            if self.lista.item(i).data(Qt.ItemDataRole.UserRole) == self.cfg.destino:
                self.lista.setCurrentRow(i)

    def agregar_red(self):
        ruta = W.QFileDialog.getExistingDirectory(self, t('unidad_elegir_red'), '/')
        if ruta:
            self.lista.setCurrentItem(self._poner(os.path.basename(ruta) or ruta, ruta))

    def seleccion(self) -> str:
        item = self.lista.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else ''

    def accept(self):
        if self.seleccion():
            self.cfg.destino = self.seleccion()
            api.guardar_config(self.cfg)
        super().accept()
