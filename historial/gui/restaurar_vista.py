"""Vista de iconos grandes de "Restaurar archivos personales", con filtro por nombre y por tipo de archivo."""
from historial import api

from .qt import C, G, Qt, Signal, W
from .widgets import icono

_mime = C.QMimeDatabase()
_TIPO = Qt.ItemDataRole.UserRole + 1


def icono_de(entrada) -> G.QIcon:
    """Icono del tema según el tipo MIME; carpeta con su icono propio; sin tema, los del estilo."""
    if entrada.es_carpeta:
        return icono('folder', 'SP_DirIcon')
    tipo = _mime.mimeTypeForFile(entrada.nombre, C.QMimeDatabase.MatchMode.MatchExtension)
    propio = G.QIcon.fromTheme(tipo.iconName(), G.QIcon.fromTheme(tipo.genericIconName()))
    return propio if not propio.isNull() else icono('text-x-generic', 'SP_FileIcon')


class Vista(W.QListView):
    abrir = Signal(object)

    def __init__(self, padre=None):
        super().__init__(padre)
        self.texto, self.tipo = '', None
        self.modelo = G.QStandardItemModel(self)
        self.setModel(self.modelo)
        self.setViewMode(W.QListView.ViewMode.IconMode)
        self.setIconSize(C.QSize(64, 64))
        self.setGridSize(C.QSize(128, 112))
        self.setResizeMode(W.QListView.ResizeMode.Adjust)
        self.setMovement(W.QListView.Movement.Static)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(W.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.doubleClicked.connect(lambda idx: self.abrir.emit(idx.data(Qt.ItemDataRole.UserRole)))

    def cargar(self, entradas) -> None:
        self.modelo.clear()
        for entrada in sorted(entradas, key=lambda e: (not e.es_carpeta, e.nombre.lower())):
            item = G.QStandardItem(icono_de(entrada), entrada.nombre)
            item.setData(entrada, Qt.ItemDataRole.UserRole)
            item.setToolTip(entrada.ruta)
            item.setData(None if entrada.es_carpeta else api.categoria_de(entrada.nombre), _TIPO)
            self.modelo.appendRow(item)
        self._aplicar()

    def entradas(self) -> list:
        """Todas las entradas visibles (no ocultas por la búsqueda)."""
        filas = range(self.modelo.rowCount())
        return [self.modelo.item(i).data(Qt.ItemDataRole.UserRole) for i in filas if not self.isRowHidden(i)]

    def seleccionadas(self) -> list:
        return [i.data(Qt.ItemDataRole.UserRole) for i in self.selectedIndexes()]

    def filtrar(self, texto: str) -> None:
        self.texto = texto.strip().lower()
        self._aplicar()

    def filtrar_tipo(self, categoria) -> None:
        """Solo los archivos de esa categoría (las carpetas siempre se ven para poder entrar); None = todos."""
        self.tipo = categoria
        self._aplicar()

    def _aplicar(self) -> None:
        for i in range(self.modelo.rowCount()):
            item = self.modelo.item(i)
            oculta_texto = bool(self.texto) and self.texto not in item.text().lower()
            oculta_tipo = bool(self.tipo) and item.data(_TIPO) not in (None, self.tipo)
            self.setRowHidden(i, oculta_texto or oculta_tipo)
