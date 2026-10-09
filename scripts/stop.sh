#!/usr/bin/env bash
# HordePlayer - stop the local server
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
exec "$DIR/../packaging/hordeplayer" --stop "$@"
