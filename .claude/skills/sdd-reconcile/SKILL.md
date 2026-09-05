---
name: sdd-reconcile
description: Reconciliação SDD retroativa (linha “Código sem spec / drift” dos playbooks) — quando há código sem spec, spec desatualizada, drift, ou o gatilho "3+ commits sem tocar .specs" disparou. Use para "reconciliar specs", "o código mudou e a spec não", "cobrir código legado".
argument-hint: "[F-ID ou 'global']"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(scripts/sdd/*), Bash(git log *), Bash(git diff *), Bash(git status *), Bash(git add *), Bash(git commit *), Bash(ls *), Bash(tail *)
---
## Contexto
Drift atual: !`scripts/sdd/spec-drift.sh 2>&1 | tail -5`
Últimos commits: !`git log --oneline -20`

## Procedimento para: $ARGUMENTS
1. **Cânone derivado do CÓDIGO primeiro.** Antes de editar qualquer `.md`, monte o mapa de verdade: módulos, rotas/contratos reais, testes existentes, o que foi removido (lápides). Não confie na spec antiga.
2. **Cobertura:** para cada módulo/comportamento, qual spec cobre? Nenhuma → decida granularidade (Feature vs Component; 1 Component por subsistema com ciclo próprio) e crie via `/spec-new`, em `draft`.
3. **Passada mecânica** (paths, ids, `@test:`) separada da **passada de conteúdo** (ACs, riscos). Nunca as duas no mesmo commit.
4. **Verificação adversarial:** invoque o subagente `spec-reviewer` (passando o ID ou “global”) para comparar spec × código × testes. Quem reconcilia não verifica o próprio trabalho.
5. Validação nesta ordem: `spec-index.sh` → `spec-drift.sh` → `spec-lint-all.sh` → testes → typecheck → build → lint.
6. Commits em lotes: `docs(specs): <ID> vX.Y.Z reconciliação Lote N` listando spec→versão, tasks, risks, hash bumps. Nunca “um PR gigante”.
7. Feche com `/postmortem <escopo> reconciliation` e recomende a mudança de hábito que vira Regra em AGENTS.md.
