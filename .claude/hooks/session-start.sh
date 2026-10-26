#!/usr/bin/env bash
command -v python3 >/dev/null || { echo "Python 3 ausente: SDD indisponível" >&2; exit 2; }
exec python3 "$(dirname "$0")/../../scripts/sdd/sdd.py" session
