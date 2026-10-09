#!/usr/bin/env bash
# HordePlayer - per-user install (no root required).
# Installs into $PREFIX (default: ~/.local).
set -euo pipefail

ROOT="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"
APP="$PREFIX/share/hordeplayer"
BIN="$PREFIX/bin"
APPS="$PREFIX/share/applications"
ICONS="$PREFIX/share/icons/hicolor"

echo "Installing HordePlayer into $PREFIX ..."
mkdir -p "$APP" "$BIN" "$APPS" \
         "$ICONS/128x128/apps" "$ICONS/256x256/apps" "$ICONS/512x512/apps"

cp -r "$ROOT"/app/. "$APP/"
cp "$ROOT/LICENSE" "$ROOT/README.md" "$APP/"
find "$APP" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

install -m0755 "$ROOT/packaging/hordeplayer" "$BIN/hordeplayer"

# desktop entry with an absolute Exec so it works even if ~/.local/bin is not in PATH
sed "s|^Exec=hordeplayer|Exec=$BIN/hordeplayer|; s|^TryExec=hordeplayer|TryExec=$BIN/hordeplayer|" \
  "$ROOT/packaging/hordeplayer.desktop" > "$APPS/hordeplayer.desktop"
chmod 0644 "$APPS/hordeplayer.desktop"

install -m0644 "$ROOT/assets/hordeplayer-128.png" "$ICONS/128x128/apps/hordeplayer.png"
install -m0644 "$ROOT/assets/hordeplayer-256.png" "$ICONS/256x256/apps/hordeplayer.png"
install -m0644 "$ROOT/assets/hordeplayer.png"     "$ICONS/512x512/apps/hordeplayer.png"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q "$APPS" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t -f "$ICONS" || true

echo
echo "Done."
echo "  Run:   $BIN/hordeplayer"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "  Note:  add $BIN to your PATH to run 'hordeplayer' directly.";; esac
