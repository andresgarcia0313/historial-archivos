"""Barra inferior de la línea de tiempo: |◀  (botón verde)  ▶|"""
from .boton_verde import BotonVerde
from .qt import Qt, Signal, W
from .textos import t


def _redondo(texto: str, ayuda: str) -> W.QToolButton:
    boton = W.QToolButton()
    boton.setObjectName('redondo')
    boton.setText(texto)
    boton.setToolTip(ayuda)
    boton.setAccessibleName(ayuda)
    boton.setFixedSize(44, 44)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    return boton


class BarraVersiones(W.QWidget):
    anterior = Signal()
    siguiente = Signal()
    restaurar = Signal()

    def __init__(self, padre=None):
        super().__init__(padre)
        self.setObjectName('barra_inferior')
        self.atras = _redondo('|◀', t('version_anterior'))
        self.adelante = _redondo('▶|', t('version_siguiente'))
        self.verde = BotonVerde()
        self.verde.setToolTip(t('restaurar_original'))
        self.verde.setAccessibleName(t('restaurar_original'))
        self.atras.clicked.connect(self.anterior)
        self.adelante.clicked.connect(self.siguiente)
        self.verde.clicked.connect(self.restaurar)
        fila = W.QHBoxLayout(self)
        fila.setContentsMargins(12, 10, 12, 10)
        fila.setSpacing(28)
        fila.addStretch(1)
        for boton in (self.atras, self.verde, self.adelante):
            fila.addWidget(boton, 0, Qt.AlignmentFlag.AlignVCenter)
        fila.addStretch(1)

    def ajustar(self, posicion: int, total: int) -> None:
        """posicion es el índice (0 = copia más antigua); habilita lo que se puede recorrer."""
        self.atras.setEnabled(posicion > 0)
        self.adelante.setEnabled(0 <= posicion < total - 1)
        self.verde.setEnabled(total > 0)
