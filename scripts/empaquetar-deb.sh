#!/usr/bin/env bash
# Construye dist/historial-archivos_<version>_all.deb (Python puro, Architecture: all).
# Uso: scripts/empaquetar-deb.sh        Imprime la ruta del .deb en la última línea.
# Necesita: dpkg-deb (dpkg). Los módulos van a /usr/lib/python3/dist-packages.
set -euo pipefail
umask 022

raiz="$(cd "$(dirname "$0")/.." && pwd)"
id="io.github.andresgarcia0313.HistorialArchivos"
version="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$raiz/historial/__init__.py")"
[[ -n "$version" ]] || { echo "No se encontró __version__" >&2; exit 1; }
salida="$raiz/dist"
paquete="$(mktemp -d)"
trap 'rm -rf -- "$paquete"' EXIT
destino="$paquete/usr/lib/python3/dist-packages"

install -d "$destino"
cp -r "$raiz/historial" "$destino/historial"
find "$destino" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$destino" -type f -exec chmod 644 {} +
find "$destino" -type d -exec chmod 755 {} +

install -Dm755 /dev/stdin "$paquete/usr/bin/historial-archivos" <<'EOF'
#!/usr/bin/python3
import sys

from historial.cli import main

sys.exit(main())
EOF
install -Dm644 "$raiz/packaging/linux/$id.desktop" "$paquete/usr/share/applications/$id.desktop"
install -Dm644 "$raiz/packaging/linux/$id.svg" "$paquete/usr/share/icons/hicolor/scalable/apps/$id.svg"
install -Dm644 "$raiz/packaging/linux/historial-archivos-dolphin.desktop" \
  "$paquete/usr/share/kio/servicemenus/historial-archivos.desktop"
install -Dm644 "$raiz/packaging/linux/historial_archivos_nautilus.py" \
  "$paquete/usr/share/nautilus-python/extensions/historial_archivos.py"

doc="$paquete/usr/share/doc/historial-archivos"
install -d "$doc"
install -m644 "$raiz/README.md" "$doc/README.md"
cat > "$doc/copyright" <<EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: historial-archivos
Source: https://github.com/andresgarcia0313/historial-archivos

Files: *
Copyright: 2026 Andrés García
License: GPL-3+
 En Debian y Ubuntu el texto completo está en /usr/share/common-licenses/GPL-3.
EOF
printf 'historial-archivos (%s) unstable; urgency=medium\n\n  * Ver las notas de la versión en GitHub.\n\n -- Andrés García <andresgarcia0313@users.noreply.github.com>  %s\n' \
  "$version" "$(date -R)" | gzip -9n > "$doc/changelog.Debian.gz"

install -d "$paquete/DEBIAN"
install -m755 /dev/stdin "$paquete/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
# Precompila para que el primer arranque no escriba en /usr (falla en silencio si no hay python3).
python3 -m compileall -q /usr/lib/python3/dist-packages/historial >/dev/null 2>&1 || true
exit 0
EOF
install -m755 /dev/stdin "$paquete/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
find /usr/lib/python3/dist-packages/historial -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
exit 0
EOF
tamano="$(du -sk --exclude=DEBIAN "$paquete" | cut -f1)"
cat > "$paquete/DEBIAN/control" <<EOF
Package: historial-archivos
Version: $version
Section: utils
Priority: optional
Architecture: all
Installed-Size: $tamano
Depends: python3 (>= 3.10), python3-pyside6.qtwidgets | python3-pyqt6
Suggests: python3-nautilus
Maintainer: Andrés García <andresgarcia0313@users.noreply.github.com>
Homepage: https://github.com/andresgarcia0313/historial-archivos
Description: Historial de archivos al estilo de Windows (File History)
 Guarda versiones de tus carpetas personales en una unidad o carpeta de red,
 sin demonio residente (temporizador de systemd de usuario), y permite
 restaurarlas desde una línea de tiempo. Incluye menú contextual para
 Dolphin y Nautilus.
EOF

mkdir -p "$salida"
deb="$salida/historial-archivos_${version}_all.deb"
dpkg-deb --root-owner-group --build "$paquete" "$deb" >/dev/null
echo "$deb"
