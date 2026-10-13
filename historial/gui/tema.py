"""Temas Drácula (oscuro, predeterminado) y Alucard (claro), y la elección guardada en la config de la GUI.

Los acentos de Drácula se reasignan a funciones de interfaz (una sola función por color):
morado = acción principal y foco, cian = enlaces, verde = restaurar y éxito, naranja = advertencia,
rojo = destructivo. Contrastes medidos con WCAG (texto principal 13,4:1; secundario 7,6:1).
"""
from .qt import C, G, Qt

ELECCIONES = ('dracula', 'alucard', 'sistema')
PREDETERMINADO = 'dracula'

PALETAS = {
    'dracula': dict(fondo='#282a36', lateral='#21222c', tarjeta='#343746', campo='#21222c', hover='#424450',
                    seleccion='#44475a', texto='#f8f8f2', secundario='#b6bcd8', borde='#44475a',
                    borde_control='#7d8ab8', apagado='#6272a4', acento='#bd93f9', sobre_acento='#282a36',
                    verde='#50fa7b', sobre_verde='#282a36', rojo='#ff5555', naranja='#ffb86c',
                    cian='#8be9fd', rosa='#ff79c6', amarillo='#f1fa8c'),
    'alucard': dict(fondo='#fffbeb', lateral='#ece9df', tarjeta='#fffdf5', campo='#fffdf5', hover='#dedccf',
                    seleccion='#cfcfde', texto='#1f1f1f', secundario='#5c5848', borde='#dedccf',
                    borde_control='#8a8466', apagado='#8a8466', acento='#644ac9', sobre_acento='#ffffff',
                    verde='#14710a', sobre_verde='#ffffff', rojo='#cb3a2a', naranja='#a34d14',
                    cian='#036a96', rosa='#a3144d', amarillo='#846e15'),
}
_actual = {'nombre': PREDETERMINADO, 'colores': dict(PALETAS[PREDETERMINADO])}


def mezclar(fondo: str, color: str, fraccion: float) -> str:
    """`color` al `fraccion` de opacidad sobre `fondo`, como hexadecimal (tintes suaves para áreas grandes)."""
    a, b = G.QColor(fondo), G.QColor(color)
    canal = [round(x + (y - x) * fraccion) for x, y in
             ((a.red(), b.red()), (a.green(), b.green()), (a.blue(), b.blue()))]
    return '#{:02x}{:02x}{:02x}'.format(*canal)


def tokens(nombre: str) -> dict:
    """Colores del tema con los derivados (tintes de aviso, de selección lateral y del verde)."""
    c = dict(PALETAS[nombre])
    c['acento_suave'] = mezclar(c['fondo'], c['acento'], 0.22)
    c['aviso_fondo'] = mezclar(c['fondo'], c['naranja'], 0.12)
    c['verde_hover'] = mezclar(c['verde'], c['texto'], 0.18)
    c['verde_pulsado'] = mezclar(c['verde'], c['fondo'], 0.25)
    c['verde_apagado'] = mezclar(c['fondo'], c['verde'], 0.3)
    return c


def _ajustes():
    return C.QSettings(C.QSettings.Format.IniFormat, C.QSettings.Scope.UserScope, 'historial-archivos', 'gui')


def eleccion() -> str:
    """'dracula' | 'alucard' | 'sistema', guardada en la configuración de la GUI (no en la del motor)."""
    valor = str(_ajustes().value('apariencia/tema', PREDETERMINADO))
    return valor if valor in ELECCIONES else PREDETERMINADO


def guardar(valor: str) -> None:
    if valor not in ELECCIONES:
        raise ValueError(valor)
    ajustes = _ajustes()
    ajustes.setValue('apariencia/tema', valor)
    ajustes.sync()


def resolver(valor: str, app) -> str:
    """Traduce 'sistema' al tema concreto según el esquema de color del escritorio (oscuro si no se sabe)."""
    if valor != 'sistema':
        return valor
    esquema = getattr(app.styleHints(), 'colorScheme', lambda: None)()
    return 'alucard' if esquema == getattr(Qt.ColorScheme, 'Light', object()) else 'dracula'


def activar(nombre: str) -> dict:
    _actual['nombre'], _actual['colores'] = nombre, tokens(nombre)
    return _actual['colores']


def actual() -> str:
    return _actual['nombre']


def color(rol: str) -> G.QColor:
    """Color del tema activo para los widgets que se pintan a mano (botón verde, gráficos)."""
    return G.QColor(_actual['colores'][rol])
