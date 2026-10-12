"""Punto de entrada del .app empaquetado con PyInstaller: misma CLI que el comando de Linux."""
import sys

from historial.cli import main

sys.exit(main())
