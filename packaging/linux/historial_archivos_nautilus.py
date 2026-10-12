"""Extensión de Nautilus (nautilus-python): menú contextual de Historial de archivos.

Funciona con Nautilus 4 (GNOME 43 o posterior) y con Nautilus 3.
Se instala en /usr/share/nautilus-python/extensions/.
"""
import locale
import subprocess
from urllib.parse import unquote, urlparse

import gi

try:
    gi.require_version("Nautilus", "4.0")
except ValueError:
    gi.require_version("Nautilus", "3.0")
from gi.repository import GObject, Nautilus

EN_ESPANOL = (locale.getlocale()[0] or "").startswith("es")
TEXTO_VERSIONES = "Versiones anteriores" if EN_ESPANOL else "Previous versions"
TEXTO_RESTAURAR = "Restaurar archivos personales" if EN_ESPANOL else "Restore personal files"


def _ruta_local(archivo):
    """Ruta local del archivo seleccionado, o None si no es local (por ejemplo, red sin montar)."""
    uri = urlparse(archivo.get_uri())
    return unquote(uri.path) if uri.scheme == "file" else None


def _lanzar(*argumentos):
    subprocess.Popen(["historial-archivos", *argumentos], start_new_session=True)


class ExtensionHistorial(GObject.GObject, Nautilus.MenuProvider):
    """Añade «Versiones anteriores» y «Restaurar archivos personales» al menú contextual."""

    def _al_pedir_versiones(self, _item, ruta):
        _lanzar("--versiones", ruta)

    def _al_pedir_restaurar(self, _item):
        _lanzar("--restaurar")

    def get_file_items(self, *argumentos):
        archivos = argumentos[-1]  # Nautilus 3 pasa (ventana, archivos); Nautilus 4 solo archivos
        if len(archivos) != 1 or _ruta_local(archivos[0]) is None:
            return []
        versiones = Nautilus.MenuItem(
            name="HistorialArchivos::Versiones", label=TEXTO_VERSIONES, icon="io.github.andresgarcia0313.HistorialArchivos"
        )
        versiones.connect("activate", self._al_pedir_versiones, _ruta_local(archivos[0]))
        restaurar = Nautilus.MenuItem(
            name="HistorialArchivos::Restaurar", label=TEXTO_RESTAURAR, icon="io.github.andresgarcia0313.HistorialArchivos"
        )
        restaurar.connect("activate", self._al_pedir_restaurar)
        return [versiones, restaurar]
