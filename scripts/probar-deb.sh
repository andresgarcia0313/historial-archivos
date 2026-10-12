#!/usr/bin/env bash
# Prueba de aceptación de un .deb en Ubuntu limpio: apt lo instala con sus dependencias, existen
# el menú, el icono y los menús contextuales, y la aplicación arranca sin pantalla.
# Uso: scripts/probar-deb.sh dist/historial-archivos_<v>_all.deb [imagen...]
#   Sin imágenes prueba ubuntu:24.04 y ubuntu:26.04, de una en una, con podman (o docker).
# Dentro de un contenedor de CI (HISTORIAL_EN_CONTENEDOR=1) prueba el sistema actual.
set -euo pipefail

id="io.github.andresgarcia0313.HistorialArchivos"

probar_aqui() {
  export DEBIAN_FRONTEND=noninteractive
  local deb
  deb="$(realpath "$1")"
  apt-get update -qq >/dev/null
  apt-get install -y -qq "$deb" >/tmp/apt.log 2>&1 || { tail -20 /tmp/apt.log; exit 1; }
  . /etc/os-release
  echo "== $PRETTY_NAME: paquete instalado, dependencias de Qt resueltas:"
  dpkg-query -W -f='${Package} ${Version} ${Architecture}\n' historial-archivos
  dpkg -l | awk '/^ii +python3-(pyside6|pyqt6)/ {print "   " $2, $3}'
  for f in "/usr/share/applications/$id.desktop" "/usr/share/icons/hicolor/scalable/apps/$id.svg" \
           /usr/share/kio/servicemenus/historial-archivos.desktop \
           /usr/share/nautilus-python/extensions/historial_archivos.py /usr/bin/historial-archivos; do
    test -e "$f" || { echo "Falta $f"; exit 1; }
  done
  grep -q '^Exec=historial-archivos$' "/usr/share/applications/$id.desktop"
  grep -q 'historial-archivos --versiones %f' /usr/share/kio/servicemenus/historial-archivos.desktop

  export HOME=/tmp/casa HISTORIAL_SIN_PROGRAMAR=1 QT_QPA_PLATFORM=offscreen
  export XDG_RUNTIME_DIR=/tmp/ejecucion
  mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
  chmod 700 "$XDG_RUNTIME_DIR"
  historial-archivos --estado | /usr/bin/python3 -c 'import json,sys; print("   --estado:", json.load(sys.stdin))'
  # La interfaz debe seguir viva tras 8 s (código 124 de timeout) y sin errores de Python o Qt.
  codigo=0
  timeout 8 historial-archivos >/tmp/gui.log 2>&1 || codigo=$?
  cat /tmp/gui.log
  [[ "$codigo" == 124 || "$codigo" == 0 ]] || { echo "La interfaz terminó con código $codigo"; exit 1; }
  if grep -E "Traceback|ModuleNotFoundError|could not load the Qt platform plugin" /tmp/gui.log; then
    echo "La interfaz reportó errores"; exit 1
  fi
  echo "== $PRETTY_NAME: CORRECTO (interfaz viva, código $codigo)"
}

if [[ "${HISTORIAL_EN_CONTENEDOR:-}" == 1 ]]; then
  probar_aqui "$1"
  exit 0
fi

deb="$(realpath "$1")"
shift
imagenes=("$@")
[[ ${#imagenes[@]} -gt 0 ]] || imagenes=(ubuntu:24.04 ubuntu:26.04)
motor="$(command -v podman || command -v docker)" || { echo "Se necesita podman o docker" >&2; exit 1; }
aqui="$(cd "$(dirname "$0")" && pwd)"
for imagen in "${imagenes[@]}"; do
  echo "=== $imagen (con $(basename "$motor"))"
  nice -n 15 "$motor" run --rm -e HISTORIAL_EN_CONTENEDOR=1 \
    -v "$aqui:/scripts:ro,z" -v "$(dirname "$deb"):/deb:ro,z" \
    "docker.io/library/$imagen" bash /scripts/probar-deb.sh "/deb/$(basename "$deb")"
done
