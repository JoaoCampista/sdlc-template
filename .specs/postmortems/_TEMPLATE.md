---
id: PM-<escopo>-<YYYY-MM-DD>
kind: postmortem
title: <Título>
parent: F-<DOMINIO>-V1
version: 1.0.0
status: draft
risk_tier: limited
owners: [<nome>]
related_adrs: []
last_updated: <YYYY-MM-DD>
index: false
---

# PM — <Título>
kind: **feature-close | incident | smoke | refresh | reconciliation**

## §1. Objetivo
TL;DR em 3 linhas. `Timeline` (hh:mm → evento) se incident/smoke.

## §2. Funcionou ✅
## §3. Deu errado ⚠️
### Bug 1 — <nome>
- Sintoma · Root cause · Evidência (path) · Fix (commit/ADR) · Impacto · Detecção (como/quando)

## §4. Métricas
| Métrica | Baseline | Medido | Delta |
|---|---|---|---|

## §5. Lições
1. <lição> → fix concreto: <ADR-NNN | Regra N em AGENTS.md | hook>
- **Spec gap identificado:** <qual AC/spec faltava ou estava errada> → PR de spec: <link>
- **Convenção descoberta:** <padrão que “sempre fazemos” e não está em DS → /ds-new DS-0N> | nenhuma

## §6. Pendências (declare `nenhuma` explicitamente se for o caso)
| Pendência | Tipo (prevent/mitigate/process) | Owner | Prazo | Tracking | Status |
|---|---|---|---|---|---|

## §7. Evidências (paths reproduzíveis — confirme que existem antes de escrever)
- <path>
