"""Gráficos de barras pintados con QPainter (sin QtCharts): horizontales por tipo o carpeta y verticales por mes.

Una sola serie y un solo color (el acento): la longitud compara, el número exacto va escrito al lado.
"""
from . import tema
from .qt import C, G, Qt, W
from .textos import t

FILA, ETIQUETA, VALOR = 28, 176, 88


class _Grafico(W.QWidget):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.datos = []                     # [(etiqueta, valor, texto del valor)]
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def poner(self, datos) -> None:
        self.datos = [d for d in datos if d[1] >= 0]
        self.setAccessibleDescription('; '.join(f'{e}: {v}' for e, _, v in self.datos) or t('grafico_vacio'))
        self.setToolTip('\n'.join(f'{e}: {v}' for e, _, v in self.datos))
        self.updateGeometry()
        self.update()

    def _vacio(self, p) -> bool:
        if self.datos and max(d[1] for d in self.datos) > 0:
            return False
        p.setPen(tema.color('secundario'))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, t('grafico_vacio'))
        return True


class BarrasH(_Grafico):
    def sizeHint(self):
        return C.QSize(480, max(1, len(self.datos)) * FILA + 4)

    def minimumSizeHint(self):
        return C.QSize(320, self.sizeHint().height())

    def paintEvent(self, evento):
        p = G.QPainter(self)
        p.setRenderHint(G.QPainter.RenderHint.Antialiasing)
        if self._vacio(p):
            return
        tope = max(d[1] for d in self.datos)
        ancho = max(8, self.width() - ETIQUETA - VALOR - 16)
        medidas = G.QFontMetrics(self.font())
        for i, (etiqueta, valor, texto) in enumerate(self.datos):
            y = i * FILA
            p.setPen(tema.color('texto'))
            nombre = medidas.elidedText(etiqueta, Qt.TextElideMode.ElideMiddle, ETIQUETA - 8)
            p.drawText(C.QRect(0, y, ETIQUETA - 8, FILA), Qt.AlignmentFlag.AlignVCenter, nombre)
            largo = max(3, round(ancho * valor / tope)) if valor else 0
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(tema.color('acento'))
            p.drawRoundedRect(C.QRectF(ETIQUETA, y + 8, largo, FILA - 16), 3, 3)
            p.setPen(tema.color('secundario'))
            caja = C.QRect(ETIQUETA + largo + 8, y, VALOR + 8, FILA)
            p.drawText(caja, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, texto)


class BarrasV(_Grafico):
    ALTO = 168

    def sizeHint(self):
        return C.QSize(480, self.ALTO)

    def minimumSizeHint(self):
        return C.QSize(320, self.ALTO)

    def paintEvent(self, evento):
        p = G.QPainter(self)
        p.setRenderHint(G.QPainter.RenderHint.Antialiasing)
        if self._vacio(p):
            return
        tope = max(d[1] for d in self.datos)
        base, arriba = self.height() - 24, 24
        paso = self.width() / len(self.datos)
        cada = max(1, round(len(self.datos) / max(1, self.width() // 64)))   # etiquetas que caben sin pisarse
        p.setPen(G.QPen(tema.color('borde'), 1))
        p.drawLine(0, base, self.width(), base)
        for i, (etiqueta, valor, texto) in enumerate(self.datos):
            alto = round((base - arriba) * valor / tope) if valor else 0
            x = i * paso + paso * 0.2
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(tema.color('acento'))
            p.drawRoundedRect(C.QRectF(x, base - alto, paso * 0.6, alto), 3, 3)
            p.setPen(tema.color('secundario'))
            if i % cada == 0 or i == len(self.datos) - 1:
                p.drawText(C.QRectF(i * paso - 16, base + 4, paso + 32, 18), Qt.AlignmentFlag.AlignHCenter, etiqueta)
            if valor == tope or i == len(self.datos) - 1:
                p.setPen(tema.color('texto'))
                caja = C.QRectF(i * paso - 32, base - alto - 20, paso + 64, 18)
                p.drawText(caja, Qt.AlignmentFlag.AlignHCenter, texto)
