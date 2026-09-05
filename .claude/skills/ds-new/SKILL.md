---
name: ds-new
description: Cria ou estende um doc do Design System (.specs/design-system/DS-0N-*.md) — arquitetura e fronteiras, testes, nomes, erros, padrões canônicos — sempre com enforcement executável. Use no F-SETUP (semente DS-00/06/07), quando um padrão aparece pela 2ª vez, quando uma revisão diz "aqui sempre fazemos X", ou quando uma lição de postmortem é uma convenção.
argument-hint: "<DS-0N-slug | 'estender DS-0N'> [tema]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(scripts/sdd/*), Bash(ls *), Bash(date *), Bash(git log *), Bash(grep *), Bash(sort *)
---
## Contexto
DS existentes: !`ls .specs/design-system 2>/dev/null | grep -E '^DS-' || echo "(nenhum — semente pendente)"`
Hoje: !`date +%Y-%m-%d`

## Procedimento para: $ARGUMENTS
1. **Descubra antes de escrever.** Leia o código real (`ls`, `grep`): o DS é snapshot do que existe, normativo dali em diante. Não invente convenção para código que ainda não existe (Regra 13). Se o tema ainda não tem 2 ocorrências no repo, diga isso e pare — cedo demais. **Exceção:** a semente DS-00/06/07 no F-SETUP descreve o esqueleto recém-criado (1 módulo, 1 teste) e é obrigatória.
2. Existe DS para o tema? **Estender**: adicione a regra numerada, a linha de Enforcement, bump `version` (minor), `last_updated`, `## Changelog`. **Criar**: copie `.specs/design-system/_TEMPLATE.md` → `DS-0N-<slug>.md`, preencha sem placeholders. Números reservados: 00 arquitetura · 05 erros · 06 testes · 07 nomes; padrões do projeto usam 01–04 e 08+.
3. Cada regra em **uma frase verificável** + **uma linha em Enforcement** apontando lint, regra de fronteira (eslint boundaries / dependency-cruiser / import-linter), hook ou teste. Sem enforcement possível? Escreva o teste ratchet (ex.: teste que varre a árvore e afirma a contagem/forma, citando o DS na mensagem de falha). O enforcement (config de lint, regra de fronteira, teste ratchet) entra no MESMO commit que o doc — precisa de feature ativa em `.sdd/active-spec`.
4. `## Exemplos canônicos` com path:linha reais; `## Anti-padrões` com o que já deu errado (postmortems).
5. `related_adrs` com a ADR que motivou (ADR-002 stack, ou a decisão específica). Desvio de DS existente não se resolve editando o DS: exige ADR.
6. `scripts/sdd/spec-lint.sh <doc>` → `scripts/sdd/spec-index.sh`. Um único commit com doc + fence: `docs(ds): DS-0N — <tema> (+ fence)`.
7. Se for um tipo de trabalho novo, adicione uma linha à tabela “Leitura obrigatória por tipo de trabalho” em `.specs/design-system/README.md`.
