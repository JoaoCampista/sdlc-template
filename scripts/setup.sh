#!/usr/bin/env bash
# Prepara o template: git, hooks, índice de specs. Rode uma vez após clonar/copiar. Independe de linguagem.
set -e; cd "$(dirname "$0")/.."
command -v jq >/dev/null || { echo "instale o jq (brew install jq / apt install jq) — os hooks dependem dele"; exit 1; }
[ -d .git ] || git init -q
chmod +x scripts/sdd/*.sh .claude/hooks/*.sh scripts/setup.sh
bash scripts/sdd/install-git-hooks.sh
bash scripts/sdd/spec-index.sh && bash scripts/sdd/spec-drift.sh && bash scripts/sdd/spec-lint-all.sh
mkdir -p .sdd && : > .sdd/active-spec
# commit inicial: único lugar onde `git add -A` é aceitável (Regra 10 vale para o agente, por caminho)
if [ -z "$(git log --oneline 2>/dev/null)" ]; then git add -A . && git commit -q -m "chore: template spec-driven (CLAUDE.md, AGENTS.md, .specs, hooks)" && echo "commit inicial criado"; fi
echo; echo "pronto. abra 'claude' e descreva o case. O Playbook Bootstrap do CLAUDE.md faz o resto (produto → stack por ADR → F-SETUP → features → postmortem)."
