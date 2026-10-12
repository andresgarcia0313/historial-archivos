"""Zona derecha del panel: estado, carpetas de origen, destino, última copia y botones."""
import os

from .estilo import margenes
from .formato import fecha_texto, tam_humano
from .qt import Qt, W
from .textos import t
from .widgets import etiqueta


def _nombres(carpetas: list[str]) -> str:
    return ', '.join(os.path.basename(c.rstrip('/')) or c for c in carpetas) or t('ninguna')


class Derecha(W.QWidget):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.estado = etiqueta('', 'estado_off')
        self.aviso = etiqueta('', 'aviso')
        self.desde = etiqueta()
        self.hacia = etiqueta()
        self.ultima = etiqueta('', 'gris')
        self.activar = W.QPushButton(t('activar'))
        self.ejecutar = W.QPushButton(t('ejecutar'))
        self.progreso = W.QProgressBar()
        self.progreso.setRange(0, 0)
        self.progreso.setTextVisible(False)
        self.progreso.setVisible(False)
        self.avance = etiqueta('', 'gris')
        total = W.QVBoxLayout(self)
        margenes(total, 28, 8)
        total.addWidget(etiqueta(t('cabecera'), 'titulo'))
        total.addWidget(etiqueta(t('explicacion')))
        total.addSpacing(10)
        for w in (self.estado, self.aviso, etiqueta(t('desde'), 'subtitulo'), self.desde,
                  etiqueta(t('hacia'), 'subtitulo'), self.hacia, self.ultima):
            total.addWidget(w)
        fila = W.QHBoxLayout()
        fila.addWidget(self.activar)
        fila.addWidget(self.ejecutar)
        fila.addStretch(1)
        total.addSpacing(10)
        total.addLayout(fila)
        total.addWidget(self.progreso)
        total.addWidget(self.avance)
        total.addStretch(1)
        total.setAlignment(self.progreso, Qt.AlignmentFlag.AlignTop)

    def mostrar(self, cfg, est, copiando: bool = False) -> None:
        """Pinta la configuración y el estado actuales del motor."""
        self.estado.setText(t('activado' if est.activo else 'desactivado'))
        self.estado.setObjectName('estado_on' if est.activo else 'estado_off')
        self.estado.style().unpolish(self.estado)
        self.estado.style().polish(self.estado)
        problema = est.error or (t('reconectar') if cfg.destino and not est.destino_conectado else '')
        self.aviso.setText(problema)
        self.desde.setText(_nombres(cfg.carpetas))
        self.hacia.setText(f"{os.path.basename(cfg.destino.rstrip('/')) or cfg.destino}  "
                           f"{t('libres', libre=tam_humano(est.libre), total=tam_humano(est.total))}"
                           if cfg.destino else t('sin_destino'))
        self.ultima.setText(t('ultima_copia', fecha=fecha_texto(est.ultima_copia))
                            if est.ultima_copia else t('nunca'))
        self.activar.setText(t('desactivar' if est.activo else 'activar'))
        self.ejecutar.setEnabled(est.activo and est.destino_conectado and not copiando)
        self.progreso.setVisible(copiando)
        self.avance.setText(t('copiando') if copiando else '')
