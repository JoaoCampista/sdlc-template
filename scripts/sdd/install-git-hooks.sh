#!/usr/bin/env bash
set -e
command -v python3 >/dev/null || { echo "Python 3 ausente" >&2; exit 2; }
exec python3 "$(dirname "$0")/sdd.py" install "$@"
