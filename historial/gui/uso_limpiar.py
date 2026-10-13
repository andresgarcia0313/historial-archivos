"""Limpiar por tipo o carpeta: borra versiones filtradas en segundo plano, con confirmación porque no se deshace."""
import os

from historial import api

from . import categorias
from .formato import tam_humano
from .limpiar import OPCIONES
from .opciones import texto_limpiar
from .qt import Signal, W
from .textos import t
from .trabajo import lanzar
from .widgets import confirmar, etiqueta


class LimpiarFiltro(W.QFrame):
    limpiado = Signal(object)        # bytes liberados (pueden pasar de 2 GB: no cabe en int de 32 bits)

    def __init__(self, cfg, padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.setObjectName('tarjeta')
        self.tipo, self.carpeta, self.edad = W.QComboBox(), W.QComboBox(), W.QComboBox()
        for dias in OPCIONES:
            self.edad.addItem(texto_limpiar(dias), dias)
        self.edad.setCurrentIndex(self.edad.findData(365))
        self.ultima = W.QCheckBox(t('incluso_ultima'))
        self.boton = W.QPushButton(t('limpiar_boton'))
        self.boton.setObjectName('peligro')
        self.boton.clicked.connect(self.limpiar)
        self.resultado = etiqueta('', 'gris')
        formulario = W.QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.addRow(t('limpiar_tipo'), self.tipo)
        formulario.addRow(t('limpiar_carpeta'), self.carpeta)
        formulario.addRow(t('limpiar_texto'), self.edad)
        fila = W.QHBoxLayout()
        fila.addWidget(self.resultado, 1)
        fila.addWidget(self.boton)
        caja = W.QVBoxLayout(self)
        caja.setContentsMargins(16, 16, 16, 16)
        caja.setSpacing(8)
        caja.addWidget(etiqueta(t('limpiar_filtro_texto'), 'gris'))
        caja.addLayout(formulario)
        caja.addWidget(self.ultima)
        caja.addLayout(fila)

    def poner(self, tipos: list[str], carpetas: list[str]) -> None:
        """Opciones de los combos a partir de lo que hay en las copias."""
        for combo, todos, valores, nombre in ((self.tipo, 'todos_tipos', tipos, categorias.nombre),
                                              (self.carpeta, 'todas_carpetas', carpetas, self._carpeta)):
            combo.clear()
            combo.addItem(t(todos), None)
            for valor in valores:
                combo.addItem(nombre(valor), valor)

    @staticmethod
    def _carpeta(ruta: str) -> str:
        return os.path.basename(ruta.rstrip('/')) or ruta

    def _descripcion(self) -> str:
        partes = [self.tipo.currentText(), self.carpeta.currentText(), self.edad.currentText()]
        return ', '.join(p for p in partes if p)

    def limpiar(self):
        incluso = self.ultima.isChecked()
        clave = 'limpiar_confirma_ultima' if incluso else 'limpiar_confirma'
        if not confirmar(self, t(clave, que=self._descripcion())):
            return
        tipo, carpeta, dias = self.tipo.currentData(), self.carpeta.currentData(), self.edad.currentData()
        self.boton.setEnabled(False)
        self.resultado.setText(t('limpiando'))

        def trabajo():
            return api.limpiar_filtrado(self.cfg, categoria=tipo, carpeta=carpeta,
                                        anteriores_a_dias=dias, incluso_la_ultima=incluso)
        self.tarea = lanzar(self, trabajo, self._listo, self._fallo)

    def _listo(self, liberados):
        self.boton.setEnabled(True)
        self.resultado.setText(t('limpiar_listo', tam=tam_humano(int(liberados or 0))))
        self.limpiado.emit(int(liberados or 0))

    def _fallo(self, motivo):
        self.boton.setEnabled(True)
        self.resultado.setText(motivo)
