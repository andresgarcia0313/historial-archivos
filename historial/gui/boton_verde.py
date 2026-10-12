"""Botón redondo verde de "Restaurar a la ubicación original" (flecha circular blanca)."""
from .qt import C, G, Qt, W


class BotonVerde(W.QAbstractButton):
    def __init__(self, diametro: int = 76, padre=None):
        super().__init__(padre)
        self._d = diametro
        self.setFixedSize(diametro, diametro)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        return C.QSize(self._d, self._d)

    def _color(self):
        if not self.isEnabled():
            return G.QColor('#a9c9a9')
        if self.isDown():
            return G.QColor('#0b8a22')
        return G.QColor('#27c244' if self.underMouse() else '#06b025')

    def _flecha(self, p, r: float):
        """Arco de 300 grados con punta de flecha, la silueta de "restaurar" de Windows."""
        pluma = G.QPen(G.QColor('white'), self._d * 0.075)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pluma)
        caja = C.QRectF(-r, -r, 2 * r, 2 * r)
        p.drawArc(caja, 60 * 16, 270 * 16)
        punta = G.QPainterPath()
        punta.moveTo(r * 0.55, -r * 0.95)
        punta.lineTo(r * 1.15, -r * 0.55)
        punta.lineTo(r * 0.35, -r * 0.35)
        punta.closeSubpath()
        p.setBrush(G.QColor('white'))
        p.drawPath(punta)

    def paintEvent(self, evento):
        p = G.QPainter(self)
        p.setRenderHint(G.QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color())
        p.drawEllipse(C.QRectF(2, 2, self._d - 4, self._d - 4))
        p.translate(self._d / 2, self._d / 2)
        self._flecha(p, self._d * 0.22)
        if self.hasFocus():
            p.resetTransform()
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(G.QPen(G.QColor('#1e3287'), 1.5, Qt.PenStyle.DotLine))
            p.drawEllipse(C.QRectF(0.5, 0.5, self._d - 1, self._d - 1))
