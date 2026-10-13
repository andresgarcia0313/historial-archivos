"""Piezas pequeñas compartidas por las ventanas."""
from .qt import G, Qt, W
from .textos import t


def etiqueta(texto: str = '', nombre: str | None = None) -> W.QLabel:
    """Etiqueta con ajuste de línea; `nombre` enlaza con la hoja de estilos."""
    lbl = W.QLabel(texto)
    lbl.setWordWrap(True)
    lbl.setIndent(0)                                     # sin sangría extra cuando la hoja le da márgenes
    if nombre:
        lbl.setObjectName(nombre)
    return lbl


def icono(nombre: str, respaldo: str, tinta: G.QColor | None = None) -> G.QIcon:
    """Icono del tema (Linux); sin tema (macOS, sesiones mínimas) el icono estándar del estilo Qt.
    Con `tinta`, el icono monocromo se repinta de ese color (legible en Drácula y en Alucard)."""
    dado = G.QIcon.fromTheme(nombre)
    if dado.isNull():
        dado = W.QApplication.style().standardIcon(getattr(W.QStyle.StandardPixmap, respaldo))
    return colorear(dado, tinta) if tinta is not None else dado


def colorear(base: G.QIcon, color: G.QColor, lado: int = 32) -> G.QIcon:
    imagen = base.pixmap(lado, lado)
    p = G.QPainter(imagen)
    p.setCompositionMode(G.QPainter.CompositionMode.CompositionMode_SourceIn)
    p.fillRect(imagen.rect(), color)
    p.end()
    return G.QIcon(imagen)


def enlace(texto: str, accion=None) -> W.QPushButton:
    """Botón plano que parece un enlace azul del Panel de control."""
    boton = W.QPushButton(texto)
    boton.setObjectName('enlace')
    boton.setFlat(True)
    boton.setAutoDefault(False)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    if accion:
        boton.clicked.connect(lambda *_: accion())
    return boton


def botones_dialogo(dialogo, texto_ok: str, texto_cancelar: str | None) -> W.QDialogButtonBox:
    """Fila Aceptar/Cancelar con textos propios (acepta y rechaza el diálogo)."""
    caja = W.QDialogButtonBox()
    ok = caja.addButton(texto_ok, W.QDialogButtonBox.ButtonRole.AcceptRole)
    ok.setDefault(True)
    ok.setObjectName('primario')
    caja.accepted.connect(dialogo.accept)
    if texto_cancelar:
        caja.addButton(texto_cancelar, W.QDialogButtonBox.ButtonRole.RejectRole)
        caja.rejected.connect(dialogo.reject)
    return caja


def aviso(padre, texto: str) -> None:
    """Mensaje informativo modal."""
    W.QMessageBox.information(padre, '', texto)


def confirmar(padre, texto: str) -> bool:
    """Pregunta modal con Aceptar y Cancelar (textos propios, sin depender de las traducciones de Qt)."""
    caja = W.QMessageBox(padre)
    caja.setText(texto)
    aceptar = caja.addButton(t('aceptar'), W.QMessageBox.ButtonRole.AcceptRole)
    caja.addButton(t('cancelar'), W.QMessageBox.ButtonRole.RejectRole)
    caja.exec()
    return caja.clickedButton() is aceptar
