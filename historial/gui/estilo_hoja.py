"""Hoja de estilos con los colores del tema ($rol). Rejilla de 8 px, radios de 6 a 10 px, foco visible de 2 px."""
from string import Template

HOJA = Template("""
QWidget { font-size: 10pt; }
QMainWindow, QDialog, #contenido, #pagina, #pagina_cuerpo { background: $fondo; }
QLabel { background: transparent; }
#titulo { font-size: 17pt; font-weight: 600; }
#subtitulo { font-size: 12pt; font-weight: 600; }
#seccion { font-size: 11pt; font-weight: 600; padding-top: 16px; }
#gris { color: $secundario; }
#aviso { color: $naranja; }
#cifra { font-size: 18pt; font-weight: 600; }
#grupo_lateral { color: $secundario; font-size: 9pt; font-weight: 600; padding: 16px 8px 4px 8px; }
#aviso_caja { background: $aviso_fondo; border: 1px solid $naranja; border-radius: 8px; }
QGroupBox#caja { background: $tarjeta; border: 1px solid $borde; border-radius: 10px;
                 margin-top: 32px; padding: 16px; }
QGroupBox#caja::title { subcontrol-origin: margin; left: 0px; top: 0px; font-size: 12pt; font-weight: 600; }
#tarjeta { background: $tarjeta; border: 1px solid $borde; border-radius: 10px; }
#lateral { background: $lateral; border-right: 1px solid $borde; }
QPushButton#enlace, QToolButton#enlace { color: $cian; background: transparent; border: 2px solid transparent;
    border-radius: 6px; text-align: left; padding: 4px 8px; min-width: 0px; }
QPushButton#enlace:hover { background: $hover; }
QPushButton#enlace:disabled { color: $apagado; }
QPushButton#pagina_lateral { color: $texto; background: transparent; border: 2px solid transparent;
    border-radius: 6px; text-align: left; padding: 4px 8px; min-width: 0px; }
QPushButton#pagina_lateral:hover { background: $hover; }
QPushButton#pagina_lateral:checked { background: $acento_suave; font-weight: 600; }
QPushButton { background: $tarjeta; color: $texto; border: 1px solid $borde_control; border-radius: 6px;
              padding: 6px 16px; min-width: 80px; min-height: 20px; }
QPushButton:hover { background: $hover; }
QPushButton:pressed { background: $seleccion; }
QPushButton:disabled { color: $apagado; border-color: $borde; }
QPushButton#primario, QPushButton:default { background: $acento; color: $sobre_acento; border: 2px solid $acento;
                                            font-weight: 600; }
QPushButton#primario:disabled { background: $seleccion; color: $apagado; border-color: $seleccion; }
QPushButton#peligro { color: $texto; border: 1px solid $rojo; }
QPushButton:focus, QPushButton#enlace:focus, QPushButton#pagina_lateral:focus { border: 2px solid $acento; }
QPushButton#primario:focus, QPushButton:default:focus { border: 2px solid $texto; }
QLineEdit, QComboBox, QSpinBox { background: $campo; color: $texto; border: 1px solid $borde_control;
    border-radius: 6px; padding: 5px 8px; min-height: 20px; selection-background-color: $seleccion; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid $acento; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: $tarjeta; color: $texto; border: 1px solid $borde;
    selection-background-color: $seleccion; selection-color: $texto; }
QListView, QTreeView, QTableView { background: $campo; alternate-background-color: $tarjeta;
    border: 1px solid $borde; border-radius: 8px; selection-background-color: $seleccion; selection-color: $texto; }
QListView:focus, QTreeView:focus, QTableView:focus { border: 2px solid $acento; }
QHeaderView::section { background: $tarjeta; color: $secundario; border: none; border-bottom: 1px solid $borde;
    padding: 4px 8px; font-weight: 600; }
QTableCornerButton::section { background: $tarjeta; border: none; }
QCheckBox { spacing: 8px; }
QCheckBox:focus { color: $acento; }
QProgressBar { border: none; background: $seleccion; max-height: 4px; border-radius: 2px; }
QProgressBar::chunk { background: $verde; border-radius: 2px; }
QScrollArea { border: none; background: $fondo; }
QTabWidget::pane { border: 1px solid $borde; border-radius: 8px; background: $tarjeta; top: -1px; }
QTabBar::tab { background: transparent; color: $secundario; border: none; border-bottom: 2px solid transparent;
               padding: 6px 16px; }
QTabBar::tab:selected { color: $texto; border-bottom: 2px solid $acento; font-weight: 600; }
QTabBar::tab:focus { color: $acento; }
QMenu { background: $tarjeta; color: $texto; border: 1px solid $borde; padding: 4px; }
QMenu::item { padding: 6px 16px; border-radius: 4px; }
QMenu::item:selected { background: $seleccion; }
QToolTip { background: $tarjeta; color: $texto; border: 1px solid $borde; padding: 4px; }
#barra_inferior { background: $lateral; border-top: 1px solid $borde; }
QToolButton { border: 2px solid transparent; border-radius: 6px; padding: 4px; }
QToolButton:hover { background: $hover; }
QToolButton:focus { border: 2px solid $acento; }
QToolButton#redondo { border: 1px solid $borde_control; border-radius: 22px; background: $tarjeta; color: $texto; }
QToolButton#redondo:hover { background: $hover; }
QToolButton#redondo:focus { border: 2px solid $acento; }
QToolButton#redondo:disabled { color: $apagado; border-color: $borde; }
#pildora_si { color: $sobre_verde; background: $verde; border-radius: 9px; padding: 2px 10px; font-weight: 600; }
#pildora_no { color: $secundario; background: $seleccion; border-radius: 9px; padding: 2px 10px; font-weight: 600; }
""")


def hoja(colores: dict) -> str:
    return HOJA.substitute(colores)
