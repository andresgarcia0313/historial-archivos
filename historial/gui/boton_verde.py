"""Botón redondo verde de "Restaurar a la ubicación original": verde del tema y flecha con contraste AA."""
from . import tema
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
            return tema.color('verde_apagado')
        if self.isDown():
            return tema.color('verde_pulsado')
        return tema.color('verde_hover' if self.underMouse() else 'verde')

    def _flecha(self, p, r: float):
        """Arco de 300 grados con punta de flecha, la silueta de "restaurar" de Windows."""
        tinta = tema.color('sobre_verde' if self.isEnabled() else 'apagado')
        pluma = G.QPen(tinta, self._d * 0.075)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pluma)
        caja = C.QRectF(-r, -r, 2 * r, 2 * r)
        p.drawArc(caja, 60 * 16, 270 * 16)
        punta = G.QPainterPath()
        punta.moveTo(r * 0.55, -r * 0.95)
        punta.lineTo(r * 1.15, -r * 0.55)
        punta.lineTo(r * 0.35, -r * 0.35)
        punta.closeSubpath()
        p.setBrush(tinta)
        p.drawPath(punta)

    def paintEvent(self, evento):
        p = G.QPainter(self)
        p.setRenderHint(G.QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color())
        p.drawEllipse(C.QRectF(4, 4, self._d - 8, self._d - 8))
        p.translate(self._d / 2, self._d / 2)
        self._flecha(p, self._d * 0.22)
        if self.hasFocus():
            p.resetTransform()
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(G.QPen(tema.color('acento'), 2))
            p.drawEllipse(C.QRectF(1, 1, self._d - 2, self._d - 2))
