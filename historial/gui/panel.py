"""Ventana principal: Historial de archivos (Panel de control) con sus páginas laterales."""
from historial import api

from . import carpetas_base
from .otras_pagina import OtrasPagina
from .panel_ventanas import Ventanas
from .panel_derecha import Derecha
from .panel_lateral import Lateral
from .qt import C, Qt, W
from .textos import t
from .tipos_pagina import TiposPagina
from .uso_pagina import UsoPagina

PAGINAS = ('pag_inicio', 'pag_uso', 'pag_tipos', 'pag_otras')


class Panel(Ventanas, W.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t('titulo_ventana'))
        self.resize(960, 640)
        self.setMinimumSize(720, 480)
        self.hijas, self.espera = [], 0
        self.sondeo = C.QTimer(self)
        self.sondeo.setInterval(1000)
        self.sondeo.timeout.connect(self.sondear)
        self.cfg = api.cargar_config()
        self.derecha = Derecha()
        self.derecha.activar.clicked.connect(self.alternar)
        self.derecha.ejecutar.clicked.connect(self.ejecutar)
        self.derecha.red.clicked.connect(self.elegir_unidad)
        self.uso, self.tipos, self.otras = UsoPagina(self.cfg), TiposPagina(self.cfg), OtrasPagina()
        self.paginas = W.QStackedWidget()
        for pagina in (self.derecha, self.uso, self.tipos, self.otras):
            self.paginas.addWidget(pagina)
        self.lateral = Lateral((('enl_restaurar', self.abrir_restaurar), ('enl_unidad', self.elegir_unidad),
                                ('enl_excluir', self.excluir), ('enl_avanzada', self.avanzada)),
                               PAGINAS, self.ir)
        centro = W.QWidget()
        centro.setObjectName('contenido')
        fila = W.QHBoxLayout(centro)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(0)
        fila.addWidget(self.lateral)
        fila.addWidget(self.paginas, 1)
        self.setCentralWidget(centro)
        centro.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        centro.setFocus()                                   # sin anillo de foco al abrir; Tab entra al lateral
        self.refrescar()

    def ir(self, indice: int) -> None:
        """Muestra la página `indice` del panel lateral con la configuración vigente."""
        self.lateral.marcar(indice)
        self.paginas.setCurrentIndex(indice)
        pagina = self.paginas.currentWidget()
        if pagina is not self.derecha:
            pagina.cfg = self.cfg
            pagina.al_mostrar()

    def refrescar(self):
        self.cfg = api.cargar_config()
        self.est = api.estado(self.cfg)
        if self.est.en_curso:
            self.espera = 0
        self.derecha.mostrar(self.cfg, self.est, copiando=self.est.en_curso or self.espera > 0)
        if self.est.en_curso or self.espera > 0:
            self.sondeo.start()

    def sondear(self):
        """Mientras copia (aunque lo haya lanzado el temporizador) consulta el estado cada segundo."""
        self.espera = max(0, self.espera - 1)
        self.refrescar()
        if not self.est.en_curso and self.espera == 0:
            self.sondeo.stop()

    def ejecutar(self):
        """Lanza la copia en otro proceso (no bloquea) y vigila hasta que el estado diga que terminó."""
        api.ejecutar_en_segundo_plano()
        self.espera = 3
        self.refrescar()

    def alternar(self):
        if self.cfg.activo:
            self.cfg.activo = False
            api.guardar_config(self.cfg)
        elif self.preparar():
            self.cfg.activo = True
            api.guardar_config(self.cfg)
            self.ejecutar()
        self.refrescar()

    def preparar(self) -> bool:
        """Antes de activar: unidad elegida y carpetas a proteger."""
        if not self.cfg.destino:
            self.elegir_unidad()
        if not self.cfg.carpetas:
            self.cfg.carpetas = carpetas_base.predeterminadas()
        return bool(self.cfg.destino)
