# CLAUDE.md — repositório spec-driven (template CEIA)

> `.specs/` é a fonte da verdade; código é derivado; auditoria é subproduto. Método do `ai-4sdlc-platform` (CEIA/UFG).
> Este arquivo é contexto; `AGENTS.md` é a lei; os hooks em `.claude/settings.json` e `scripts/sdd/` são o enforcement.
> Linguagem e stack NÃO estão decididas: são a primeira decisão registrada (ADR-002) quando o produto for definido.

## Passo 0 — setup do repositório (faça antes de qualquer outra coisa)

Se faltar `.specs/index.json`, `.git/` ou `.git/hooks/commit-msg`, o setup ainda não rodou. Execute, sem perguntar:

```bash
bash scripts/setup.sh
```

Ele faz `git init`, dá permissão de execução aos scripts e hooks, instala os git hooks (Conventional Commits + trailer
`Spec-Hash`), gera o índice de specs, verifica drift e lint e cria o commit inicial. Se acusar falta de `jq`, proponha
`brew install jq` / `apt install jq`, rode após a confirmação do usuário e repita o setup. Só depois continue a leitura abaixo.

## Ordem de leitura (toda sessão)

1. Este arquivo. 2. `AGENTS.md` (Regras 0–13). 3. `.specs/constitution/constitution.md`. 4. `.specs/product/product-spec.md`.
5. `.specs/design-system/` — **obrigatório antes de criar módulo, pasta, handler, teste, nome ou contrato de erro novo** (DS-00 arquitetura · DS-06 testes · DS-07 nomes · DS-05 erros · DS-0N do padrão).
6. Se houver feature ativa (`.sdd/active-spec`): `.specs/features/<F-ID>/{spec,plan,tasks,risks}.md`.
O hook `SessionStart` imprime o estado (bootstrap pendente? feature ativa? drift?). Leia antes de agir.

## Comandos

- Specs: `scripts/sdd/spec-lint.sh <arquivo>` · `scripts/sdd/spec-lint-all.sh` · `scripts/sdd/spec-index.sh` (após QUALQUER edição em `.specs/`; escritor único de `index.json`) · `scripts/sdd/spec-drift.sh` · `/sdd-status`
- Projeto (preencha no bootstrap, passo B4): testes `<a definir>` · lint/format `<a definir>` · build `<a definir>` · dev `<a definir>`

## Playbook Bootstrap — quando o repositório ainda não tem produto nem código

Dispara quando `product-spec.md` está em `draft` com título “a definir” ou quando não existe código. Ao receber o case:

- **B1 Entender o case.** Faça no máximo 3 perguntas, uma por vez, só se mudarem o desenho (quem usa, o que fica fora, dado sensível?). O resto, infira e registre como premissa.
- **B2 Product Spec.** Preencha `.specs/product/product-spec.md` (visão, públicos/JTBD, pilares, princípios, métricas, roadmap com as F-* previstas, não-objetivos). bump para 0.1.0. **G0:** mostre o resumo e pergunte “aprova o produto?”. Aprovado → `status: in_review` (+ `status_history`).
- **B3 Stack por ADR.** `/adr-new ADR-002 — stack do projeto`: linguagem/runtime, framework, persistência, testes/lint, com ≥2 alternativas e o que se perde. **G2:** aceite. Aceita → atualize a tabela §2 da Constitution (bump `minor` 1.0.0 → 1.1.0, `status_history`, `## Changelog`) e o §5 do product-spec (arquitetura).
- **B4 F-SETUP-V1.** `/spec-new F-SETUP-V1` — spec do esqueleto: estrutura de pastas e fronteiras entre elas, runner de testes com 1 teste “hello” verde, lint/format, comando de dev, `.gitignore`, workflow de CI mínimo (testes + `scripts/sdd/spec-drift.sh`), **e a semente do Design System como ACs** (“DS-00/06/07 existem, passam no lint e cada regra tem enforcement executável”). **G1:** aprove → `status: in_review` → `echo F-SETUP-V1 > .sdd/active-spec`. Só então crie arquivos de código (o hook libera). Preencha a seção **Comandos** deste CLAUDE.md e adicione `## Layout do código`. Se a stack tiver formatador/testes, proponha hooks `PostToolUse` (format) e `Stop` (testes) em `.claude/settings.json`.
- **B4b Semente do Design System.** Com o esqueleto pronto, `/ds-new` três vezes, descrevendo o que o esqueleto JÁ faz: `DS-00-architecture` (pastas, camadas, quem pode importar quem — com a regra de fronteira executável: eslint boundaries / dependency-cruiser / import-linter), `DS-06-tests` (co-location ou pasta, naming, hermético, comando), `DS-07-naming` (arquivos, identificadores, commits). Cada regra com linha em `## Enforcement`; contagens com ratchet test. ≤ 60 linhas cada. Não invente convenção para o que ainda não existe.
- **B5 Fechar o setup.** Validação (testes, lint, `spec-lint-all`, `spec-index`, `spec-drift`), commit `feat(setup): F-SETUP-V1 — esqueleto <stack>` e um commit por DS (`docs(ds): DS-00 — arquitetura (+ fence)`, idem 06 e 07), `/postmortem F-SETUP-V1 feature-close` (curto). Limpe `.sdd/active-spec`. Siga para a primeira feature do roadmap com o fluxo abaixo.

## Fluxo de uma feature — obrigatório, de ponta a ponta

Só as paradas marcadas com **G** exigem minha palavra (Constitution §1.2). Se eu disser “siga sem parar” ou “pré-aprovado”, trate todos os gates como aprovados e vá até o postmortem.

1. **Entender.** Releia product-spec e specs existentes. ≤3 perguntas, uma por vez, só se mudarem o desenho.
2. **Spec antes de código.** `/spec-new F-<DOMINIO>-V1`: `spec.md` (WHAT/HOW, User Stories, ACs `- **AC-N.** … @test:<path>`, NFRs, NEEDS_CLARIFICATION), `plan.md`, `tasks.md` (toda task → 1+ AC), `risks.md` (≥3). Sem placeholders. `spec-lint.sh` OK → `spec-index.sh`. **G1:** resumo (ACs + riscos + premissas) e “aprova a spec?”. Aprovada → `status: in_review`, `echo F-ID > .sdd/active-spec`, commit `feat(specs): F-ID v0.1.0 — <título>`.
3. **Decidir por escrito.** Novo modelo/entidade persistida, novo endpoint/contrato público de escrita, nova dependência, integração externa, regra de negócio/agregação não óbvia, ou qualquer mudança em §2 da Constitution → `/adr-new` ANTES do código (Contexto, Decisão, Consequências com o que se perde, ≥2 alternativas, Riscos, Fences, Revisões). **G2:** aceite → `status: accepted`, `related_adrs` na spec, commit `docs(adr): ADR-NNN — <título>`. Sem decisão nova → diga em uma linha (“sem ADR: coberto por ADR-002”) e siga.
3b. **Conferir o Design System.** Antes de escrever código, leia o DS aplicável (Regra 13) e diga em uma linha qual: “DS-00 §2 fronteiras, DS-06, DS-07”. A feature cria contrato de erro/API e não há DS-05? Crie-o agora (`/ds-new`). A feature introduz a **2ª ocorrência** de um padrão (2º handler, 2º módulo do mesmo tipo, 2º evento)? Codifique o padrão em `DS-0N` com enforcement, doc e fence no mesmo commit. Precisa desviar de um DS? Não edite o DS: ADR (passo 3).
4. **Implementar por AC, com TDD.** Para cada AC: teste no `@test:` declarado → rode e confirme que falha pelo motivo certo → implemente o mínimo → verde → formate. Nunca altere um teste para passar. Marque a task (✅) em `tasks.md`. Commit por AC ou grupo coeso: `feat(<escopo>): <o quê> (AC-N..M)`.
5. **Revisar adversarialmente.** Subagente `spec-reviewer` sobre o diff. Corrija alta/média. Divergência da spec → corrija a spec primeiro (bump `version`, `status_history`).
6. **Validar antes de declarar done.** Testes · lint · build · `spec-lint-all.sh` · `spec-index.sh` · `spec-drift.sh`. Recalcule; não copie números. `git add` por caminho (nunca `-A`); `git add .specs/index.json` explicitamente.
7. **Fechar com postmortem.** `/postmortem F-ID feature-close`: 7 seções; §5 com lições e **“Spec gap identificado”** (o que a spec não previu — ou “nenhum” justificado) e **“Convenção descoberta”** (algo que “sempre fazemos” e não está em DS → `/ds-new`, ou “nenhuma”); §6 pendências com dono ou `nenhuma`; §7 paths que existem. Commit `docs(postmortem): <PM-id> — feature-close (<data>)`.
8. **Encerrar.** Limpe `.sdd/active-spec`. Proponha promover a spec a `approved` (só eu promovo). Resuma em 5 linhas: artefatos, ACs verdes, ADRs, pendências.

Gatilho duro (AGENTS.md 12.1): **3+ commits no mesmo subsistema em < 1h sem tocar `.specs/`** = iteração sem SDD. Pare, 1 commit de código + 1 commit `docs(specs): F-ID vX.Y.Z reconciliação Lote N`, retome.

## Playbooks por tipo de tarefa

| Tarefa | Ordem |
|---|---|
| Repositório vazio / case novo | Playbook Bootstrap (B1 → B5), depois o fluxo de feature |
| Feature nova | fluxo 1 → 8 |
| Bug | achar a AC violada → teste que falha no `@test:` → fix → se a AC estava errada, corrigir a AC ANTES → `fix(<escopo>): <bug> (AC-N)` → postmortem `incident` com Spec gap |
| Refactor | contrato muda? spec antes. Só implementação? code-only. Commit `refactor(...)`, nunca `feat` |
| Componente interno com ciclo próprio | `C-<NOME>` com `parent:` F-*/C-*, `spec/plan/risks`, seção `## Evolução` |
| Convenção nova / padrão repetido / “sempre fazemos X” | `/ds-new`: descobrir no código → regra verificável → enforcement no mesmo commit → `docs(ds)`. Desvio de DS existente → ADR, nunca edição silenciosa |
| Código sem spec / drift | `/sdd-reconcile`: cânone derivado do código → specs → revisão adversarial por outro agente |
| Incidente | postmortem com Spec gap → PR de spec → depois o fix. Hotfix sem spec é violação retroativa |

## Quando o Design System é construído

O DS (`.specs/design-system/`) é a meta-camada: specs dizem O QUE, ADRs dizem POR QUE, o DS diz **COMO se escreve
código aqui**. Ele **não** nasce antes do código (seria doc-as-prompt) nem depois de 92 arquivos (folclore, o erro
que o ai-4sdlc-platform pagou no ADR-093). Nasce no **F-SETUP**, como semente que descreve o esqueleto recém-criado
(DS-00 arquitetura/fronteiras, DS-06 testes, DS-07 nomes), e cresce por gatilho: 1ª API/erro → DS-05; 2ª ocorrência
de um padrão → DS-0N do padrão; lição de postmortem que é convenção → extensão. Toda regra com enforcement
executável; contagens com ratchet. Snapshot do que existe, normativo dali em diante.

## Hierarquia (Constitution §13) — `parent:` obrigatório

```
CONST-001 → PROD-001 → F-<DOMINIO>-V<N> (spec/plan/tasks/risks) → C-<NOME> (spec/plan/risks)
DS-0N design-system (meta-camada, parent CONST-001) · ADR-NNN transversais (related_adrs) · PM-* fora do índice
```
Status: feature/component `draft → in_review → approved → deprecated`; ADR `in_review → accepted → superseded`; postmortem `draft → approved → corrected`. Nunca `approved` com `NEEDS_CLARIFICATION` aberto.

## Regras duras (violar só com ADR)

- Spec antes de código: o hook `PreToolUse` nega criar/editar qualquer arquivo fora de `.specs/`, `.sdd/`, `.claude/`, `scripts/sdd/`, `.github/`, `docs/`, `.gitignore` e `*.md` sem `.sdd/active-spec` apontando para spec fora de `draft`. `.specs/index.json` só via `spec-index.sh`. Não contorne com `echo >`/`cp` — é violação da Constitution §1.1.
- Humano decide o irreversível: produto (G0), spec (G1), ADR (G2), `approved`, deleção, merge.
- ADR é decisão, não ticket. Extensão → `## Revisões` no ADR original; reversão → `ADR-NNN-v2` com `supersedes`.
- Design System é lei para código novo (Regra 13): regra sem enforcement não se escreve; desvio exige ADR; DS descreve o que existe.
- Não suprima; resolva: sem `skip`, `eslint-disable`/`# noqa`/`biome-ignore`, `|| true`, `--no-verify`, `"off"` sem razão de domínio.
- Não envelope SDKs maduras; função pura > classe; módulo/package novo só com ciclo de release próprio.
- Testes hermeticos (sem rede, sem banco real; em memória ou fixture). Erros de API em formato único documentado na spec.
- Lápides: o que morreu fica registrado onde viveu (`**Lápide YYYY-MM-DD:** …`), nunca apagado em silêncio.
- Contagens sempre derivadas (`ls -d .specs/features/F-* | wc -l`); nunca fixadas em documento.
- Pedido meu que viole um invariante → recuse dizendo qual e ofereça alternativa. Não escolha em silêncio.

## Pegadinhas

- Hooks exigem `jq` e `$CLAUDE_PROJECT_DIR`. Se o `SessionStart` acusar “JQ AUSENTE” ou não imprimir nada (erro de hook), o enforcement está desligado — pare, avise o usuário e resolva antes de qualquer edição.
- Placeholders `<…>` em `.specs/` são rejeitados pelo lint — preencha antes de commitar.
