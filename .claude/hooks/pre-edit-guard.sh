#!/usr/bin/env bash
command -v python3 >/dev/null || { echo "Python 3 ausente: ferramenta bloqueada" >&2; exit 2; }
python3 "$(dirname "$0")/guard.py" edit

rc=$?
[ "$rc" -eq 0 ] || { echo "Hook SDD falhou (status $rc): operação bloqueada" >&2; exit 2; }
