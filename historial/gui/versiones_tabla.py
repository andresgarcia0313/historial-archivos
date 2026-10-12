"""Piezas de Versiones anteriores: cabecera de la pestaña y tabla de versiones."""
import os

from .formato import fecha_texto
from .qt import W
from .textos import t
from .widgets import etiqueta, icono

COLUMNAS = ('col_nombre', 'col_fecha', 'col_ubicacion')


def cabecera_pestana(texto: str) -> W.QWidget:
    """Icono de reloj y la explicación de dónde vienen las versiones."""
    reloj = W.QLabel()
    reloj.setPixmap(icono('document-open-recent', 'SP_BrowserReload').pixmap(40, 40))
    fila = W.QHBoxLayout()
    fila.addWidget(reloj)
    fila.addWidget(etiqueta(texto), 1)
    pagina = W.QWidget()
    W.QVBoxLayout(pagina).addLayout(fila)
    return pagina


def crear_tabla(versiones) -> W.QTableWidget:
    """Tabla de solo lectura (Nombre, Fecha de modificación, Ubicación) con la primera fila seleccionada."""
    tabla = W.QTableWidget(len(versiones), len(COLUMNAS))
    tabla.setHorizontalHeaderLabels([t(c) for c in COLUMNAS])
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setStretchLastSection(True)
    tabla.setSelectionBehavior(W.QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(W.QAbstractItemView.SelectionMode.SingleSelection)
    tabla.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
    for fila, v in enumerate(versiones):
        for col, texto in enumerate((os.path.basename(v.ruta), fecha_texto(v.fecha), t('ubicacion_hist'))):
            tabla.setItem(fila, col, W.QTableWidgetItem(texto))
    tabla.resizeColumnsToContents()
    if versiones:
        tabla.selectRow(0)
    return tabla
