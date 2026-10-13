"""Tarjeta de una copia de seguridad detectada: estado, destino, frecuencia, carpetas, última copia y tamaño."""
import os

from .formato import fecha_texto, tam_humano
from .qt import Qt, Signal, W
from .textos import t
from .widgets import etiqueta


def _carpetas(rutas: list[str]) -> str:
    return ', '.join(os.path.basename(r.rstrip('/')) or r for r in rutas) or '-'


class TarjetaCopia(W.QFrame):
    editar = Signal(object)
    abrir = Signal(object)

    def __init__(self, copia, padre=None):
        super().__init__(padre)
        self.copia = copia
        self.setObjectName('tarjeta')
        titulo = f'{copia.herramienta} - {copia.nombre}' if copia.nombre else copia.herramienta
        self.titulo = etiqueta(titulo, 'subtitulo')
        self.pildora = W.QLabel(t('otras_activa' if copia.activa else 'otras_inactiva'))
        self.pildora.setObjectName('pildora_si' if copia.activa else 'pildora_no')
        cabeza = W.QHBoxLayout()
        cabeza.addWidget(self.titulo, 1)
        cabeza.addWidget(self.pildora, 0, Qt.AlignmentFlag.AlignTop)
        self.tam = etiqueta(t('otras_midiendo'), 'gris')
        datos = W.QFormLayout()
        datos.setHorizontalSpacing(16)
        datos.setVerticalSpacing(4)
        filas = (('otras_destino', copia.destino or '-', ''), ('otras_frecuencia', copia.frecuencia or '-', ''),
                 ('otras_carpetas', _carpetas(copia.carpetas), '\n'.join(copia.carpetas)),
                 ('otras_ultima', fecha_texto(copia.ultima) or t('otras_nunca'), ''))
        for clave, valor, ayuda in filas:
            lbl = etiqueta(valor)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setToolTip(ayuda or valor)
            datos.addRow(etiqueta(t(clave), 'gris'), lbl)
        datos.addRow(etiqueta(t('otras_tam'), 'gris'), self.tam)
        self.boton_abrir = W.QPushButton(t('otras_abrir', herramienta=copia.herramienta))
        self.boton_abrir.clicked.connect(lambda *_: self.abrir.emit(self.copia))
        self.boton_editar = W.QPushButton(t('otras_editar'))
        self.boton_editar.clicked.connect(lambda *_: self.editar.emit(self.copia))
        self.boton_editar.setVisible(copia.editable)
        botones = W.QHBoxLayout()
        botones.addStretch(1)
        botones.addWidget(self.boton_abrir)
        botones.addWidget(self.boton_editar)
        caja = W.QVBoxLayout(self)
        caja.setContentsMargins(16, 16, 16, 16)
        caja.setSpacing(8)
        caja.addLayout(cabeza)
        caja.addLayout(datos)
        if copia.nota:
            caja.addWidget(etiqueta(copia.nota, 'aviso'))
        caja.addLayout(botones)
        self.setAccessibleName(titulo)

    def poner_tam(self, bytes_: int | None) -> None:
        self.tam.setText(t('otras_sin_medir') if bytes_ is None else tam_humano(int(bytes_)))
