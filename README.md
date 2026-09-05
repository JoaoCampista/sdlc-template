# Template spec-driven para Claude Code (CEIA)

Repositório vazio de código, cheio de método: o `ai-4sdlc-platform` (CEIA/UFG) portado para qualquer linguagem.
**Spec antes de código, ADR para decisão, postmortem no fechamento, hooks que obrigam.** A stack é a primeira
decisão registrada (ADR-002), não uma premissa do template.

## Começar
```bash
claude   # só isso. O CLAUDE.md manda o Claude rodar `bash scripts/setup.sh` (git init, hooks, índice, commit inicial; requer jq)
```
Descreva o case em linguagem de produto. O CLAUDE.md conduz:

**Bootstrap** — product-spec → **G0 você aprova o produto** → ADR-002 (stack, ≥2 alternativas) → **G2 você aceita** →
Constitution §2 atualizada → F-SETUP-V1 (esqueleto + 1 teste verde + lint) → **G1 você aprova** → código liberado →
semente do Design System (DS-00 arquitetura/fronteiras, DS-06 testes, DS-07 nomes, cada regra com enforcement) →
postmortem do setup.

**Cada feature** — `/spec-new` (spec/plan/tasks/risks) → **G1** → `/adr-new` se houver decisão → **G2** → TDD por AC
com commits `Spec-Hash` → `spec-reviewer` → validação → `/postmortem` com “Spec gap identificado” → resumo.

Diga “siga sem parar” para pré-aprovar os gates.

## Estrutura
```
CLAUDE.md                 contexto: bootstrap, fluxo da feature, playbooks, regras duras
AGENTS.md                 a lei: Regras 0–13, anti-padrões
.specs/
  constitution/           princípios não-negociáveis, §2 stack (preenchida por ADR-002), regras computáveis, emendas
  product/                PROD-001 (esqueleto; preenchido no bootstrap)
  features/_TEMPLATE/     spec.md · plan.md · tasks.md · risks.md
  components/_TEMPLATE/   spec.md · plan.md · risks.md
  design-system/          meta-camada: COMO se escreve código aqui (DS-00 arquitetura · DS-06 testes · DS-07 nomes · DS-05 erros…); semente no F-SETUP, cresce por gatilho; toda regra com enforcement
  adr/                    ADR-000-template · ADR-001-adotar-sdd
  postmortems/_TEMPLATE.md
  index.json              gerado por scripts/sdd/spec-index.sh (hash de cada spec)
.claude/
  settings.json           hooks: SessionStart · PreToolUse (nega código sem spec) · PostToolUse (lint + index) · Stop
  rules/                  specs.md · adr.md · design-system.md · tests.md (carregam por caminho)
  skills/                 /spec-new · /adr-new · /ds-new · /postmortem · /sdd-reconcile · /sdd-status
  agents/spec-reviewer.md revisor adversarial: diff × ACs × ADRs
.sdd/active-spec          feature ativa (estado de sessão; lida pelos hooks; não versionado)
scripts/sdd/              spec-index · spec-drift · spec-lint · spec-lint-all · install-git-hooks + git hooks (Conventional Commits, trailer Spec-Hash)
```
Escape consciente para mudança trivial já coberta: `SDD_ALLOW_TRIVIAL=1` (fica no histórico do shell).
