"""Piezas pequeñas compartidas por las ventanas."""
from .qt import Qt, W


def etiqueta(texto: str = '', nombre: str | None = None) -> W.QLabel:
    """Etiqueta con ajuste de línea; `nombre` enlaza con la hoja de estilos."""
    lbl = W.QLabel(texto)
    lbl.setWordWrap(True)
    if nombre:
        lbl.setObjectName(nombre)
    return lbl


def enlace(texto: str, accion=None) -> W.QPushButton:
    """Botón plano que parece un enlace azul del Panel de control."""
    boton = W.QPushButton(texto)
    boton.setObjectName('enlace')
    boton.setFlat(True)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    if accion:
        boton.clicked.connect(lambda *_: accion())
    return boton


def botones_dialogo(dialogo, texto_ok: str, texto_cancelar: str | None) -> W.QDialogButtonBox:
    """Fila Aceptar/Cancelar con textos propios (acepta y rechaza el diálogo)."""
    caja = W.QDialogButtonBox()
    ok = caja.addButton(texto_ok, W.QDialogButtonBox.ButtonRole.AcceptRole)
    ok.setDefault(True)
    caja.accepted.connect(dialogo.accept)
    if texto_cancelar:
        caja.addButton(texto_cancelar, W.QDialogButtonBox.ButtonRole.RejectRole)
        caja.rejected.connect(dialogo.reject)
    return caja


def aviso(padre, texto: str) -> None:
    """Mensaje informativo modal."""
    W.QMessageBox.information(padre, '', texto)
