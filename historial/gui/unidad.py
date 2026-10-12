"""Seleccionar unidad: unidades detectadas más "Agregar ubicación de red"."""
import os

from historial import api

from . import unidades
from .estilo import margenes
from .formato import tam_humano
from .qt import Qt, W
from .textos import t
from .widgets import botones_dialogo, enlace, etiqueta


class Unidad(W.QDialog):
    def __init__(self, cfg, padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.setWindowTitle(t('unidad_titulo'))
        self.resize(640, 460)
        self.lista = W.QTreeWidget()
        self.lista.setRootIsDecorated(False)
        self.lista.setHeaderLabels([t('col_unidades'), t('col_libre'), t('col_total')])
        self.lista.header().setStretchLastSection(False)
        self.lista.header().setSectionResizeMode(0, W.QHeaderView.ResizeMode.Stretch)
        self.vacia = etiqueta(t('unidad_ninguna'), 'gris')
        total = W.QVBoxLayout(self)
        margenes(total, 24, 12)
        total.addWidget(etiqueta(t('unidad_titulo'), 'titulo'))
        total.addWidget(etiqueta(t('unidad_texto')))
        total.addWidget(self.lista, 1)
        total.addWidget(self.vacia)
        total.addWidget(enlace(t('unidad_red'), self.agregar_red), 0, Qt.AlignmentFlag.AlignRight)
        total.addWidget(botones_dialogo(self, t('aceptar'), t('cancelar')))
        for u in unidades.detectar():
            self._poner(u.nombre, u.ruta, u.libre, u.total)
        if cfg.destino and not self._buscar(cfg.destino):
            self._poner(os.path.basename(cfg.destino) or cfg.destino, cfg.destino)
        self.lista.setCurrentItem(self._buscar(cfg.destino))

    def _poner(self, nombre, ruta, libre=None, total=None):
        datos = [f'{nombre} ({ruta})' if libre is not None else ruta]
        datos += ['', ''] if libre is None else [tam_humano(libre), tam_humano(total)]
        item = W.QTreeWidgetItem(datos)
        item.setData(0, Qt.ItemDataRole.UserRole, ruta)
        self.lista.addTopLevelItem(item)
        self.vacia.setVisible(False)
        return item

    def _buscar(self, ruta):
        for i in range(self.lista.topLevelItemCount()):
            if self.lista.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole) == ruta:
                return self.lista.topLevelItem(i)
        return None

    def agregar_red(self):
        ruta = W.QFileDialog.getExistingDirectory(self, t('unidad_elegir_red'), '/')
        if ruta:
            self.lista.setCurrentItem(self._buscar(ruta) or self._poner(os.path.basename(ruta) or ruta, ruta))

    def seleccion(self) -> str:
        item = self.lista.currentItem()
        return item.data(0, Qt.ItemDataRole.UserRole) if item else ''

    def accept(self):
        if self.seleccion():
            self.cfg.destino = self.seleccion()
            api.guardar_config(self.cfg)
        super().accept()
