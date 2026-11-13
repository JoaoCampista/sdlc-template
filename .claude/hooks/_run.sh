#!/usr/bin/env bash
# Runner de todo hook do settings.json: roda .claude/hooks/NOME com a mesma entrada, os mesmos argumentos, a mesma saída
# e o mesmo código, e grava uma linha por rodada em .sdd/harness/AAAA-MM.jsonl (decisão, motivo mascarado, alvo, tempo;
# nunca o comando nem conteúdo de arquivo). Uso: _run.sh NOME.sh [args]. Hook ausente ou runner quebrado: sai com 2.
command -v python3 >/dev/null || { echo "_run.sh: Python 3 ausente; hook bloqueado" >&2; exit 2; }
exec python3 "$(dirname "$0")/../../scripts/sdd/harness.py" run "$@"
