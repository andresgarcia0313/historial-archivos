"""Compatibilidad: PySide6 primero y PyQt6 como alternativa (HISTORIAL_QT=pyqt6 lo fuerza)."""
import os

try:
    if os.environ.get('HISTORIAL_QT', '').lower() == 'pyqt6':
        raise ImportError('PyQt6 forzado')
    from PySide6 import QtCore as C, QtGui as G, QtWidgets as W
    from PySide6.QtCore import Qt, Signal, Slot
    NOMBRE = 'PySide6'
except ImportError:
    from PyQt6 import QtCore as C, QtGui as G, QtWidgets as W
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, pyqtSlot as Slot
    NOMBRE = 'PyQt6'

__all__ = ['C', 'G', 'W', 'Qt', 'Signal', 'Slot', 'NOMBRE']
