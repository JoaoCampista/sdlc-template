#!/usr/bin/env bash
# Stop: os documentos de cima (product-spec, Constitution, clarificações) acompanham o trabalho.
command -v python3 >/dev/null || { echo "Python 3 ausente: bloqueado" >&2; exit 2; }
python3 "$(dirname "$0")/team.py" stop-governance

rc=$?
[ "$rc" -eq 0 ] || { echo "Hook SDD falhou (status $rc): operação bloqueada" >&2; exit 2; }
