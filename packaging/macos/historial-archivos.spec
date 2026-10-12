# -*- mode: python ; coding: utf-8 -*-
# Especificación de PyInstaller para la aplicación de macOS (--windowed, bundle .app).
# Uso (desde la raíz): pyinstaller --noconfirm packaging/macos/historial-archivos.spec
import os
import re

raiz = os.path.abspath(os.path.join(SPECPATH, "..", ".."))  # noqa: F821 (lo define PyInstaller)
version = re.search(
    r'__version__ = "(.*?)"', open(os.path.join(raiz, "historial", "__init__.py")).read()
).group(1)
icono = os.path.join(SPECPATH, "historial-archivos.icns")  # noqa: F821
nombre_visible = "Historial de archivos"
identificador = "io.github.andresgarcia0313.HistorialArchivos"

# Módulos de Qt que la interfaz no usa: sin ellos el .app pesa mucho menos.
sobrantes = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQml", "PySide6.QtQuick",
    "PySide6.Qt3DCore", "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtPdf", "PySide6.QtDesigner", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtBluetooth",
    "PyQt6", "tkinter",
]

analisis = Analysis(  # noqa: F821
    [os.path.join(SPECPATH, "lanzador.py")],  # noqa: F821
    pathex=[raiz],
    hiddenimports=["historial.gui.app"],  # la CLI lo importa de forma perezosa
    excludes=sobrantes,
)
pyz = PYZ(analisis.pure)  # noqa: F821
ejecutable = EXE(  # noqa: F821
    pyz, analisis.scripts, [], exclude_binaries=True, name="historial-archivos",
    console=False, upx=False,
)
recopilado = COLLECT(  # noqa: F821
    ejecutable, analisis.binaries, analisis.datas, upx=False, name="historial-archivos"
)
app = BUNDLE(  # noqa: F821
    recopilado,
    name=f"{nombre_visible}.app",
    icon=icono if os.path.exists(icono) else None,
    bundle_identifier=identificador,
    version=version,
    info_plist={
        "CFBundleName": nombre_visible,
        "CFBundleDisplayName": nombre_visible,
        "CFBundleExecutable": "historial-archivos",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "CFBundleDevelopmentRegion": "es",
        "CFBundleLocalizations": ["es", "en"],
        "LSMinimumSystemVersion": "12.0",
        "LSApplicationCategoryType": "public.app-category.utilities",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "GPL-3.0-or-later",
        "NSDesktopFolderUsageDescription": "Para copiar las versiones de sus archivos.",
        "NSDocumentsFolderUsageDescription": "Para copiar las versiones de sus archivos.",
        "NSRemovableVolumesUsageDescription": "Para guardar las copias en la unidad elegida.",
        "NSNetworkVolumesUsageDescription": "Para guardar las copias en la carpeta de red elegida.",
    },
)
