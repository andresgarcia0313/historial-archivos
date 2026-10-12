"""Permite `python -m historial`."""
import sys

from .cli import principal

sys.exit(principal())
