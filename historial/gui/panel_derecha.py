"""Zona derecha del panel: aviso, estado, carpetas de origen, destino, última copia y botones."""
import os

from .estilo import margenes
from .formato import fecha_texto, tam_humano
from .qt import W
from .textos import t
from .widgets import enlace, etiqueta


def _nombres(carpetas: list[str]) -> str:
    return ', '.join(os.path.basename(c.rstrip('/')) or c for c in carpetas) or t('ninguna')


def _caja_aviso(red) -> W.QFrame:
    """Recuadro amarillo "No se encontró una unidad..." con el enlace a la ubicación de red."""
    caja = W.QFrame()
    caja.setObjectName('aviso_caja')
    dentro = W.QVBoxLayout(caja)
    dentro.addWidget(etiqueta(t('aviso_unidad')))
    dentro.addWidget(red)
    return caja


class Derecha(W.QWidget):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.red = enlace(t('enl_red'))
        self.caja_aviso = _caja_aviso(self.red)
        self.caja = W.QGroupBox()
        self.caja.setObjectName('caja')
        self.problema = etiqueta('', 'aviso')
        self.desde, self.hacia, self.ultima = etiqueta(), etiqueta(), etiqueta('', 'gris')
        cuadro = W.QGridLayout(self.caja)
        cuadro.setColumnStretch(1, 1)
        cuadro.addWidget(etiqueta(t('desde')), 0, 0)
        cuadro.addWidget(self.desde, 0, 1)
        cuadro.addWidget(etiqueta(t('hacia')), 1, 0)
        cuadro.addWidget(self.hacia, 1, 1)
        cuadro.addWidget(self.problema, 2, 0, 1, 2)
        cuadro.addWidget(self.ultima, 3, 0, 1, 2)
        self.activar = W.QPushButton(t('activar'))
        self.ejecutar = enlace(t('ejecutar'))
        self.progreso = W.QProgressBar()
        self.progreso.setRange(0, 0)
        self.progreso.setTextVisible(False)
        self.avance = etiqueta('', 'gris')
        fila = W.QHBoxLayout()
        fila.addWidget(self.avance, 1)
        fila.addWidget(self.ejecutar)
        fila.addWidget(self.activar)
        total = W.QVBoxLayout(self)
        margenes(total, 28, 10)
        total.addWidget(etiqueta(t('cabecera'), 'titulo'))
        total.addWidget(etiqueta(t('explicacion')))
        total.addWidget(self.caja_aviso)
        total.addWidget(self.caja)
        total.addLayout(fila)
        total.addWidget(self.progreso)
        total.addStretch(1)

    def mostrar(self, cfg, est, copiando: bool = False) -> None:
        """Pinta la configuración y el estado actuales del motor."""
        self.caja.setTitle(t('activado' if est.activo else 'desactivado'))
        self.caja_aviso.setVisible(not cfg.destino)
        self.problema.setText(est.error or (t('reconectar') if cfg.destino and not est.destino_conectado else ''))
        self.desde.setText(_nombres(cfg.carpetas))
        libre = t('libres', libre=tam_humano(est.libre), total=tam_humano(est.total))
        nombre = os.path.basename(cfg.destino.rstrip('/')) or cfg.destino
        self.hacia.setText(f'{nombre}  {libre}' if cfg.destino else t('sin_destino'))
        self.ultima.setText(t('ultima_copia', fecha=fecha_texto(est.ultima_copia)) if est.ultima_copia else '')
        self.activar.setText(t('desactivar' if est.activo else 'activar'))
        self.ejecutar.setEnabled(est.activo and est.destino_conectado and not copiando)
        self.progreso.setVisible(copiando)
        self.avance.setText(t('copiando') if copiando else '')
