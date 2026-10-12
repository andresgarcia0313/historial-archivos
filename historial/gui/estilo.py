"""Aspecto general: Fusion con fondo blanco, márgenes amplios y azul de enlaces como Windows."""
from .qt import G

HOJA = """
QWidget { font-size: 10pt; }
QMainWindow, QDialog, #contenido { background: white; }
#titulo { color: #1e3287; font-size: 16pt; }
#subtitulo { color: #1e3287; font-size: 12pt; }
#aviso_caja { background: #ffffe1; border: 1px solid #d6d6a0; }
QGroupBox#caja { border: 1px solid #c8c8c8; margin-top: 18px; padding: 14px 10px 10px 10px; }
QGroupBox#caja::title { subcontrol-origin: margin; left: 0px; top: 0px; color: #1e3287; font-size: 12pt; }
#seccion { color: #1e3287; border-bottom: 1px solid #c8d4f0; padding-top: 10px; }
#aviso { color: #b00020; }
#gris { color: #666666; }
#lateral { background: white; border-right: 1px solid #d9d9d9; }
QPushButton#enlace, QToolButton#enlace { color: #0066cc; border: none; text-align: left; padding: 4px 0; }
QPushButton#enlace:hover, QToolButton#enlace:hover { color: #3399ff; }
QPushButton { min-width: 90px; padding: 5px 14px; }
QProgressBar { border: none; background: #e6e6e6; max-height: 4px; }
QProgressBar::chunk { background: #06b025; }
QListView { border: 1px solid #d9d9d9; }
#barra_inferior { background: #f5f5f5; border-top: 1px solid #d9d9d9; }
QToolButton#redondo { border: 1px solid #bdbdbd; border-radius: 22px; background: #ececec; }
QToolButton#redondo:hover { background: #dcdcdc; }
QToolButton#redondo:disabled { color: #b0b0b0; background: #f3f3f3; }
"""


def aplicar(app) -> None:
    """Deja la aplicación con estilo Fusion y la hoja de estilos común."""
    app.setStyle('Fusion')
    paleta = app.palette()
    paleta.setColor(G.QPalette.ColorRole.Window, G.QColor('white'))
    app.setPalette(paleta)
    app.setStyleSheet(HOJA)
    app.setWindowIcon(G.QIcon.fromTheme('document-open-recent'))


def margenes(layout, valor: int = 20, separacion: int = 10) -> None:
    layout.setContentsMargins(valor, valor, valor, valor)
    layout.setSpacing(separacion)
