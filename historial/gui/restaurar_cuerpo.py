"""Aspecto de Restaurar archivos personales: barra superior, iconos y barra de línea de tiempo."""
from .estilo import margenes
from .qt import Qt, W
from .restaurar_barra import BarraVersiones
from .restaurar_vista import Vista
from .textos import t
from .widgets import etiqueta, icono


def _boton(nombre: str, respaldo: str, ayuda: str) -> W.QToolButton:
    b = W.QToolButton()
    b.setIcon(icono(nombre, respaldo))
    b.setToolTip(ayuda)
    b.setAutoRaise(True)
    return b


class Cuerpo(W.QWidget):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.atras = _boton('go-previous', 'SP_ArrowBack', t('atras'))
        self.adelante = _boton('go-next', 'SP_ArrowForward', t('adelante'))
        self.arriba = _boton('go-up', 'SP_ArrowUp', t('arriba'))
        self.inicio = _boton('go-home', 'SP_DirHomeIcon', t('inicio'))
        self.ruta = W.QLineEdit()
        self.ruta.setReadOnly(True)
        self.buscar = W.QLineEdit()
        self.buscar.setPlaceholderText(t('buscar'))
        self.buscar.setClearButtonEnabled(True)
        self.menu = W.QMenu(self)
        self.accion_en = self.menu.addAction(t('restaurar_en'))
        self.accion_todo = self.menu.addAction(t('sel_todo'))
        engranaje = _boton('configure', 'SP_FileDialogDetailedView', t('engranaje'))
        engranaje.setMenu(self.menu)
        engranaje.setPopupMode(W.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.encabezado = etiqueta('', 'subtitulo')
        self.encabezado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado = etiqueta('', 'gris')
        self.vista = Vista()
        self.barra = BarraVersiones()
        fila = W.QHBoxLayout()
        for w in (self.atras, self.adelante, self.arriba):
            fila.addWidget(w)
        fila.addWidget(self.ruta, 3)
        fila.addWidget(self.buscar, 1)
        fila.addWidget(self.inicio)
        fila.addWidget(engranaje)
        centro = W.QWidget()
        centro.setObjectName('contenido')
        cuerpo = W.QVBoxLayout(centro)
        margenes(cuerpo, 16, 8)
        cuerpo.addLayout(fila)
        cuerpo.addWidget(self.encabezado)
        cuerpo.addWidget(self.vista, 1)
        cuerpo.addWidget(self.estado)
        total = W.QVBoxLayout(self)
        total.setContentsMargins(0, 0, 0, 0)
        total.setSpacing(0)
        total.addWidget(centro, 1)
        total.addWidget(self.barra)
