"""Restaurar archivos personales: navegación por carpetas y por la línea de tiempo de copias."""
from historial import api

from . import acciones
from .formato import fecha_texto
from .qt import W
from .restaurar_cuerpo import Cuerpo
from .restaurar_nav import Navegacion, miga, padre_de
from .textos import t


class Restaurar(W.QMainWindow):
    def __init__(self, carpeta: str = '', cfg=None):
        super().__init__()
        self.cfg = cfg or api.cargar_config()
        self.puntos = api.puntos(self.cfg)
        self.i = len(self.puntos) - 1
        self.nav = Navegacion(carpeta)
        self.ocupado = False
        self.setWindowTitle(t('restaurar_titulo'))
        self.resize(980, 640)
        c = self.c = Cuerpo()
        self.setCentralWidget(c)
        c.vista.abrir.connect(self.abrir)
        c.buscar.textChanged.connect(c.vista.filtrar)
        c.barra.anterior.connect(lambda: self.mover(-1))
        c.barra.siguiente.connect(lambda: self.mover(1))
        c.barra.restaurar.connect(lambda: self.restaurar(None))
        c.atras.clicked.connect(lambda *_: self.navegar('atras'))
        c.adelante.clicked.connect(lambda *_: self.navegar('adelante'))
        c.arriba.clicked.connect(lambda *_: self.navegar('arriba'))
        c.accion_en.triggered.connect(lambda *_: self.restaurar_en())
        c.accion_todo.triggered.connect(lambda *_: c.vista.selectAll())
        self.recargar()

    def recargar(self):
        c, hay = self.c, bool(self.puntos)
        entradas = api.listar(self.cfg, self.puntos[self.i].id, self.nav.carpeta) if hay else []
        c.vista.cargar(entradas)
        c.ruta.setText(miga(self.nav.carpeta, self.cfg.carpetas))
        c.barra.ajustar(self.i if hay else -1, len(self.puntos))
        c.atras.setEnabled(self.nav.hay_atras())
        c.adelante.setEnabled(self.nav.hay_adelante())
        c.arriba.setEnabled(bool(self.nav.carpeta))
        fecha = fecha_texto(self.puntos[self.i].fecha, True) if hay else ''
        c.encabezado.setText(t('encabezado_punto', fecha=fecha, n=self.i + 1, m=len(self.puntos)) if hay else '')
        c.estado.setText('' if entradas else t('carpeta_vacia' if hay else 'sin_copias'))

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
        elegidas = self.c.vista.seleccionadas() or self.c.vista.entradas()
        if elegidas and not self.ocupado:
            self.c.estado.setText(t('restaurando'))
            acciones.restaurar_entradas(self, self.cfg, elegidas, destino, self._restaurado)

    def _restaurado(self, rutas, error):
        self.c.estado.setText(t('restaurar_fallo', motivo=error) if error else t('restaurado', n=len(rutas)))

    def closeEvent(self, evento):
        if self.ocupado:
            self.c.estado.setText(t('cerrar_ocupado'))
            evento.ignore()
        else:
            super().closeEvent(evento)
