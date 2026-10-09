#!/usr/bin/env bash
# Build a Debian/Ubuntu .deb package for HordePlayer.
set -euo pipefail

ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
NAME=hordeplayer
ARCH=all
DIST="$ROOT/dist"
STAGE="$ROOT/build/${NAME}_${VERSION}_${ARCH}"
mkdir -p "$DIST"

command -v dpkg-deb >/dev/null 2>&1 || { echo "dpkg-deb not found" >&2; exit 1; }

rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/usr/share/hordeplayer" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/metainfo" \
         "$STAGE/usr/share/icons/hicolor/128x128/apps" \
         "$STAGE/usr/share/icons/hicolor/256x256/apps" \
         "$STAGE/usr/share/icons/hicolor/512x512/apps" \
         "$STAGE/usr/share/doc/$NAME"

# application payload
cp -r "$ROOT"/app/. "$STAGE/usr/share/hordeplayer/"
cp "$ROOT/LICENSE" "$ROOT/README.md" "$STAGE/usr/share/hordeplayer/"
find "$STAGE/usr/share/hordeplayer" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# launcher + desktop entry + icons
install -m0755 "$ROOT/packaging/hordeplayer"          "$STAGE/usr/bin/$NAME"
install -m0644 "$ROOT/packaging/hordeplayer.desktop"  "$STAGE/usr/share/applications/$NAME.desktop"
install -m0644 "$ROOT/packaging/hordeplayer.appdata.xml" "$STAGE/usr/share/metainfo/$NAME.appdata.xml"
install -m0644 "$ROOT/assets/hordeplayer-128.png"     "$STAGE/usr/share/icons/hicolor/128x128/apps/$NAME.png"
install -m0644 "$ROOT/assets/hordeplayer-256.png"     "$STAGE/usr/share/icons/hicolor/256x256/apps/$NAME.png"
install -m0644 "$ROOT/assets/hordeplayer.png"         "$STAGE/usr/share/icons/hicolor/512x512/apps/$NAME.png"

# docs / copyright
install -m0644 "$ROOT/README.md" "$STAGE/usr/share/doc/$NAME/README.md"
cat > "$STAGE/usr/share/doc/$NAME/copyright" <<EOF
HordePlayer - professional local video player powered by ffmpeg
Copyright (C) 2026 Hordekiller

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

On Debian systems the full text of the GPL-3.0 license is available at
/usr/share/common-licenses/GPL-3.
EOF

# control file
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $NAME
Version: $VERSION
Section: video
Priority: optional
Architecture: $ARCH
Depends: python3, ffmpeg
Recommends: xdg-utils | chromium | firefox | firefox-esr
Maintainer: Hordekiller <Hordekiller@users.noreply.github.com>
Homepage: https://github.com/Hordekiller/HordePlayer
Description: Professional local video player powered by ffmpeg
 HordePlayer plays any video link or local file in a clean, modern web UI.
 A small local ffmpeg server remuxes/transcodes MKV and AC3/E-AC3 audio
 (common in Farsi-dubbed files) that browsers cannot decode, with optional
 audio amplification and EBU R128 normalization.
EOF

# postinst: refresh desktop + icon caches
cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1 && [ -d /usr/share/icons/hicolor ]; then
  gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 0755 "$STAGE/DEBIAN/postinst"

OUT="$DIST/${NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT" >/dev/null
echo "built: $OUT"
