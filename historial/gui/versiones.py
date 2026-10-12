"""Versiones anteriores: pestaña estilo Propiedades con las copias de un archivo."""
import os

from historial import api
from historial.api import Entrada

from . import acciones
from .estilo import margenes
from .formato import fecha_texto, tam_humano
from .qt import W
from .textos import t
from .widgets import botones_dialogo, etiqueta, icono

COLUMNAS = ('col_nombre', 'col_fecha', 'col_tam', 'col_ubicacion')


def _pestana(texto: str) -> W.QWidget:
    """Cabecera de la pestaña: icono de reloj y la explicación de dónde vienen las versiones."""
    reloj = W.QLabel()
    reloj.setPixmap(icono('document-open-recent', 'SP_BrowserReload').pixmap(40, 40))
    fila = W.QHBoxLayout()
    fila.addWidget(reloj)
    fila.addWidget(etiqueta(texto), 1)
    pagina = W.QWidget()
    W.QVBoxLayout(pagina).addLayout(fila)
    return pagina


class Versiones(W.QDialog):
    def __init__(self, ruta: str, cfg=None, padre=None):
        super().__init__(padre)
        self.cfg, self.ruta, self.ocupado = cfg or api.cargar_config(), ruta, False
        self.lista_versiones = api.versiones(self.cfg, ruta)
        self.setWindowTitle(t('versiones_titulo', nombre=os.path.basename(ruta)))
        self.resize(560, 520)
        self.tabla = W.QTableWidget(len(self.lista_versiones), len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels([t(c) for c in COLUMNAS])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setSelectionBehavior(W.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(W.QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.estado = etiqueta('', 'gris')
        self._llenar()
        pestana = W.QTabWidget()
        pagina = W.QWidget()
        dentro = W.QVBoxLayout(pagina)
        margenes(dentro, 14, 8)
        dentro.addWidget(_pestana(t('versiones_texto')))
        dentro.addWidget(etiqueta(t('versiones_lista')))
        dentro.addWidget(self.tabla, 1)
        dentro.addWidget(self.estado)
        dentro.addLayout(self._botones())
        pestana.addTab(pagina, t('versiones_pestana'))
        total = W.QVBoxLayout(self)
        margenes(total, 12, 10)
        total.addWidget(pestana, 1)
        total.addWidget(botones_dialogo(self, t('aceptar'), t('cancelar')))

    def _llenar(self):
        for fila, v in enumerate(self.lista_versiones):
            datos = (os.path.basename(v.ruta), fecha_texto(v.fecha), tam_humano(v.tam), t('ubicacion_hist'))
            for col, texto in enumerate(datos):
                self.tabla.setItem(fila, col, W.QTableWidgetItem(texto))
        if self.lista_versiones:
            self.tabla.selectRow(0)
        else:
            self.estado.setText(t('versiones_vacia'))

    def _botones(self) -> W.QHBoxLayout:
        self.abrir = W.QPushButton(t('abrir'))
        self.abrir.clicked.connect(self.abrir_version)
        menu = W.QMenu(self)
        menu.addAction(t('restaurar')).triggered.connect(lambda *_: self.restaurar())
        menu.addAction(t('restaurar_en')).triggered.connect(lambda *_: self.restaurar_en())
        self.boton_restaurar = W.QPushButton(t('restaurar'))
        self.boton_restaurar.setMenu(menu)
        fila = W.QHBoxLayout()
        fila.addStretch(1)
        fila.addWidget(self.abrir)
        fila.addWidget(self.boton_restaurar)
        return fila

    def seleccionada(self):
        fila = self.tabla.currentRow()
        return self.lista_versiones[fila] if 0 <= fila < len(self.lista_versiones) else None

    def abrir_version(self):
        v = self.seleccionada()
        if v:
            acciones.abrir_copia(v.archivo, os.path.basename(v.ruta))

    def restaurar(self, destino=None):
        v = self.seleccionada()
        if v and not self.ocupado:
            entrada = Entrada(os.path.basename(v.ruta), v.ruta, False, v.tam, v.fecha, v.id)
            self.estado.setText(t('restaurando'))
            acciones.restaurar_entradas(self, self.cfg, [entrada], destino, self._restaurado)

    def restaurar_en(self):
        destino = acciones.elegir_destino(self)
        if destino:
            self.restaurar(destino)

    def _restaurado(self, rutas, error):
        self.estado.setText(t('restaurar_fallo', motivo=error) if error else t('restaurado', n=len(rutas)))

    def reject(self):
        if not self.ocupado:
            super().reject()
