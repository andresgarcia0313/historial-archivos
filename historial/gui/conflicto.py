"""Diálogo "Reemplazar u omitir archivos" y el puente que lo muestra desde el hilo de restauración."""
import os
import threading
from datetime import datetime

from .estilo import margenes
from .formato import fecha_texto, tam_humano
from .qt import C, Signal, W
from .textos import t
from .widgets import etiqueta


class DialogoConflicto(W.QDialog):
    """Tres salidas como Windows; cerrar la ventana equivale a omitir."""

    def __init__(self, ruta, version, padre=None):
        super().__init__(padre)
        self.resultado = 'omitir'
        self.setWindowTitle(t('conflicto_titulo'))
        self.resize(520, 330)
        total = W.QVBoxLayout(self)
        margenes(total, 24, 10)
        total.addWidget(etiqueta(t('conflicto_texto', nombre=os.path.basename(ruta)), 'subtitulo'))
        total.addWidget(etiqueta(self._linea('conflicto_actual', os.path.getsize(ruta) if os.path.exists(ruta) else 0,
                                             self._mtime(ruta)), 'gris'))
        total.addWidget(etiqueta(self._linea('conflicto_version', version.tam, version.fecha), 'gris'))
        for clave, valor in (('conflicto_reemplazar', 'reemplazar'), ('conflicto_omitir', 'omitir'),
                             ('conflicto_ambos', 'renombrar')):
            boton = W.QPushButton(t(clave))
            boton.setMinimumHeight(36)
            boton.clicked.connect(lambda _=False, v=valor: self._elegir(v))
            total.addWidget(boton)
        self.todos = W.QCheckBox(t('conflicto_todos'))
        total.addWidget(self.todos)

    @staticmethod
    def _mtime(ruta):
        return datetime.fromtimestamp(os.path.getmtime(ruta)) if os.path.exists(ruta) else None

    @staticmethod
    def _linea(clave, tam, fecha):
        return t(clave, tam=tam_humano(tam), fecha=fecha_texto(fecha))

    def _elegir(self, valor):
        self.resultado = valor
        self.accept()

    @property
    def para_todos(self) -> bool:
        return self.todos.isChecked()


class Decisor(C.QObject):
    """Se llama desde el hilo de restauración (`decidir`); el diálogo sale en el hilo de la interfaz."""

    consulta = Signal(str, object)

    def __init__(self, padre):
        super().__init__(padre)
        self._listo = threading.Event()
        self._respuesta = 'omitir'
        self._para_todos = None
        self.consulta.connect(self._preguntar)

    def __call__(self, ruta, version):
        if self._para_todos:
            return self._para_todos
        self._listo.clear()
        self.consulta.emit(ruta, version)
        self._listo.wait()
        return self._respuesta

    def _preguntar(self, ruta, version):
        dialogo = DialogoConflicto(ruta, version, self.parent())
        dialogo.exec()
        self._respuesta = dialogo.resultado
        if dialogo.para_todos:
            self._para_todos = dialogo.resultado
        self._listo.set()
