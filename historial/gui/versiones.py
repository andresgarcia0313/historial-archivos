"""Versiones anteriores: pestaña estilo Propiedades con las copias de un archivo."""
import os

from historial import api
from historial.api import Entrada

from . import acciones
from .estilo import margenes
from .qt import W
from .textos import t
from .versiones_tabla import cabecera_pestana, crear_tabla
from .widgets import botones_dialogo, etiqueta


class Versiones(W.QDialog):
    def __init__(self, ruta: str, cfg=None, padre=None):
        super().__init__(padre)
        self.cfg, self.ruta, self.ocupado = cfg or api.cargar_config(), ruta, False
        self.lista_versiones = api.versiones(self.cfg, ruta)
        self.setWindowTitle(t('versiones_titulo', nombre=os.path.basename(ruta)))
        self.resize(560, 520)
        self.tabla = crear_tabla(self.lista_versiones)
        self.estado = etiqueta('' if self.lista_versiones else t('versiones_vacia'), 'gris')
        pagina = W.QWidget()
        dentro = W.QVBoxLayout(pagina)
        margenes(dentro, 14, 8)
        dentro.addWidget(cabecera_pestana(t('versiones_texto')))
        dentro.addWidget(etiqueta(t('versiones_lista')))
        dentro.addWidget(self.tabla, 1)
        dentro.addWidget(self.estado)
        dentro.addLayout(self._botones())
        pestana = W.QTabWidget()
        pestana.addTab(pagina, t('versiones_pestana'))
        total = W.QVBoxLayout(self)
        margenes(total, 12, 10)
        total.addWidget(pestana, 1)
        total.addWidget(botones_dialogo(self, t('aceptar'), t('cancelar')))

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
