"""Aspecto general: Fusion con la paleta del tema (Drácula, Alucard o según el sistema) y su hoja de estilos."""
from . import tema
from .estilo_hoja import hoja
from .qt import G

_R = G.QPalette.ColorRole
_ROLES = ((_R.Window, 'fondo'), (_R.WindowText, 'texto'), (_R.Base, 'campo'), (_R.AlternateBase, 'tarjeta'),
          (_R.Text, 'texto'), (_R.Button, 'tarjeta'), (_R.ButtonText, 'texto'), (_R.BrightText, 'texto'),
          (_R.Highlight, 'seleccion'), (_R.HighlightedText, 'texto'), (_R.ToolTipBase, 'tarjeta'),
          (_R.ToolTipText, 'texto'), (_R.PlaceholderText, 'secundario'), (_R.Link, 'cian'),
          (_R.LinkVisited, 'acento'), (_R.Light, 'hover'), (_R.Midlight, 'hover'), (_R.Mid, 'borde_control'),
          (_R.Dark, 'lateral'), (_R.Shadow, 'lateral'), (_R.Accent, 'acento'))
_APAGADOS = (_R.WindowText, _R.Text, _R.ButtonText)


def paleta(colores: dict) -> G.QPalette:
    p = G.QPalette()
    for rol, clave in _ROLES:
        p.setColor(rol, G.QColor(colores[clave]))
    for rol in _APAGADOS:
        p.setColor(G.QPalette.ColorGroup.Disabled, rol, G.QColor(colores['apagado']))
    return p


def aplicar(app, valor: str | None = None) -> str:
    """Pone Fusion, la paleta y la hoja del tema elegido (o del guardado); devuelve el tema concreto aplicado."""
    valor = valor or tema.eleccion()
    nombre = tema.resolver(valor, app)
    colores = tema.activar(nombre)
    app.setStyle('Fusion')
    app.setPalette(paleta(colores))
    app.setStyleSheet(hoja(colores))
    app.setWindowIcon(G.QIcon.fromTheme('document-open-recent'))
    _seguir_al_sistema(app)
    for ventana in app.topLevelWidgets():
        ventana.update()
    return nombre


def _seguir_al_sistema(app) -> None:
    """Con "Según el sistema", cambia de tema cuando el escritorio pasa de claro a oscuro o al revés."""
    if getattr(app, '_historial_sigue_sistema', False) or not hasattr(app.styleHints(), 'colorSchemeChanged'):
        return
    app._historial_sigue_sistema = True
    app.styleHints().colorSchemeChanged.connect(lambda *_: tema.eleccion() == 'sistema' and aplicar(app, 'sistema'))


def margenes(layout, valor: int = 24, separacion: int = 8) -> None:
    layout.setContentsMargins(valor, valor, valor, valor)
    layout.setSpacing(separacion)
