"""Configuración avanzada: frecuencia, retención, limpiar versiones y registro de eventos."""
import os

from historial import api

from .estilo import margenes
from .limpiar import Limpiar
from .opciones import texto_conservar, texto_frecuencia
from .qt import C, G, W
from .textos import t
from .widgets import aviso, botones_dialogo, enlace, etiqueta


def ruta_registro() -> str:
    base = os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
    return os.path.join(base, 'historial-archivos', 'historial.log')


def _combo(valores, texto, actual) -> W.QComboBox:
    combo = W.QComboBox()
    for valor in valores:
        combo.addItem(texto(valor), valor)
    combo.setCurrentIndex(max(0, combo.findData(actual)))
    return combo


class Avanzada(W.QDialog):
    def __init__(self, cfg, padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.setWindowTitle(t('avanzada_titulo'))
        self.resize(640, 440)
        self.frecuencia = _combo(api.FRECUENCIAS_MIN, texto_frecuencia, cfg.frecuencia_min)
        self.conservar = _combo(api.CONSERVAR_DIAS, texto_conservar, cfg.conservar_dias)
        self.limpiar = enlace(t('avanzada_limpiar'), self.abrir_limpiar)
        self.registro = enlace(t('avanzada_abrir_registro'), self.abrir_registro)
        formulario = W.QFormLayout()
        formulario.setHorizontalSpacing(24)
        formulario.addRow(t('avanzada_copias'), self.frecuencia)
        formulario.addRow(t('avanzada_versiones'), self.conservar)
        total = W.QVBoxLayout(self)
        margenes(total, 24, 10)
        total.addWidget(etiqueta(t('avanzada_titulo'), 'titulo'))
        total.addWidget(etiqueta(t('avanzada_texto')))
        total.addWidget(etiqueta(t('sec_versiones'), 'seccion'))
        total.addLayout(formulario)
        total.addWidget(self.limpiar)
        total.addWidget(etiqueta(t('avanzada_registro'), 'seccion'))
        total.addWidget(self.registro)
        total.addStretch(1)
        total.addWidget(botones_dialogo(self, t('guardar'), t('cancelar')))

    def abrir_limpiar(self):
        Limpiar(self.cfg, self).exec()

    def abrir_registro(self):
        ruta = ruta_registro()
        if os.path.exists(ruta):
            G.QDesktopServices.openUrl(C.QUrl.fromLocalFile(ruta))
        else:
            aviso(self, t('sin_registro'))

    def accept(self):
        self.cfg.frecuencia_min = self.frecuencia.currentData()
        self.cfg.conservar_dias = self.conservar.currentData()
        api.guardar_config(self.cfg)
        super().accept()
