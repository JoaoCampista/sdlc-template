---
name: postmortem
description: Escreve um postmortem canônico (7 seções, frontmatter, fora do índice) em .specs/postmortems. Use ao fechar uma feature, após incidente/bug em produção, smoke real, refresh de dependências ou reconciliação — ou quando o usuário disser "registra o que aconteceu".
argument-hint: "<escopo> <feature-close|incident|smoke|refresh|reconciliation>"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git log *), Bash(git diff *), Bash(ls *), Bash(date *), Bash(scripts/sdd/*)
---
## Contexto
Commits recentes: !`git log --oneline -15`
Hoje: !`date +%Y-%m-%d`

## Procedimento para: $ARGUMENTS
1. Copie `.specs/postmortems/_TEMPLATE.md` para `PM-<escopo>-<YYYY-MM-DD>.md`. `index: false` (forense ≠ contrato): o índice ignora postmortems; rode `scripts/sdd/spec-lint.sh` no arquivo.
2. §1 TL;DR em 3 linhas (+ Timeline se incident/smoke). §2 o que funcionou. §3 cada problema com Sintoma / Root cause / Evidência (path) / Fix / Impacto / Detecção.
3. §4 métricas com baseline e delta reais (recalcule; não copie). §5 lições — cada uma com fix concreto: ADR, Regra em AGENTS.md ou hook. Inclua **Spec gap identificado** (e o PR de spec) e **Convenção descoberta** (algo que “sempre fazemos” sem DS → `/ds-new`, ou “nenhuma”); sem isto o loop SDD não fecha.
4. §6 pendências com owner e prazo, ou `nenhuma` explícito. §7 paths de evidência — **confirme que existem antes de escrever**.
5. Se houve “burrice” nova, adicione uma linha na tabela de anti-padrões de `AGENTS.md`; padrão bom ganha `✓ POSITIVO`.
6. Commit: `docs(postmortem): <id> — <kind> (<data>)`.
