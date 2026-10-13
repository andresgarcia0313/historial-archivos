"""Panel izquierdo: la página principal, los enlaces del Historial de archivos de Windows y "Más opciones"."""
from .qt import Qt, W
from .textos import t
from .widgets import enlace, etiqueta


def _pagina(texto: str) -> W.QPushButton:
    boton = W.QPushButton(texto)
    boton.setObjectName('pagina_lateral')
    boton.setCheckable(True)
    boton.setFlat(True)
    return boton


class Lateral(W.QWidget):
    def __init__(self, acciones, paginas=(), al_elegir=None, padre=None):
        """`acciones`: pares (clave de texto, función) que abren ventanas, en el orden de Windows.
        `paginas`: claves de las páginas del panel; la primera (la principal) va arriba y el resto bajo
        "Más opciones". `al_elegir(indice)` cambia de página."""
        super().__init__(padre)
        self.setObjectName('lateral')
        self.setFixedWidth(248)
        self.grupo = W.QButtonGroup(self)
        self.grupo.setExclusive(True)
        self.paginas = [_pagina(t(clave)) for clave in paginas]
        for i, boton in enumerate(self.paginas):
            self.grupo.addButton(boton, i)
            boton.clicked.connect(lambda *_, i=i: al_elegir and al_elegir(i))
        columna = W.QVBoxLayout(self)
        columna.setContentsMargins(16, 24, 16, 16)
        columna.setSpacing(2)
        if self.paginas:
            columna.addWidget(self.paginas[0])
            columna.addSpacing(8)
        for clave, accion in acciones:
            columna.addWidget(enlace(t(clave), accion))
        if len(self.paginas) > 1:
            columna.addWidget(etiqueta(t('grupo_mas'), 'grupo_lateral'))
            for boton in self.paginas[1:]:
                columna.addWidget(boton)
        columna.addStretch(1)
        for boton in self.findChildren(W.QPushButton):      # foco solo con el teclado: el clic no deja anillo
            boton.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.marcar(0)

    def marcar(self, indice: int) -> None:
        if 0 <= indice < len(self.paginas):
            self.paginas[indice].setChecked(True)
