"""Restaurar archivos personales: carpetas en iconos grandes y línea de tiempo de copias."""
from historial import api

from . import acciones
from .estilo import margenes
from .formato import fecha_texto
from .qt import G, Qt, W
from .restaurar_barra import BarraVersiones
from .restaurar_nav import Navegacion, miga, padre_de
from .restaurar_vista import Vista
from .textos import t
from .widgets import etiqueta


def _boton(icono: str, ayuda: str, accion) -> W.QToolButton:
    b = W.QToolButton()
    b.setIcon(G.QIcon.fromTheme(icono))
    b.setToolTip(ayuda)
    b.setAutoRaise(True)
    b.clicked.connect(lambda *_: accion())
    return b


class Restaurar(W.QMainWindow):
    def __init__(self, carpeta: str = '', cfg=None):
        super().__init__()
        self.cfg = cfg or api.cargar_config()
        self.puntos = api.puntos(self.cfg)
        self.i = len(self.puntos) - 1
        self.nav = Navegacion(carpeta)
        self.tarea = None
        self.setWindowTitle(t('restaurar_titulo'))
        self.resize(980, 640)
        self.vista = Vista()
        self.vista.abrir.connect(self.abrir)
        self.barra = BarraVersiones()
        self.barra.anterior.connect(lambda: self.mover(-1))
        self.barra.siguiente.connect(lambda: self.mover(1))
        self.barra.restaurar.connect(lambda: self.restaurar(None))
        self.atras = _boton('go-previous', t('atras'), lambda: self.navegar('atras'))
        self.adelante = _boton('go-next', t('adelante'), lambda: self.navegar('adelante'))
        self.arriba = _boton('go-up', t('arriba'), lambda: self.navegar('arriba'))
        self.ruta = W.QLineEdit()
        self.ruta.setReadOnly(True)
        self.buscar = W.QLineEdit()
        self.buscar.setPlaceholderText(t('buscar'))
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self.vista.filtrar)
        self.encabezado = etiqueta('', 'subtitulo')
        self.encabezado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.estado = etiqueta('', 'gris')
        self._armar()
        self.recargar()

    def _armar(self):
        fila = W.QHBoxLayout()
        for w in (self.atras, self.adelante, self.arriba):
            fila.addWidget(w)
        fila.addWidget(self.ruta, 3)
        fila.addWidget(self.buscar, 1)
        fila.addWidget(self._engranaje())
        centro = W.QWidget()
        centro.setObjectName('contenido')
        cuerpo = W.QVBoxLayout(centro)
        margenes(cuerpo, 16, 8)
        for parte in (fila, self.encabezado, self.vista, self.estado):
            cuerpo.addLayout(parte) if isinstance(parte, W.QLayout) else cuerpo.addWidget(parte)
        cuerpo.setStretch(2, 1)
        todo = W.QWidget()
        total = W.QVBoxLayout(todo)
        total.setContentsMargins(0, 0, 0, 0)
        total.setSpacing(0)
        total.addWidget(centro, 1)
        total.addWidget(self.barra)
        self.setCentralWidget(todo)

    def _engranaje(self) -> W.QToolButton:
        menu = W.QMenu(self)
        menu.addAction(t('restaurar_en')).triggered.connect(lambda *_: self.restaurar_en())
        menu.addAction(t('sel_todo')).triggered.connect(lambda *_: self.vista.selectAll())
        boton = W.QToolButton()
        boton.setIcon(G.QIcon.fromTheme('configure'))
        boton.setToolTip(t('engranaje'))
        boton.setMenu(menu)
        boton.setPopupMode(W.QToolButton.ToolButtonPopupMode.InstantPopup)
        return boton

    def recargar(self):
        hay = bool(self.puntos)
        entradas = api.listar(self.cfg, self.puntos[self.i].id, self.nav.carpeta) if hay else []
        self.vista.cargar(entradas)
        self.ruta.setText(miga(self.nav.carpeta, self.cfg.carpetas))
        self.barra.ajustar(self.i if hay else -1, len(self.puntos))
        self.atras.setEnabled(self.nav.hay_atras())
        self.adelante.setEnabled(self.nav.hay_adelante())
        self.arriba.setEnabled(bool(self.nav.carpeta))
        fecha = fecha_texto(self.puntos[self.i].fecha, True) if hay else ''
        self.encabezado.setText(t('encabezado_punto', fecha=fecha, n=self.i + 1, m=len(self.puntos)) if hay else '')
        self.estado.setText('' if entradas else t('carpeta_vacia' if hay else 'sin_copias'))

    def mover(self, paso: int):
        self.i = min(max(0, self.i + paso), len(self.puntos) - 1)
        self.recargar()

    def ir(self, carpeta: str):
        self.nav.ir(carpeta)
        self.recargar()

    def navegar(self, como: str):
        if como == 'arriba':
            self.nav.ir(padre_de(self.nav.carpeta, self.cfg.carpetas))
        else:
            getattr(self.nav, como)()
        self.recargar()

    def abrir(self, entrada):
        if entrada.es_carpeta:
            return self.ir(entrada.ruta)
        copia = next((v for v in api.versiones(self.cfg, entrada.ruta) if v.id == entrada.version_id), None)
        if copia:
            acciones.abrir_copia(copia.archivo, entrada.nombre)

    def restaurar_en(self):
        destino = acciones.elegir_destino(self)
        if destino:
            self.restaurar(destino)

    def restaurar(self, destino):
        elegidas = self.vista.seleccionadas() or self.vista.entradas()
        if not elegidas or self.tarea is not None and self.tarea.isRunning():
            return
        self.estado.setText(t('restaurando'))
        acciones.restaurar_entradas(self, self.cfg, elegidas, destino, self._restaurado)

    def _restaurado(self, rutas, error):
        self.estado.setText(t('restaurar_fallo', motivo=error) if error else t('restaurado', n=len(rutas)))

    def closeEvent(self, evento):
        if self.tarea is not None and self.tarea.isRunning():
            self.estado.setText(t('cerrar_ocupado'))
            evento.ignore()
        else:
            super().closeEvent(evento)
