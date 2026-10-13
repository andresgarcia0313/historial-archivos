"""Pestañas "Los más grandes" y "Los más versionados" con nombre, ubicación, tamaño total y versiones."""
import os

from .formato import tam_humano
from .qt import Qt, W
from .textos import t

COLUMNAS = ('col_nombre', 'col_ubicacion', 'col_tam', 'col_versiones')


def _tabla() -> W.QTableWidget:
    tabla = W.QTableWidget(0, len(COLUMNAS))
    tabla.setHorizontalHeaderLabels([t(c) for c in COLUMNAS])
    tabla.verticalHeader().setVisible(False)
    tabla.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
    tabla.setSelectionBehavior(W.QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setShowGrid(False)
    tabla.setAlternatingRowColors(True)
    tabla.setMinimumHeight(220)
    cabecera = tabla.horizontalHeader()
    cabecera.setSectionResizeMode(1, W.QHeaderView.ResizeMode.Stretch)
    for col in (0, 2, 3):
        cabecera.setSectionResizeMode(col, W.QHeaderView.ResizeMode.ResizeToContents)
    return tabla


def _celda(texto: str, derecha: bool = False, ayuda: str = '') -> W.QTableWidgetItem:
    item = W.QTableWidgetItem(texto)
    if derecha:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    item.setToolTip(ayuda or texto)
    return item


class Tablas(W.QTabWidget):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.grandes, self.versionados = _tabla(), _tabla()
        self.addTab(self.grandes, t('tab_grandes'))
        self.addTab(self.versionados, t('tab_versionados'))

    def poner(self, grandes, versionados) -> None:
        for tabla, filas in ((self.grandes, grandes), (self.versionados, versionados)):
            tabla.setRowCount(len(filas))
            for i, (ruta, total, versiones) in enumerate(filas):
                tabla.setItem(i, 0, _celda(os.path.basename(ruta), ayuda=ruta))
                tabla.setItem(i, 1, _celda(os.path.dirname(ruta)))
                tabla.setItem(i, 2, _celda(tam_humano(total), True))
                tabla.setItem(i, 3, _celda(str(versiones), True))
