#!/usr/bin/env bash
# git hook commit-msg: Conventional Commits. Uso: git-commit-msg.sh <arquivo-da-mensagem>
first=$(grep -v '^#' "$1" | head -1)
echo "$first" | grep -Eq '^(Merge |Revert "|fixup!|squash!)' && exit 0
echo "$first" | grep -Eq '^(feat|fix|chore|docs|test|refactor|perf|build|ci|style|revert)(\([A-Za-z0-9,_-]+\))?!?: .+' && exit 0
echo "ERRO: mensagem fora do Conventional Commits: '$first'"; echo "formato: tipo(escopo): assunto — ex.: feat(feedback): POST /feedback (AC-1..3)"; exit 1
