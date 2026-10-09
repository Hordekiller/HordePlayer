#!/usr/bin/env bash
# HordePlayer - run from the source tree
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
exec "$DIR/../packaging/hordeplayer" "$@"
