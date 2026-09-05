#!/usr/bin/env bash
# SessionStart: injeta estado SDD no contexto (stdout vira contexto do Claude).
command -v jq >/dev/null || { echo "## Estado SDD"; echo "- JQ AUSENTE: enforcement SDD desligado. Instale jq (brew install jq / apt install jq) e reabra a sessão."; exit 0; }
source "$(dirname "$0")/../../scripts/sdd/_lib.sh"
id=$(active_spec)
echo "## Estado SDD"
if [ ! -f "$INDEX" ] || [ ! -d "$ROOT/.git" ] || [ ! -x "$ROOT/.git/hooks/commit-msg" ]; then
  echo "- SETUP PENDENTE: rode agora 'bash scripts/setup.sh' (git init, hooks, índice, commit inicial) antes de qualquer outra ação."
fi
if grep -q '^title: Produto a definir' "$SPECS/product/product-spec.md" 2>/dev/null; then
  echo "- BOOTSTRAP PENDENTE: produto e stack ainda não definidos. Ao receber o case, execute o Playbook Bootstrap do CLAUDE.md (B1 → B5): product-spec → G0 → ADR-002 stack → G2 → F-SETUP-V1 → G1 → esqueleto → semente DS-00/06/07 → postmortem."
fi
if [ -n "$id" ]; then
  spec=$(ls "$SPECS"/features/"$id"/spec.md "$SPECS"/components/"$id"/spec.md 2>/dev/null | head -1)
  if [ -z "$spec" ]; then
    echo "- Feature ativa: $id SEM spec em .specs/features|components — corrija .sdd/active-spec (o guard nega código)."
  else
    echo "- Feature ativa: $id ($(fm "$spec" status) v$(fm "$spec" version)) → ${spec#$ROOT/}"
    echo "- ACs: $(grep -cE '^- \*\*AC-' "$spec" 2>/dev/null) · NEEDS_CLARIFICATION: $(awk '/^## NEEDS_CLARIFICATION/{f=1;next} /^## /{f=0} f' "$spec" | grep -vE '^[[:space:]]*$|^- ?(nenhum|none)' | wc -l | tr -d ' ') aberto(s)"
  fi
else
  echo "- Feature ativa: NENHUMA. Arquivos de código estão bloqueados. Ao receber uma demanda, siga o fluxo do CLAUDE.md: /spec-new → G1 → ADR? → TDD por AC → spec-reviewer → /postmortem."
fi
echo "- Drift: $(bash "$ROOT/scripts/sdd/spec-drift.sh" 2>&1 | tail -1)"
ds=$(ls "$SPECS"/design-system/ 2>/dev/null | grep -c '^DS-' || true)
echo "- Contagens: $(ls -d "$SPECS"/features/F-* 2>/dev/null | wc -l | tr -d ' ') features · $(ls "$SPECS"/adr/ 2>/dev/null | grep -E "^ADR-[0-9]{3}-" | grep -vc "^ADR-000-template") ADRs · $ds design-system · $(ls "$SPECS"/postmortems/PM-* 2>/dev/null | wc -l | tr -d ' ') postmortems"
if [ "$ds" -eq 0 ] && [ -d "$SPECS/features/F-SETUP-V1" ]; then echo "- DESIGN SYSTEM AUSENTE com F-SETUP existente: semente DS-00/06/07 pendente (CLAUDE.md B4b, Regra 13)."; fi
if [ "$ds" -gt 0 ]; then echo "- Design System: $(ls "$SPECS"/design-system/ | grep '^DS-' | sed 's/\.md$//' | tr '\n' ' ')— leia o aplicável antes de criar módulo/teste/nome/erro novo (Regra 13)."; fi
echo "- Releia AGENTS.md Regra 12 antes de começar."
exit 0
