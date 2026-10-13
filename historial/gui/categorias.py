"""Nombres visibles de las categorías de archivo del contrato (y 'otros', lo que no encaja en ninguna)."""
from historial.contrato_uso import CATEGORIAS

from .textos import t

NOMBRES = {'documentos': 'cat_documentos', 'hojas': 'cat_hojas', 'presentaciones': 'cat_presentaciones',
           'imagenes': 'cat_imagenes', 'videos': 'cat_videos', 'audio': 'cat_audio', 'codigo': 'cat_codigo',
           'comprimidos': 'cat_comprimidos', 'otros': 'cat_otros'}
ORDEN = tuple(CATEGORIAS) + ('otros',)


def nombre(categoria: str) -> str:
    """'imagenes' -> 'Imágenes'; una categoría desconocida se muestra tal cual."""
    clave = NOMBRES.get(categoria)
    return t(clave) if clave else categoria


def ejemplos(categoria: str, cuantos: int = 6) -> str:
    """Extensiones de muestra para la ayuda: 'jpg, jpeg, png, gif...'."""
    extensiones = CATEGORIAS.get(categoria, ())
    texto = ', '.join(extensiones[:cuantos])
    return texto + ('...' if len(extensiones) > cuantos else '')
