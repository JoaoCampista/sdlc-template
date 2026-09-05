#!/usr/bin/env bash
# git hook pre-commit: lint das specs staged + drift. Nunca `--no-verify` sem registrar no postmortem (Regra 9).
source "$(dirname "$0")/_lib.sh"
staged=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^\.specs/.*\.md$' || true)
if [ -n "$staged" ]; then bash "$ROOT/scripts/sdd/spec-lint.sh" $staged || exit 1; fi
bash "$ROOT/scripts/sdd/spec-drift.sh" || { echo "→ rode scripts/sdd/spec-index.sh e faça 'git add .specs/index.json'"; exit 1; }
