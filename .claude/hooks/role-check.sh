#!/usr/bin/env bash
# Stop: caminhos de um papel (.claude/harness.json) mudaram depois do último pedido ao subagente dele.
command -v python3 >/dev/null || { echo "Python 3 ausente: bloqueado" >&2; exit 2; }
python3 "$(dirname "$0")/team.py" stop-roles

rc=$?
[ "$rc" -eq 0 ] || { echo "Hook SDD falhou (status $rc): operação bloqueada" >&2; exit 2; }
