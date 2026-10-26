#!/usr/bin/env bash
# Idempotente: não cria commit, muda identidade ou apaga estado da sessão.
set -eu
cd "$(dirname "$0")/.."
CLAUDE_PROJECT_DIR=$(pwd -P)
export CLAUDE_PROJECT_DIR
for dependency in git jq python3; do
  command -v "$dependency" >/dev/null || { echo "Dependência ausente: $dependency" >&2; exit 1; }
done
python3 -c 'import sys; assert sys.version_info >= (3, 9), "Python 3.9+ necessário"'
# .git também pode ser arquivo (worktree). Não confundir um repositório pai com este.
if [ ! -e .git ]; then git init -q; fi
bash scripts/sdd/install-git-hooks.sh
bash scripts/sdd/spec-lint-all.sh
bash scripts/sdd/spec-index.sh
bash scripts/sdd/spec-drift.sh
mkdir -p .sdd
[ -e .sdd/active-spec ] || : > .sdd/active-spec
printf '%s\n' 'Setup pronto. Abra a sessão na raiz. Produto → stack por ADR-002 → F-SETUP → features.'
