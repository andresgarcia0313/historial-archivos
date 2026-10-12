"""Genera un .icns a partir del icono SVG: renderiza con Qt las tallas de iconutil.

Uso: python packaging/macos/crear_icns.py <icono.svg> <salida.icns> (necesita macOS: iconutil).
Con --solo-png <carpeta> escribe únicamente el .iconset (útil para revisar en otros sistemas).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

TALLAS = [16, 32, 128, 256, 512]  # cada una con su versión @2x


def escribir_iconset(svg, carpeta):
    """Escribe icon_<t>x<t>.png e icon_<t>x<t>@2x.png, los nombres que exige iconutil."""
    renderizador = QSvgRenderer(str(svg))
    for tamano in TALLAS:
        for factor, sufijo in ((1, ""), (2, "@2x")):
            lado = tamano * factor
            imagen = QImage(lado, lado, QImage.Format.Format_ARGB32)
            imagen.fill(0)
            pintor = QPainter(imagen)
            renderizador.render(pintor)
            pintor.end()
            imagen.save(str(carpeta / f"icon_{tamano}x{tamano}{sufijo}.png"))


def main():
    _app = QGuiApplication(sys.argv[:1])
    if sys.argv[1] == "--solo-png":
        carpeta = Path(sys.argv[3])
        carpeta.mkdir(parents=True, exist_ok=True)
        escribir_iconset(Path(sys.argv[2]), carpeta)
        return
    svg, salida = Path(sys.argv[1]), Path(sys.argv[2])
    with tempfile.TemporaryDirectory() as temporal:
        iconset = Path(temporal) / "icono.iconset"
        iconset.mkdir()
        escribir_iconset(svg, iconset)
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(salida)], check=True)


if __name__ == "__main__":
    main()
