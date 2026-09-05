# .specs/ — a fonte da verdade

Hierarquia (Constitution §13): `constitution/` → `product/` → `features/F-*/` e `components/C-*/`; `design-system/DS-0N-*`
(meta-camada, parent CONST-001). ADRs em `adr/` (transversais, via `related_adrs`). Postmortems em `postmortems/` (fora do índice: forense ≠ contrato).

| Pasta | Arquivos | `kind` | Status válidos |
|---|---|---|---|
| `features/F-<DOMINIO>-V<N>/` | `spec.md plan.md tasks.md risks.md` | `feature_spec` | draft → in_review → approved → deprecated |
| `components/C-<NOME>/` | `spec.md plan.md risks.md` (sem tasks) | `component_spec` | idem |
| `adr/ADR-NNN-slug.md` | 1 arquivo; reversão = `ADR-NNN-v2-slug.md` | `adr` | in_review → accepted → superseded |
| `design-system/DS-0N-slug.md` | 1 arquivo; semente DS-00/06/07 no F-SETUP | `design_system_spec` | draft → in_review → approved |
| `postmortems/PM-<escopo>-<YYYY-MM-DD>.md` | 1 arquivo | `postmortem` | draft → approved → corrected |

Regras computáveis (lint `scripts/sdd/spec-lint.sh`):
R1 frontmatter obrigatório (`id kind title parent version status last_updated`) ·
R2 seções literais — F-/C-: `## WHAT/HOW`, `## User Stories`, `## Acceptance Criteria`, `## NFRs`, `## NEEDS_CLARIFICATION`; ADR: Contexto/Decisão/Consequências/Alternativas consideradas/Riscos/Fences contra regressão/Revisões; DS: Escopo/Regras/Enforcement (uma linha por regra)/Exemplos canônicos/Anti-padrões/Changelog; postmortem: §1–§7 ·
R3 ≥1 AC no formato `- **AC-N.** … @test:<path>` ·
R4 sem `NEEDS_CLARIFICATION` aberto quando `status: approved` ·
R5 `@test:` aponta para arquivo existente (aviso em draft/in_review, erro em approved).

Fluxo: copie `_TEMPLATE`, renomeie, preencha, `scripts/sdd/spec-lint.sh <spec>`, `scripts/sdd/spec-index.sh`, gate G1 (humano aprova),
`status: in_review`, `echo F-ID > .sdd/active-spec`, só então código. `spec_hash: pending` no frontmatter é placeholder — o índice é a verdade; `risk_tier` é informativo.

Playbooks detalhados: ver `CLAUDE.md` (tabela) e as skills `/spec-new`, `/adr-new`, `/ds-new`, `/postmortem`, `/sdd-reconcile`, `/sdd-status`.
