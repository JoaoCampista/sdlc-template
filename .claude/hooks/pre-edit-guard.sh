#!/usr/bin/env bash
# PreToolUse (Edit|Write|MultiEdit): bloqueia edição de CÓDIGO sem spec ativa válida. Specs/docs/config do harness passam.
# Constitution §1.1 — spec antes de código. Escape consciente: SDD_ALLOW_TRIVIAL=1 (auditado: fica no shell history).
source "$(dirname "$0")/../../scripts/sdd/_lib.sh"
command -v jq >/dev/null || { echo "jq ausente — guard SDD inoperante; instale jq (brew install jq) antes de editar código" >&2; exit 2; }
input=$(cat); f=$(echo "$input" | jq -r '.tool_input.file_path // empty'); [ -z "$f" ] && exit 0
rel="${f#$ROOT/}"
[ "$rel" = ".specs/index.json" ] && { jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:".specs/index.json é gerado — rode scripts/sdd/spec-index.sh (escritor único)."}}'; exit 0; }
case "$rel" in
  .specs/*|.sdd/*|.claude/*|scripts/sdd/*|CLAUDE.md|AGENTS.md|README.md|CONTRIBUTING.md|docs/*|*.md|.gitignore|.github/*) exit 0;;
esac
[ "${SDD_ALLOW_TRIVIAL:-0}" = "1" ] && exit 0
id=$(active_spec)
deny() { jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
[ -z "$id" ] && deny "Spec antes de código (Constitution §1.1): não há feature ativa em .sdd/active-spec. Crie a spec (/spec-new) ou aponte uma existente: echo F-ID > .sdd/active-spec. Para mudança trivial já coberta por spec, o humano pode exportar SDD_ALLOW_TRIVIAL=1."
spec=$(ls "$SPECS"/features/"$id"/spec.md "$SPECS"/components/"$id"/spec.md 2>/dev/null | head -1)
[ -z "$spec" ] && deny "Feature ativa '$id' não tem spec em .specs/features/$id/spec.md. Crie-a antes de editar código."
st=$(fm "$spec" status)
case "$st" in draft) deny "Spec $id está em 'draft'. Só após o gate G1 (humano aprova a spec) ela vai para in_review — e só então código.";; esac
exit 0
