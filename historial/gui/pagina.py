"""Página del panel lateral: título, explicación y cuerpo desplazable con márgenes de la rejilla de 8 px."""
from .qt import Qt, W
from .widgets import etiqueta


class Pagina(W.QScrollArea):
    def __init__(self, titulo: str, texto: str, padre=None):
        super().__init__(padre)
        self.setObjectName('pagina')
        self.setWidgetResizable(True)
        self.setFrameShape(W.QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        dentro = W.QWidget()
        dentro.setObjectName('pagina_cuerpo')
        self.cuerpo = W.QVBoxLayout(dentro)
        self.cuerpo.setContentsMargins(32, 28, 32, 24)
        self.cuerpo.setSpacing(8)
        self.cuerpo.addWidget(etiqueta(titulo, 'titulo'))
        if texto:
            self.cuerpo.addWidget(etiqueta(texto, 'gris'))
        self.setWidget(dentro)

    def seccion(self, texto: str) -> W.QLabel:
        lbl = etiqueta(texto, 'seccion')
        self.cuerpo.addWidget(lbl)
        return lbl

    def al_mostrar(self) -> None:
        """La llama el panel cada vez que se elige la página (recarga perezosa)."""
