"""Contrato v1.1: uso del espacio y filtros por tipo de archivo. Lo implementa el motor en
historial/uso.py y lo reexporta historial.api; la GUI solo usa estos nombres."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

# Categorías para filtrar copias y agrupar el uso. 'otros' = lo que no encaja en ninguna.
CATEGORIAS = {
    'documentos': ('doc', 'docx', 'odt', 'rtf', 'txt', 'md', 'pdf', 'epub', 'tex'),
    'hojas': ('xls', 'xlsx', 'xlsm', 'ods', 'csv', 'tsv', 'numbers'),
    'presentaciones': ('ppt', 'pptx', 'odp', 'key'),
    'imagenes': ('jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'svg', 'bmp', 'tif', 'tiff', 'raw', 'cr2', 'nef', 'psd', 'xcf'),
    'videos': ('mp4', 'mkv', 'mov', 'avi', 'webm', 'm4v', 'wmv'),
    'audio': ('mp3', 'flac', 'ogg', 'opus', 'wav', 'm4a', 'aac'),
    'codigo': ('py', 'js', 'ts', 'java', 'cs', 'c', 'cpp', 'h', 'go', 'rs', 'sh', 'sql', 'json', 'yaml', 'yml', 'xml', 'html', 'css'),
    'comprimidos': ('zip', 'tar', 'gz', 'xz', '7z', 'rar', 'bz2', 'zst', 'iso', 'deb', 'dmg'),
}
# Config gana dos campos (con valores por defecto, compatibles con configuraciones viejas):
#   tipos: list[str] = []                 categorías a copiar; vacío = todas
#   extensiones_excluidas: list[str] = [] extensiones sin punto que nunca se copian


@dataclass
class Grupo:
    nombre: str                 # categoría, carpeta protegida o 'AAAA-MM'
    bytes: int                  # ocupado en el destino por todas sus versiones
    archivos: int               # archivos distintos
    versiones: int


@dataclass
class Uso:
    bytes_copias: int           # todo lo que ocupa el historial en el destino
    bytes_actual: int           # solo la versión más reciente de cada archivo
    archivos: int
    versiones: int
    libre: int                  # destino
    total: int
    primera: datetime | None
    ultima: datetime | None
    por_categoria: list[Grupo] = field(default_factory=list)   # de mayor a menor
    por_carpeta: list[Grupo] = field(default_factory=list)     # carpetas protegidas
    por_mes: list[Grupo] = field(default_factory=list)         # crecimiento, del más antiguo al más reciente
    mas_grandes: list[tuple[str, int, int]] = field(default_factory=list)       # (ruta, bytes totales, versiones), top 20
    mas_versionados: list[tuple[str, int, int]] = field(default_factory=list)   # igual, ordenado por versiones


def categoria_de(nombre: str) -> str: ...                       # por extensión; 'otros' si no encaja
def uso(cfg) -> Uso: ...                                        # solo lee el catálogo: rápido (< 1 s con 50 mil archivos)
def limpiar_filtrado(cfg, categoria: str | None = None, carpeta: str | None = None,
                     anteriores_a_dias: int | None = None, incluso_la_ultima: bool = False) -> int: ...
    # borra versiones de esa categoría y/o carpeta; por defecto conserva la más reciente de cada archivo; bytes liberados
