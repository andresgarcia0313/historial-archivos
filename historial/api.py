"""Contrato público del motor. La GUI y la CLI solo usan lo que está aquí.

Formato en el destino (igual que Windows, legible sin la aplicación):
  <destino>/HistorialArchivos/<usuario>/<equipo>/Datos/<ruta sin la raíz>/<nombre> (AAAA_MM_DD HH_MM_SS UTC).<ext>
  <destino>/HistorialArchivos/<usuario>/<equipo>/Configuracion/catalogo.sqlite   (copia del catálogo)
Solo se copia lo que cambió (tamaño o fecha de modificación). Un "punto" es una ejecución.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

FRECUENCIAS_MIN = (10, 15, 20, 30, 60, 180, 360, 720, 1440)      # como Windows; 60 por defecto
CONSERVAR_DIAS = (-1, 30, 90, 180, 270, 365, 730, 0)               # -1 = hasta que se necesite espacio, 0 = siempre
PATRONES_DEFECTO = ['~$*', '.~lock.*#', '*.tmp', '*.partial', '*.crdownload', '*~', '.Trash-*',
                    '.cache', '.thumbnails', 'node_modules', '__pycache__', '.venv', '.DS_Store']


@dataclass
class Config:
    activo: bool = False
    destino: str = ''                      # carpeta de una unidad o ubicación de red ya montada
    carpetas: list[str] = field(default_factory=list)    # rutas absolutas a proteger
    excluir: list[str] = field(default_factory=list)     # carpetas absolutas excluidas
    patrones: list[str] = field(default_factory=lambda: list(PATRONES_DEFECTO))
    frecuencia_min: int = 60
    conservar_dias: int = 0
    max_tam_mb: int = 2048                 # archivos más grandes no se copian (0 = sin límite)


@dataclass
class Punto:                               # una ejecución terminada
    id: int
    fecha: datetime                        # hora local


@dataclass
class Entrada:                             # lo que se ve en "Restaurar archivos personales"
    nombre: str
    ruta: str                              # ruta original absoluta
    es_carpeta: bool
    tam: int = 0
    mtime: datetime | None = None
    version_id: int | None = None          # None en carpetas


@dataclass
class Version:                             # pestaña "Versiones anteriores"
    id: int
    ruta: str                              # ruta original
    fecha: datetime                        # fecha de modificación de esa versión (local)
    tam: int
    archivo: str                           # ruta absoluta de la copia en el destino


@dataclass
class Estado:
    activo: bool
    destino_conectado: bool
    ultima_copia: datetime | None
    tam_copias: int                        # bytes ocupados por las versiones
    libre: int                             # bytes libres en el destino
    total: int
    error: str = ''
    en_curso: bool = False


@dataclass
class Resumen:
    punto_id: int
    revisados: int
    copiados: int
    bytes_copiados: int
    errores: list[str] = field(default_factory=list)


def cargar_config() -> Config: ...                                  # ~/.config/historial-archivos/config.json
def guardar_config(cfg: Config) -> None: ...                        # y llama a programador.aplicar(cfg)
def ejecutar(cfg: Config, progreso=None) -> Resumen: ...            # progreso(texto, fraccion 0..1)
def estado(cfg: Config) -> Estado: ...
def puntos(cfg: Config) -> list[Punto]: ...                         # del más antiguo al más reciente
def listar(cfg: Config, punto_id: int, carpeta: str) -> list[Entrada]: ...  # carpeta='' = raíz (las carpetas protegidas)
def versiones(cfg: Config, ruta: str) -> list[Version]: ...         # versiones distintas, la más reciente primero
def restaurar(cfg: Config, entradas: list[Entrada], destino_dir: str | None = None,
              conflicto: str = 'preguntar', decidir=None) -> list[str]: ...
    # destino_dir None = ubicación original. conflicto: 'reemplazar' | 'omitir' | 'renombrar' | 'preguntar'
    # (con 'preguntar', decidir(ruta_existente, version) devuelve uno de los otros tres). Carpetas: recursivo.
    # Devuelve las rutas escritas. Al reemplazar, el archivo actual se versiona antes si cambió.
def limpiar(cfg: Config, anteriores_a_dias: int | None) -> int: ... # None = todas menos la más reciente; bytes liberados
def ejecutar_en_segundo_plano() -> None: ...                        # lanza la copia sin bloquear la GUI ("Ejecutar ahora")
