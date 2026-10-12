"""Lista de carpetas con Agregar y Quitar (excluidas e incluidas)."""
import os

from .qt import Qt, W
from .textos import t
from .widgets import etiqueta


class ListaRutas(W.QWidget):
    def __init__(self, titulo: str, texto_agregar: str, rutas: list[str], vacia: str = '', pedir: str = 'elegir_carpeta', padre=None):
        super().__init__(padre)
        self.pedir = pedir
        self.lista = W.QListWidget()
        self.lista.setSelectionMode(W.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.vacia = etiqueta(vacia, 'gris')
        self.agregar = W.QPushButton(texto_agregar)
        self.quitar = W.QPushButton(t('quitar'))
        self.agregar.clicked.connect(self.elegir)
        self.quitar.clicked.connect(self.quitar_seleccion)
        self.lista.itemSelectionChanged.connect(self._ajustar)
        fila = W.QHBoxLayout()
        fila.addWidget(self.agregar)
        fila.addWidget(self.quitar)
        fila.addStretch(1)
        total = W.QVBoxLayout(self)
        total.setContentsMargins(0, 0, 0, 0)
        total.addWidget(etiqueta(titulo))
        total.addWidget(self.lista, 1)
        total.addWidget(self.vacia)
        total.addLayout(fila)
        for ruta in rutas:
            self.lista.addItem(ruta)
        self._ajustar()

    def _ajustar(self):
        self.quitar.setEnabled(bool(self.lista.selectedItems()))
        self.vacia.setVisible(self.lista.count() == 0 and bool(self.vacia.text()))

    def elegir(self):
        ruta = W.QFileDialog.getExistingDirectory(self, t(self.pedir), os.path.expanduser('~'))
        if ruta:
            self.poner(ruta)

    def poner(self, ruta: str):
        """Añade la ruta si todavía no está."""
        if not self.lista.findItems(ruta, Qt.MatchFlag.MatchExactly):
            self.lista.addItem(ruta)
        self._ajustar()

    def quitar_seleccion(self):
        for item in self.lista.selectedItems():
            self.lista.takeItem(self.lista.row(item))
        self._ajustar()

    def rutas(self) -> list[str]:
        return [self.lista.item(i).text() for i in range(self.lista.count())]
