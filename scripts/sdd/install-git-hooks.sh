#!/usr/bin/env bash
# Instala os git hooks apontando para scripts/sdd (não copia — Regra 9). Rode uma vez por clone.
set -e; ROOT=$(git rev-parse --show-toplevel); H="$ROOT/.git/hooks"; mkdir -p "$H"
for pair in "commit-msg:git-commit-msg.sh" "prepare-commit-msg:git-prepare-commit-msg.sh" "pre-commit:git-pre-commit.sh" "pre-push:spec-drift.sh"; do
  hook=${pair%%:*}; script=${pair##*:}
  printf '#!/usr/bin/env bash\nR=$(git rev-parse --show-toplevel)\nexec bash "$R/scripts/sdd/%s" "$@"\n' "$script" > "$H/$hook"; chmod +x "$H/$hook"
done
chmod +x "$ROOT"/scripts/sdd/*.sh "$ROOT"/.claude/hooks/*.sh 2>/dev/null || true
echo "git hooks instalados: commit-msg, prepare-commit-msg, pre-commit, pre-push"
