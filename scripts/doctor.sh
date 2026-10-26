#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
CLAUDE_PROJECT_DIR=$(pwd -P)
export CLAUDE_PROJECT_DIR
for tool in bash git jq python3; do
  command -v "$tool" >/dev/null || { echo "Falta: $tool" >&2; exit 1; }
done
python3 -c 'import sys; assert sys.version_info >= (3, 9), "Python 3.9+ necessário"'
[ -e .git ] || { echo 'Setup pendente: sem .git local' >&2; exit 1; }
if git config --get core.hooksPath >/dev/null; then
  echo 'core.hooksPath personalizado: confira a integração dos hooks SDD' >&2; exit 1
fi
hooks=$(git rev-parse --git-path hooks)
for hook in pre-commit prepare-commit-msg commit-msg pre-push; do
  [ -x "$hooks/$hook" ] && grep -q 'sdd-template managed hook' "$hooks/$hook" || { echo "Hook ausente/desatualizado: $hook" >&2; exit 1; }
done
bash scripts/sdd/spec-drift.sh
printf '%s\n' 'doctor: OK. Verifique o disparo na sessão real do cliente; este comando só confere instalação.'
