"""Vista de iconos grandes de "Restaurar archivos personales"."""
from .qt import C, G, Qt, Signal, W

_mime = C.QMimeDatabase()


def icono_de(entrada) -> G.QIcon:
    """Icono del tema según el tipo MIME; carpeta con su icono propio."""
    if entrada.es_carpeta:
        return G.QIcon.fromTheme('folder')
    tipo = _mime.mimeTypeForFile(entrada.nombre, C.QMimeDatabase.MatchMode.MatchExtension)
    icono = G.QIcon.fromTheme(tipo.iconName(), G.QIcon.fromTheme(tipo.genericIconName()))
    return icono if not icono.isNull() else G.QIcon.fromTheme('text-x-generic')


class Vista(W.QListView):
    abrir = Signal(object)

    def __init__(self, padre=None):
        super().__init__(padre)
        self.modelo = G.QStandardItemModel(self)
        self.setModel(self.modelo)
        self.setViewMode(W.QListView.ViewMode.IconMode)
        self.setIconSize(C.QSize(64, 64))
        self.setGridSize(C.QSize(120, 110))
        self.setResizeMode(W.QListView.ResizeMode.Adjust)
        self.setMovement(W.QListView.Movement.Static)
        self.setWordWrap(True)
        self.setUniformItemSizes(True)
        self.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(W.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.doubleClicked.connect(lambda idx: self.abrir.emit(idx.data(Qt.ItemDataRole.UserRole)))

    def cargar(self, entradas) -> None:
        self.modelo.clear()
        for entrada in sorted(entradas, key=lambda e: (not e.es_carpeta, e.nombre.lower())):
            item = G.QStandardItem(icono_de(entrada), entrada.nombre)
            item.setData(entrada, Qt.ItemDataRole.UserRole)
            item.setToolTip(entrada.ruta)
            self.modelo.appendRow(item)

    def entradas(self) -> list:
        """Todas las entradas visibles (no ocultas por la búsqueda)."""
        filas = range(self.modelo.rowCount())
        return [self.modelo.item(i).data(Qt.ItemDataRole.UserRole) for i in filas if not self.isRowHidden(i)]

    def seleccionadas(self) -> list:
        return [i.data(Qt.ItemDataRole.UserRole) for i in self.selectedIndexes()]

    def filtrar(self, texto: str) -> None:
        texto = texto.strip().lower()
        for i in range(self.modelo.rowCount()):
            self.setRowHidden(i, bool(texto) and texto not in self.modelo.item(i).text().lower())
