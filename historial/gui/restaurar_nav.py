"""Navegación de carpetas de Restaurar: historial Atrás/Adelante, Arriba y barra de ruta."""
import os

from .textos import t


class Navegacion:
    def __init__(self, inicial: str = ''):
        self.pila = [inicial]
        self.pos = 0

    @property
    def carpeta(self) -> str:
        return self.pila[self.pos]

    def ir(self, carpeta: str) -> None:
        if carpeta != self.carpeta:
            self.pila = self.pila[:self.pos + 1] + [carpeta]
            self.pos += 1

    def atras(self) -> None:
        self.pos = max(0, self.pos - 1)

    def adelante(self) -> None:
        self.pos = min(len(self.pila) - 1, self.pos + 1)

    def hay_atras(self) -> bool:
        return self.pos > 0

    def hay_adelante(self) -> bool:
        return self.pos < len(self.pila) - 1


def padre_de(carpeta: str, raices: list[str]) -> str:
    """Carpeta superior; las carpetas protegidas suben a Inicio ('')."""
    if not carpeta or carpeta in raices:
        return ''
    return os.path.dirname(carpeta.rstrip('/')) or ''


def _raiz_de(carpeta: str, raices: list[str]) -> str:
    propias = [r for r in raices if carpeta == r or carpeta.startswith(r.rstrip('/') + '/')]
    return max(propias, key=len) if propias else ''


def miga(carpeta: str, raices: list[str]) -> str:
    """Inicio > Documentos > Informes (la ruta completa si cuelga de una carpeta no protegida)."""
    partes = [t('inicio')]
    if carpeta:
        raiz = _raiz_de(carpeta, raices)
        if raiz:
            partes.append(os.path.basename(raiz.rstrip('/')) or raiz)
            partes += [p for p in os.path.relpath(carpeta, raiz).split(os.sep) if p != '.']
        else:
            partes += [p for p in carpeta.split(os.sep) if p]
    return '  ›  '.join(partes)
