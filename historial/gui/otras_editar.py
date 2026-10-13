"""Cambiar una copia de otra herramienta: activa, frecuencia, carpetas incluidas y excluidas."""
import copy as copiar

from historial import api

from .estilo import margenes
from .lista_rutas import ListaRutas
from .opciones import texto_frecuencia
from .qt import W
from .textos import t
from .widgets import botones_dialogo, etiqueta


class EditarCopia(W.QDialog):
    def __init__(self, copia, padre=None):
        super().__init__(padre)
        self.original = copia
        self.setWindowTitle(t('otras_editar_titulo', nombre=copia.nombre or copia.herramienta))
        self.resize(600, 620)
        self.activa = W.QCheckBox(t('otras_activa_casilla'))
        self.activa.setChecked(copia.activa)
        self.frecuencia = W.QComboBox()
        valores = sorted(set(api.FRECUENCIAS_MIN) | ({copia.frecuencia_min} if copia.frecuencia_min else set()))
        for minutos in valores:
            self.frecuencia.addItem(texto_frecuencia(minutos).replace(t('predeterminado'), ''), minutos)
        self.frecuencia.setCurrentIndex(max(0, self.frecuencia.findData(copia.frecuencia_min or 1440)))
        self.activa.toggled.connect(self.frecuencia.setEnabled)
        self.frecuencia.setEnabled(copia.activa)
        self.incluidas = ListaRutas(t('otras_incluir'), t('incluir_agregar'), copia.carpetas)
        self.excluidas = ListaRutas(t('otras_excluir'), t('agregar'), copia.excluir, t('excluir_vacia'),
                                    'excluir_elegir')
        formulario = W.QFormLayout()
        formulario.setHorizontalSpacing(16)
        formulario.addRow(t('otras_frecuencia'), self.frecuencia)
        total = W.QVBoxLayout(self)
        margenes(total, 24, 8)
        total.addWidget(etiqueta(copia.herramienta, 'titulo'))
        total.addWidget(etiqueta(copia.destino, 'gris'))
        total.addWidget(self.activa)
        total.addLayout(formulario)
        total.addWidget(self.incluidas, 1)
        total.addWidget(self.excluidas, 1)
        total.addWidget(botones_dialogo(self, t('guardar'), t('cancelar')))

    def resultado(self):
        """Copia nueva con los cambios; la original no se toca hasta guardar con éxito."""
        nueva = copiar.deepcopy(self.original)
        nueva.activa = self.activa.isChecked()
        nueva.frecuencia_min = self.frecuencia.currentData() if nueva.activa else self.original.frecuencia_min
        nueva.carpetas = self.incluidas.rutas()
        nueva.excluir = self.excluidas.rutas()
        return nueva
