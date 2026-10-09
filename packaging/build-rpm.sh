#!/usr/bin/env bash
# Build a Fedora/RHEL .rpm package for HordePlayer.
set -euo pipefail

ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
DIST="$ROOT/dist"
TOPDIR="$ROOT/build/rpm"
mkdir -p "$DIST"

command -v rpmbuild >/dev/null 2>&1 || { echo "rpmbuild not found (install rpm-build)" >&2; exit 1; }

rm -rf "$TOPDIR"
mkdir -p "$TOPDIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

tar czf "$TOPDIR/SOURCES/hordeplayer-$VERSION.tar.gz" \
  -C "$ROOT" --transform "s,^,hordeplayer-$VERSION/," \
  app packaging assets LICENSE README.md VERSION

rpmbuild --define "_topdir $TOPDIR" --define "_hversion $VERSION" \
  -bb "$ROOT/packaging/hordeplayer.spec"

cp "$TOPDIR"/RPMS/noarch/*.rpm "$DIST/"
echo "built: $(ls "$DIST"/*.rpm)"
