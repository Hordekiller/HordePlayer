#!/usr/bin/env bash
# Build a single-file, portable HordePlayer AppImage.
#
#   BUNDLE_FFMPEG=1 (default)  bundle a static ffmpeg + ffprobe into the AppImage
#   BUNDLE_FFMPEG=0            rely on the system ffmpeg
#   ARCH=x86_64|aarch64        target architecture (default: host arch)
set -euo pipefail

ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
DIST="$ROOT/dist"
BUILD="$ROOT/build"
mkdir -p "$DIST"

ARCH="${ARCH:-$(uname -m)}"
APPDIR="$BUILD/HordePlayer.AppDir"
TOOL="$BUILD/appimagetool-$ARCH.AppImage"

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/share/hordeplayer" "$APPDIR/usr/bin"

# --- payload ---
cp -r "$ROOT"/app/. "$APPDIR/usr/share/hordeplayer/"
cp "$ROOT/LICENSE" "$ROOT/README.md" "$APPDIR/usr/share/hordeplayer/"
find "$APPDIR/usr/share/hordeplayer" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

install -m0755 "$ROOT/packaging/hordeplayer" "$APPDIR/usr/bin/hordeplayer"
mkdir -p "$APPDIR/usr/share/metainfo"
cp "$ROOT/packaging/hordeplayer.appdata.xml" "$APPDIR/usr/share/metainfo/hordeplayer.appdata.xml"
cp "$ROOT/packaging/hordeplayer.desktop" "$APPDIR/hordeplayer.desktop"
cp "$ROOT/assets/hordeplayer.png" "$APPDIR/hordeplayer.png"
cp "$ROOT/assets/hordeplayer.png" "$APPDIR/.DirIcon"

# --- optional bundled ffmpeg ---
if [ "${BUNDLE_FFMPEG:-1}" != "0" ]; then
  FF=""; FP=""
  for c in "$HOME/bin/ffmpeg" "$(command -v ffmpeg 2>/dev/null || true)"; do [ -x "$c" ] && { FF="$c"; break; }; done
  for c in "$HOME/bin/ffprobe" "$(command -v ffprobe 2>/dev/null || true)"; do [ -x "$c" ] && { FP="$c"; break; }; done
  if [ -n "$FF" ]; then cp "$FF" "$APPDIR/usr/bin/ffmpeg"; echo "bundled ffmpeg: $FF"; else echo "WARN: ffmpeg not found; AppImage will use the system ffmpeg"; fi
  if [ -n "$FP" ]; then cp "$FP" "$APPDIR/usr/bin/ffprobe"; fi
fi

# --- AppRun ---
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
export APPDIR="$HERE"
exec "$HERE/usr/bin/hordeplayer" "$@"
EOF
chmod 0755 "$APPDIR/AppRun"

# --- appimagetool ---
if [ ! -x "$TOOL" ]; then
  echo "downloading appimagetool ($ARCH) ..."
  curl -fL --retry 3 -o "$TOOL" \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-$ARCH.AppImage"
  chmod +x "$TOOL"
fi

OUT="$DIST/HordePlayer-$VERSION-$ARCH.AppImage"
export ARCH
APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" --no-appstream "$APPDIR" "$OUT" >/dev/null
echo "built: $OUT"
