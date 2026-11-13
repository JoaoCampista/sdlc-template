#!/usr/bin/env bash
# PreToolUse Edit/Write do spec-reviewer: escreve só na memória dele e na cópia de mutação fora do repositório.
# Sem argumento (frontmatter do agente) vale sempre; com "settings" só quando agent_type é spec-reviewer.
command -v python3 >/dev/null || { echo "Python 3 ausente: escrita do revisor negada" >&2; exit 2; }
python3 "$(dirname "$0")/team.py" reviewer-guard "$@"

rc=$?
[ "$rc" -eq 0 ] || { echo "Hook SDD falhou (status $rc): operação bloqueada" >&2; exit 2; }
