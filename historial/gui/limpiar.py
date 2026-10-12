"""Limpiar versiones: borra copias antiguas sin bloquear la interfaz."""
from historial import api

from .estilo import margenes
from .formato import tam_humano
from .opciones import texto_limpiar
from .qt import W
from .textos import t
from .trabajo import lanzar
from .widgets import etiqueta

OPCIONES = (365, None, 30, 90, 180, 270, 730)      # el orden de Windows: 1 año primero


class Limpiar(W.QDialog):
    def __init__(self, cfg, padre=None):
        super().__init__(padre)
        self.cfg = cfg
        self.setWindowTitle(t('limpiar_titulo'))
        self.resize(460, 240)
        self.combo = W.QComboBox()
        for dias in OPCIONES:
            self.combo.addItem(texto_limpiar(dias), dias)
        self.resultado = etiqueta('', 'gris')
        self.boton = W.QPushButton(t('limpiar_boton'))
        self.boton.clicked.connect(self.limpiar)
        cerrar = W.QPushButton(t('cerrar'))
        cerrar.clicked.connect(self.reject)
        fila = W.QHBoxLayout()
        fila.addStretch(1)
        fila.addWidget(self.boton)
        fila.addWidget(cerrar)
        total = W.QVBoxLayout(self)
        margenes(total, 24, 12)
        total.addWidget(etiqueta(t('limpiar_titulo'), 'titulo'))
        total.addWidget(etiqueta(t('limpiar_texto')))
        total.addWidget(self.combo)
        total.addWidget(self.resultado)
        total.addStretch(1)
        total.addLayout(fila)

    def limpiar(self):
        dias = self.combo.currentData()
        self.boton.setEnabled(False)
        self.resultado.setText(t('copiando'))
        self.tarea = lanzar(self, lambda: api.limpiar(self.cfg, dias), self._listo, self._fallo)

    def _listo(self, bytes_liberados):
        self.boton.setEnabled(True)
        self.resultado.setText(t('limpiar_listo', tam=tam_humano(int(bytes_liberados))))

    def _fallo(self, motivo):
        self.boton.setEnabled(True)
        self.resultado.setText(motivo)
