"""Página "Otras copias de seguridad": una tarjeta por copia detectada; el tamaño se mide en segundo plano."""
from historial import otras

from .otras_editar import EditarCopia
from .otras_tarjeta import TarjetaCopia
from .pagina import Pagina
from .qt import W
from .textos import t
from .trabajo import lanzar
from .widgets import aviso, etiqueta


class OtrasPagina(Pagina):
    def __init__(self, padre=None):
        super().__init__(t('pag_otras'), t('otras_texto'), padre)
        self.tarjetas, self.tareas, self.buscando, self.vista = [], [], False, False
        self.estado = etiqueta('', 'gris')
        self.buscar = W.QPushButton(t('otras_buscar'))
        self.buscar.clicked.connect(lambda *_: self.detectar())
        fila = W.QHBoxLayout()
        fila.addWidget(self.estado, 1)
        fila.addWidget(self.buscar)
        self.lista = W.QVBoxLayout()
        self.lista.setSpacing(8)
        self.cuerpo.addLayout(fila)
        self.cuerpo.addLayout(self.lista)
        self.cuerpo.addStretch(1)

    def al_mostrar(self) -> None:
        if not self.vista:
            self.vista = True
            self.detectar()

    def detectar(self) -> None:
        if self.buscando:
            return
        self.buscando = True
        self.buscar.setEnabled(False)
        self.estado.setText(t('otras_buscando'))
        self.tareas.append(lanzar(self, otras.detectar, self.mostrar, self._fallo))

    def _fallo(self, motivo: str) -> None:
        self.mostrar([])

    def mostrar(self, copias) -> None:
        self.buscando = False
        self.buscar.setEnabled(True)
        for tarjeta in self.tarjetas:
            tarjeta.setParent(None)
            tarjeta.deleteLater()
        self.tarjetas = [TarjetaCopia(c) for c in copias or []]
        self.estado.setText('' if self.tarjetas else t('otras_vacio'))
        for tarjeta in self.tarjetas:
            tarjeta.editar.connect(self.editar)
            tarjeta.abrir.connect(self.abrir)
            self.lista.addWidget(tarjeta)
            self._medir(tarjeta)

    def _medir(self, tarjeta) -> None:
        copia = tarjeta.copia
        self.tareas.append(lanzar(self, lambda: otras.tamano(copia), tarjeta.poner_tam,
                                  lambda *_: tarjeta.poner_tam(None)))

    def abrir(self, copia) -> None:
        if not otras.abrir_herramienta(copia):
            aviso(self, t('otras_no_abre', herramienta=copia.herramienta))

    def editar(self, copia) -> None:
        dialogo = EditarCopia(copia, self)
        if dialogo.exec() != W.QDialog.DialogCode.Accepted:
            return
        try:
            otras.guardar(dialogo.resultado())
        except Exception as error:  # el detector explica qué falló (permisos, archivo bloqueado...)
            aviso(self, t('otras_fallo', motivo=str(error) or error.__class__.__name__))
            return
        aviso(self, t('otras_guardada'))
        self.detectar()
