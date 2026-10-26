#!/usr/bin/env bash
set -e
CLAUDE_PROJECT_DIR=$(git rev-parse --show-toplevel)
export CLAUDE_PROJECT_DIR
command -v python3 >/dev/null || { echo "Python 3 ausente" >&2; exit 2; }
exec python3 "$(dirname "$0")/sdd.py" prepare "$@"
