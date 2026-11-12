#!/usr/bin/env bash
# Stop: IaC commitada depois do último apply registrado (.sdd/infra-applied/).
command -v python3 >/dev/null || { echo "Python 3 ausente: bloqueado" >&2; exit 2; }
python3 "$(dirname "$0")/team.py" stop-infra

rc=$?
[ "$rc" -eq 0 ] || { echo "Hook SDD falhou (status $rc): operação bloqueada" >&2; exit 2; }
