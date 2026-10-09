#!/usr/bin/env bash
# HordePlayer - remove a per-user install.
set -uo pipefail

PREFIX="${PREFIX:-$HOME/.local}"
APP="$PREFIX/share/hordeplayer"
ICONS="$PREFIX/share/icons/hicolor"

echo "Removing HordePlayer from $PREFIX ..."
rm -rf "$APP"
rm -f  "$PREFIX/bin/hordeplayer"
rm -f  "$PREFIX/share/applications/hordeplayer.desktop"
rm -f  "$ICONS/128x128/apps/hordeplayer.png" \
       "$ICONS/256x256/apps/hordeplayer.png" \
       "$ICONS/512x512/apps/hordeplayer.png"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q "$PREFIX/share/applications" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t -f "$ICONS" || true

echo "Uninstalled. (Local cache left at ${XDG_CACHE_HOME:-$HOME/.cache}/hordeplayer)"
