#!/usr/bin/env bash
# Pre e PostToolUse de Agent/Task/SendMessage: grava em .sdd/roles/PAPEL-head o commit do último pedido que rodou a um
# subagente de papel (.claude/harness.json). Nunca bloqueia nem decide: sai sempre com 0.
command -v python3 >/dev/null || exit 0
python3 "$(dirname "$0")/team.py" role-mark
exit 0
