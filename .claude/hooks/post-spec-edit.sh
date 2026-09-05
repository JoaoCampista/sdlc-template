#!/usr/bin/env bash
# PostToolUse (Edit|Write em .specs/**): lint imediato + rebuild do índice. Falha vira feedback para o Claude (exit 2).
source "$(dirname "$0")/../../scripts/sdd/_lib.sh"
command -v jq >/dev/null || { echo "jq ausente — lint SDD inoperante" >&2; exit 2; }
f=$(jq -r '.tool_input.file_path // empty'); case "${f#$ROOT/}" in .specs/*.md) ;; *) exit 0;; esac
out=$(bash "$ROOT/scripts/sdd/spec-lint.sh" "$f" 2>&1) || { echo "$out" >&2; exit 2; }
bash "$ROOT/scripts/sdd/spec-index.sh" >/dev/null 2>&1 || true
exit 0
