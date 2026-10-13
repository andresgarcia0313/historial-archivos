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


PREFIJOS = {'backintime': 'backintime', 'dejadup': 'dejadup', 'timeshift': 'timeshift',
            'timemachine': 'timemachine', 'historial': 'propias'}
ESCRITURA = {'backintime': 'backintime_guardar', 'dejadup': 'dejadup', 'historial': 'propias'}
ORDENES = {'backintime': [['backintime-qt'], ['backintime-qt4']], 'dejadup': [['deja-dup']],
           'timeshift': [['timeshift-launcher'], ['timeshift-gtk']],
           'timemachine': [['open', 'x-apple.systempreferences:com.apple.Time-Machine-Settings.extension']]}


def _modulo(nombre: str):
    from importlib import import_module
    return import_module(f'{__name__}.{nombre}')


def detectar() -> list[CopiaDetectada]:
    """Rápido (< 2 s), sin red ni du; nunca lanza: lo que falla se omite."""
    copias = []
    for nombre in ('propias', 'backintime', 'dejadup', 'timeshift', 'timemachine'):
        try:
            copias += _modulo(nombre).detectar()
        except Exception:  # un detector roto no debe tumbar la página
            continue
    return copias


def tamano(c: CopiaDetectada) -> int | None:
    """Lento (du -sx); None si no se puede medir."""
    nombre = PREFIJOS.get(c.id.split(':', 1)[0])
    try:
        return _modulo(nombre).tamano(c) if nombre else None
    except Exception:
        return None


def guardar(c: CopiaDetectada) -> None:
    """Respalda la config original (.bak-<epoch>) antes de escribir; RuntimeError si no se puede."""
    nombre = ESCRITURA.get(c.id.split(':', 1)[0])
    if not c.editable or not nombre:
        raise RuntimeError(f'{c.herramienta}: esta copia no se puede cambiar desde aquí')
    _modulo(nombre).guardar(c)


def abrir_herramienta(c: CopiaDetectada) -> bool:
    """Abre la GUI propia de esa herramienta si existe."""
    import shutil
    import subprocess
    for orden in ORDENES.get(c.id.split(':', 1)[0], []):
        if shutil.which(orden[0]):
            try:
                subprocess.Popen(orden, start_new_session=True, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return True
            except OSError:
                continue
    return False
