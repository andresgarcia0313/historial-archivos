#!/usr/bin/env bash
# Prueba de humo de un .dmg en macOS: lo monta, comprueba firma e Info.plist, ejecuta
# --estado y deja la interfaz arrancar sin pantalla (QT_QPA_PLATFORM=offscreen).
# Uso: scripts/probar-dmg.sh dist/Historial-de-archivos-<v>-macos-<arch>.dmg
set -euo pipefail

dmg="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
punto="$(mktemp -d)"
casa="$(mktemp -d)"
trap 'hdiutil detach "$punto" -quiet || true; rm -rf -- "$punto" "$casa"' EXIT
hdiutil attach "$dmg" -mountpoint "$punto" -nobrowse -readonly -quiet

app="$punto/Historial de archivos.app"
codesign --verify --deep --strict "$app"
plist="$app/Contents/Info.plist"
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$plist")" == io.github.andresgarcia0313.HistorialArchivos
test "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleName' "$plist")" == "Historial de archivos"

export HOME="$casa" HISTORIAL_SIN_PROGRAMAR=1 QT_QPA_PLATFORM=offscreen
binario="$app/Contents/MacOS/historial-archivos"
"$binario" --estado | python3 -c 'import json,sys; print("--estado:", json.load(sys.stdin))'

# macOS no trae timeout: se lanza en segundo plano y se comprueba que siga vivo tras 8 s.
"$binario" >"$casa/gui.log" 2>&1 &
pid=$!
sleep 8
if ! kill -0 "$pid" 2>/dev/null; then
  cat "$casa/gui.log"; echo "La interfaz terminó antes de tiempo"; exit 1
fi
kill "$pid"; wait "$pid" 2>/dev/null || true
cat "$casa/gui.log"
if grep -E "Traceback|ModuleNotFoundError|could not load the Qt platform plugin" "$casa/gui.log"; then
  echo "La interfaz reportó errores"; exit 1
fi
echo "dmg correcto: $(basename "$dmg")"
