"""Panel izquierdo con los enlaces azules del Historial de archivos."""
from .qt import W
from .textos import t
from .widgets import enlace


class Lateral(W.QWidget):
    def __init__(self, acciones, padre=None):
        """`acciones`: pares (clave de texto, función) en el orden en que aparecen."""
        super().__init__(padre)
        self.setObjectName('lateral')
        self.setFixedWidth(240)
        columna = W.QVBoxLayout(self)
        columna.setContentsMargins(24, 28, 12, 12)
        for clave, accion in acciones:
            columna.addWidget(enlace(t(clave), accion))
        columna.addStretch(1)
