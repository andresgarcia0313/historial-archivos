"""Tarjetas de cifras clave: rótulo pequeño, número grande y una línea de contexto."""
from .qt import W
from .widgets import etiqueta


class Cifra(W.QFrame):
    def __init__(self, rotulo: str, padre=None):
        super().__init__(padre)
        self.setObjectName('tarjeta')
        self.rotulo = etiqueta(rotulo, 'gris')
        self.valor = etiqueta('-', 'cifra')
        self.detalle = etiqueta('', 'gris')
        caja = W.QVBoxLayout(self)
        caja.setContentsMargins(16, 12, 16, 12)
        caja.setSpacing(2)
        for w in (self.rotulo, self.valor, self.detalle):
            caja.addWidget(w)
        self.setAccessibleName(rotulo)

    def poner(self, valor: str, detalle: str = '') -> None:
        self.valor.setText(valor)
        self.detalle.setText(detalle)
        self.detalle.setVisible(bool(detalle))
        self.setAccessibleDescription(f'{valor} {detalle}'.strip())


class Rejilla(W.QWidget):
    """Tarjetas en columnas fijas que bajan de fila cuando no caben (3 por fila)."""

    def __init__(self, rotulos: dict, columnas: int = 3, padre=None):
        super().__init__(padre)
        self.cifras = {clave: Cifra(texto) for clave, texto in rotulos.items()}
        rejilla = W.QGridLayout(self)
        rejilla.setContentsMargins(0, 0, 0, 0)
        rejilla.setSpacing(8)
        for i, cifra in enumerate(self.cifras.values()):
            rejilla.addWidget(cifra, i // columnas, i % columnas)
        for c in range(columnas):
            rejilla.setColumnStretch(c, 1)

    def __getitem__(self, clave: str) -> Cifra:
        return self.cifras[clave]
