# .specs/design-system/ — a meta-camada: COMO se constrói aqui

Specs dizem O QUE o sistema faz; ADRs dizem POR QUE decidimos; o **Design System (DS)** diz **COMO se escreve
código neste repositório**: fronteiras de módulos e regras de dependência, padrões canônicos (como se cria um
módulo/handler/agente), convenções de teste, de nomes, de erros. É normativo (AGENTS.md Regra 13): código novo
que desobedece é rejeitado; desviar exige ADR.

Lição do ai-4sdlc-platform (ADR-093): o DS nasceu tarde, quando já havia 92 arquivos e toda convenção era
folclore que se aprendia por grep. Aqui ele nasce **junto com o esqueleto** (F-SETUP) e cresce por demanda.

## Quando criar e quando estender

| Momento | O que fazer |
|---|---|
| F-SETUP (bootstrap) | Semente obrigatória: `DS-00` arquitetura e fronteiras · `DS-06` testes · `DS-07` nomes. Curtos (≤ 60 linhas cada), descrevendo o que o esqueleto JÁ faz. |
| Primeira feature com contrato de erro/API | `DS-05` erros (formato único, quando lançar × retornar, o que nunca engolir). |
| 2ª ocorrência de um padrão (2º handler, 2º módulo do mesmo tipo, 2º evento) | Novo doc `DS-0N-<padrão>`: o padrão canônico + exemplo real do repo + anti-padrões. |
| Comentário de revisão “aqui a gente sempre faz X” · lição de postmortem que é convenção | Estender o DS existente (bump `version`, entrada no `## Changelog`). |
| Contagem que um DS afirma (N módulos, N eventos, N canais) | Trava por **ratchet test**: quando o número muda de propósito, o teste falha e diz qual DS atualizar. |

Regra de ouro: **DS é snapshot do que existe, normativo dali em diante.** Não invente convenção para código que
ainda não existe — descubra e codifique. E **regra DS sem enforcement é folclore**: cada regra aponta o lint, a
regra de fronteira (dependency-cruiser / eslint boundaries / import-linter), o hook ou o teste que a cobra.

## Formato

Copie `_TEMPLATE.md` → `DS-0N-<slug>.md`. Frontmatter `kind: design_system_spec`, `parent: CONST-001`,
`related_adrs`. Seções obrigatórias (lint R2): `## Escopo`, `## Regras`, `## Enforcement`, `## Exemplos canônicos`,
`## Anti-padrões`, `## Changelog`. Entram no índice (`spec-index.sh`) e no drift como qualquer spec.

## Leitura obrigatória por tipo de trabalho (Regra 13)

| Trabalhando em | Leia antes |
|---|---|
| módulo, pasta, import entre camadas | DS-00 |
| teste | DS-06 |
| nome de arquivo/identificador/commit | DS-07 |
| erro, resposta de API, exceção | DS-05 |
| padrão que já tem doc | DS-0N correspondente |
