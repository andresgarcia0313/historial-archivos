"""Contrato v1.1: copias de seguridad configuradas por otras herramientas (y por esta misma).
Lo implementa el detector en historial/otras/*.py; la GUI solo usa estos nombres."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CopiaDetectada:
    id: str                     # único y estable, p. ej. 'backintime:2'
    herramienta: str            # 'Back In Time' | 'Déjà Dup' | 'Timeshift' | 'Time Machine' | 'Historial de archivos'
    nombre: str                 # nombre del perfil o del destino
    activa: bool                # tiene programación vigente
    destino: str                # ruta local, 'usuario@equipo:/ruta' o URL
    frecuencia: str             # texto legible: 'Cada hora', 'Diaria', 'Manual'...
    frecuencia_min: int | None  # None si no se puede expresar en minutos
    carpetas: list[str] = field(default_factory=list)
    excluir: list[str] = field(default_factory=list)
    ultima: datetime | None = None
    editable: bool = False      # guardar() puede cambiar activa, frecuencia_min, carpetas y excluir
    nota: str = ''              # avisos: 'necesita permisos de administrador', 'destino desconectado'...


def detectar() -> list[CopiaDetectada]: ...      # rápido (< 2 s), sin red ni du; nunca lanza: lo que falla se omite
def tamano(c: CopiaDetectada) -> int | None: ...  # lento (du -sx o equivalente); None si no se puede medir
def guardar(c: CopiaDetectada) -> None: ...       # respalda la config original (.bak-<epoch>) antes de escribir
def abrir_herramienta(c: CopiaDetectada) -> bool: ...  # abre la GUI propia de esa herramienta si existe
