"""Textos de la interfaz: español (es) e inglés (en) según el idioma del sistema."""
import os

from .textos_en import EN as _EN
from .textos_en_rest import EN_REST
from .textos_en_v11 import EN_V11
from .textos_es import ES as _ES
from .textos_es_rest import ES_REST
from .textos_es_v11 import ES_V11

ES = {**_ES, **ES_REST, **ES_V11}
EN = {**_EN, **EN_REST, **EN_V11}
_forzado = None


def idioma() -> str:
    """'es' o 'en'. HISTORIAL_IDIOMA manda; luego LC_ALL, LC_MESSAGES y LANG; vacío o C = es."""
    if _forzado:
        return _forzado
    codigo = ''
    for var in ('HISTORIAL_IDIOMA', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        codigo = os.environ.get(var, '')
        if codigo:
            break
    codigo = codigo.lower()
    return 'es' if codigo[:2] == 'es' or codigo in ('', 'c', 'posix') else 'en'


def fijar(codigo):
    """Fuerza el idioma (pruebas). None vuelve a detectarlo."""
    global _forzado
    _forzado = codigo


def t(clave: str, **datos) -> str:
    """Texto traducido; si falta en inglés cae al español, y si falta en ambos, la clave."""
    tabla = EN if idioma() == 'en' else ES
    texto = tabla.get(clave, ES.get(clave, clave))
    return texto.format(**datos) if datos else texto
