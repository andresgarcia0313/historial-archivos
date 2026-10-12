#!/usr/bin/env bash
# Construye dist/Historial-de-archivos-<version>-macos-<arch>.dmg en macOS: PyInstaller (.app
# con PySide6 dentro), firma ad hoc y imagen de disco con el acceso a Aplicaciones.
# Uso: scripts/empaquetar-dmg.sh     Imprime la ruta del .dmg en la última línea.
# Necesita: python con PySide6 y pyinstaller instalados (pip install ".[dev]").
set -euo pipefail

[[ "$(uname -s)" == Darwin ]] || { echo "Este script solo corre en macOS" >&2; exit 1; }
raiz="$(cd "$(dirname "$0")/.." && pwd)"
cd "$raiz"
version="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' historial/__init__.py)"
arquitectura="$(uname -m)"  # arm64 o x86_64
nombre="Historial de archivos"
dmg="dist/Historial-de-archivos-$version-macos-$arquitectura.dmg"

rm -rf build dist/"$nombre.app" dist/historial-archivos
python -I packaging/macos/crear_icns.py \
  packaging/linux/io.github.andresgarcia0313.HistorialArchivos.svg \
  packaging/macos/historial-archivos.icns
python -m PyInstaller --noconfirm packaging/macos/historial-archivos.spec

# PyInstaller reescribe binarios; Apple Silicon se niega a ejecutarlos sin firma.
codesign --force --deep --sign - "dist/$nombre.app"
codesign --verify --deep --strict "dist/$nombre.app"

contenido="$(mktemp -d)"
trap 'rm -rf -- "$contenido"' EXIT
cp -R "dist/$nombre.app" "$contenido/"
ln -s /Applications "$contenido/Applications"
rm -f "$dmg"
hdiutil create -volname "$nombre" -srcfolder "$contenido" -ov -format UDZO "$dmg" >/dev/null
echo "$dmg"
