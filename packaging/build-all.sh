#!/usr/bin/env bash
# Build every distributable HordePlayer package into ./dist
set -uo pipefail

ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
DIR="$ROOT/packaging"

ran=0
run() {
  local script="$1" label="$2"
  echo "============================================================"
  echo ">> $label"
  echo "============================================================"
  if bash "$DIR/$script"; then
    ran=$((ran + 1))
  else
    echo "!! $label failed (continuing)" >&2
  fi
}

run build-deb.sh      "Debian/Ubuntu package (.deb)"
run build-rpm.sh      "Fedora/RHEL package (.rpm)"
run build-appimage.sh "Portable AppImage"

echo
echo "Artifacts in $ROOT/dist :"
ls -lh "$ROOT/dist" 2>/dev/null || true
