"""Ventanas que abren los enlaces del panel lateral (las de Windows): unidad, exclusiones, avanzada y restaurar."""
from .avanzada import Avanzada
from .excluir import Excluir
from .qt import Qt
from .restaurar import Restaurar
from .unidad import Unidad


class Ventanas:
    """Mezcla para Panel: necesita self.cfg, self.hijas y self.refrescar()."""

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
