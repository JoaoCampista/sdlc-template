#!/usr/bin/env bash
# PreToolUse SendMessage: subagente só fala com a sessão principal ("to": "main").
command -v python3 >/dev/null || { echo "Python 3 ausente: bloqueado" >&2; exit 2; }
python3 "$(dirname "$0")/team.py" message-guard

rc=$?
[ "$rc" -eq 0 ] || { echo "Hook SDD falhou (status $rc): operação bloqueada" >&2; exit 2; }
