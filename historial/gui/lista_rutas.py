"""Lista de carpetas con Agregar y Quitar (excluidas e incluidas)."""
import os

from .qt import Qt, W
from .textos import t
from .widgets import etiqueta


class ListaRutas(W.QWidget):
    def __init__(self, titulo: str, texto_agregar: str, rutas: list[str], padre=None):
        super().__init__(padre)
        self.lista = W.QListWidget()
        self.lista.setSelectionMode(W.QAbstractItemView.SelectionMode.ExtendedSelection)
        for ruta in rutas:
            self.lista.addItem(ruta)
        self.agregar = W.QPushButton(texto_agregar)
        self.quitar = W.QPushButton(t('quitar'))
        self.agregar.clicked.connect(self.elegir)
        self.quitar.clicked.connect(self.quitar_seleccion)
        lado = W.QVBoxLayout()
        lado.addWidget(self.agregar)
        lado.addWidget(self.quitar)
        lado.addStretch(1)
        cuerpo = W.QHBoxLayout()
        cuerpo.addWidget(self.lista, 1)
        cuerpo.addLayout(lado)
        total = W.QVBoxLayout(self)
        total.setContentsMargins(0, 0, 0, 0)
        total.addWidget(etiqueta(titulo, 'subtitulo'))
        total.addLayout(cuerpo)

    def elegir(self):
        ruta = W.QFileDialog.getExistingDirectory(self, t('elegir_carpeta'), os.path.expanduser('~'))
        if ruta:
            self.poner(ruta)

    def poner(self, ruta: str):
        """Añade la ruta si todavía no está."""
        if not self.lista.findItems(ruta, Qt.MatchFlag.MatchExactly):
            self.lista.addItem(ruta)

    def quitar_seleccion(self):
        for item in self.lista.selectedItems():
            self.lista.takeItem(self.lista.row(item))

    def rutas(self) -> list[str]:
        return [self.lista.item(i).text() for i in range(self.lista.count())]
