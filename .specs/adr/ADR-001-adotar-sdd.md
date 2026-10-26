---
id: ADR-001
kind: adr
title: Adotar desenvolvimento dirigido por especificação (SDD) com enforcement por hooks
parent: PROD-001
version: 1.1.0
status: accepted
date: 2026-09-05
deciders: [ceia]
related: [CONST-001]
supersedes: []
amends: []
last_updated: 2026-10-26
---

# ADR-001 — Adotar SDD com enforcement por hooks

## Contexto
Agentes de código tornam o código barato e o julgamento caro. Sem contrato explícito, a intenção se perde
(dívida de intenção), o entendimento se perde (dívida cognitiva) e a velocidade vira dívida técnica.
Método herdado do `ai-4sdlc-platform` (CEIA/UFG).

## Decisão
`.specs/` é a fonte da verdade. Toda mudança não-trivial nasce em spec; decisões arquiteturais nascem em ADR;
fechamentos e incidentes geram postmortem. O enforcement é determinístico: hook do Claude Code bloqueia edição de
código sem spec ativa; git hooks validam Conventional Commits e anexam `Spec-Hash`; `spec-drift` roda em
pre-commit/pre-push/CI.

## Consequências
- Positivas: rastreabilidade, revisão focada em ACs, onboarding pelo repositório, base para auditoria.
- Negativas: atrito inicial; specs podem inflar (mitigação: lint R1–R5, Regra 7 contra ADR-ticket).

## Alternativas consideradas
- Só CLAUDE.md com "por favor escreva specs" — rejeitada: contexto não é enforcement.
- Spec-as-source (código 100% gerado da spec) — rejeitada por ora: exige tooling que não temos.

## Riscos
- Time contornar com `--no-verify` — mitigação: auditoria em postmortem (Regra 9).

## Fences contra regressão
`scripts/sdd/spec-drift.sh` no CI; hook `PreToolUse` em `.claude/settings.json`.

## Revisões
- 2026-10-26: evolução solicitada pelo mantenedor. Python 3.9+ (biblioteca padrão) passa a ser dependência do tooling, não da stack do produto. Hash e validação usam o snapshot do Git; índice determinístico; guards testados e conservadores. Alternativas: transplantar o guard específico (rejeitado: acoplamento ao produto); manter parsing complexo só em shell (rejeitado: custo de caminhos/JSON). Custo aceito: instalar Python além de Git/jq. Limites e contratos em docs/hooks.md; regressões em scripts/tests/.
