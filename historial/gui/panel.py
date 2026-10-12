"""Ventana principal: Historial de archivos (Panel de control)."""
from historial import api

from . import carpetas_base
from .avanzada import Avanzada
from .excluir import Excluir
from .panel_derecha import Derecha
from .qt import C, Qt, W
from .restaurar import Restaurar
from .textos import t
from .unidad import Unidad
from .widgets import enlace


class Panel(W.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t('titulo_ventana'))
        self.resize(900, 560)
        self.hijas = []
        self.espera = 0
        self.sondeo = C.QTimer(self)
        self.sondeo.setInterval(1000)
        self.sondeo.timeout.connect(self.sondear)
        self.derecha = Derecha()
        self.derecha.activar.clicked.connect(self.alternar)
        self.derecha.ejecutar.clicked.connect(self.ejecutar)
        lateral = W.QWidget()
        lateral.setObjectName('lateral')
        lateral.setFixedWidth(240)
        columna = W.QVBoxLayout(lateral)
        columna.setContentsMargins(24, 28, 12, 12)
        for clave, accion in (('enl_restaurar', self.abrir_restaurar), ('enl_unidad', self.elegir_unidad),
                              ('enl_excluir', self.excluir), ('enl_avanzada', self.avanzada)):
            columna.addWidget(enlace(t(clave), accion))
        columna.addStretch(1)
        centro = W.QWidget()
        centro.setObjectName('contenido')
        fila = W.QHBoxLayout(centro)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(0)
        fila.addWidget(lateral)
        fila.addWidget(self.derecha, 1)
        self.setCentralWidget(centro)
        self.refrescar()

    def refrescar(self):
        self.cfg = api.cargar_config()
        est = api.estado(self.cfg)
        self.derecha.mostrar(self.cfg, est)
        if est.en_curso:
            self.espera = 0
        if (est.en_curso or self.espera > 0) and not self.sondeo.isActive():
            self.sondeo.start()

    def sondear(self):
        """Mientras copia (aunque lo haya lanzado el temporizador) consulta el estado cada segundo."""
        self.espera -= 1
        self.refrescar()
        if not api.estado(self.cfg).en_curso and self.espera <= 0:
            self.sondeo.stop()

    def ejecutar(self):
        api.ejecutar_en_segundo_plano()
        self.espera = 3
        self.derecha.ejecutar.setEnabled(False)
        self.derecha.progreso.setVisible(True)
        self.derecha.avance.setText(t('copiando'))
        self.sondeo.start()

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

    def _dialogo(self, clase):
        clase(self.cfg, self).exec()
        self.refrescar()

    def elegir_unidad(self):
        self._dialogo(Unidad)

    def excluir(self):
        self._dialogo(Excluir)

    def avanzada(self):
        self._dialogo(Avanzada)

    def abrir_restaurar(self):
        ventana = Restaurar(cfg=self.cfg)
        ventana.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        ventana.show()
        self.hijas.append(ventana)
