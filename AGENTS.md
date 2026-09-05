# AGENTS.md — a lei deste repositório

Leia este arquivo **antes** de criar um plano, antes de criar um package novo, antes de criar uma
interface “canônica”, antes de aceitar uma proposta sua mesmo. Regras nascem de incidentes reais;
cada uma tem (ou terá) um postmortem em `.specs/postmortems/`.

## Regra 0 — Stack fixa
A stack está em `.specs/constitution/constitution.md` §2. Não troque sem ADR aprovada e bump da Constitution.

## Regra 1 — Não envelope SDKs maduras
Antes de criar uma interface “canônica” sobre uma SDK, pergunte: a SDK já não é canônica? Se sim, use a SDK direta.
Mapeador bidirecional (`toX` + `fromX`) exige justificativa escrita em ADR. “Não quero acoplar” não é justificativa.

## Regra 2 — Teste lógica de negócio
Se 80% dos testes de um módulo são “passei X ao mapeador e saiu Y”, o módulo provavelmente não devia existir.

## Regra 3 — ADR auto-referencial é red flag
Se a justificativa do ADR é “o resto do código já depende disso”, verifique se depende porque o ADR mandou.
Se sim, o ADR é circular — revogue com `-v2` e postmortem.

## Regra 4 — Ouça o exemplo de 3 linhas
Quando alguém mostra que o problema se resolve em 3 linhas, não defenda a complexidade: registre o postmortem,
escreva o ADR de reversal, apague o código. Quanto mais cedo, mais barato.

## Regra 5 — Sem framework dentro do framework
Função pura > classe abstrata. Composição > herança. Package/módulo novo só se: (a) ciclo de release distinto,
ou (b) consumidor externo, ou (c) isola dependência pesada. Senão, escreva no módulo existente.

## Regra 6 — Aplicar SDD a si mesmo
Toda mudança não trivial:
1. Atualizar/criar spec em `.specs/features/F-*/` ou `.specs/components/C-*/` (spec antes do código).
2. Atualizar `plan.md` e `tasks.md` se mudar arquitetura; `risks.md` se mudar risco.
3. Criar ADR se mudar decisão arquitetural; reversões ganham `-v2`/`-v3` com `supersedes`.
4. Rodar `scripts/sdd/spec-index.sh` e commitar `.specs/index.json` junto.
5. Commit `tipo(escopo): assunto` (Conventional Commits). O hook adiciona `Spec-Hash:`.

## Regra 7 — ADR é decisão, não ticket
Antes de criar `.specs/adr/ADR-NNN-*.md`, pergunte: “é decisão arquitetural NOVA ou extensão/fix do ADR-YYY?”
Extensão → editar YYY adicionando `## Revisões` com data + delta. ADR novo só para: (1) decisão nova com
trade-offs distintos, (2) reversão completa (`-v2`), (3) nova área arquitetural.

## Regra 8 — Não suprimir; resolver
Quando uma regra de lint/tipo/teste/hook dispara, o caminho não é desligar a regra: é entender por que dispara
e refatorar. Proibido sem ADR ou comentário de domínio: `"rule": "off"`, `eslint-disable`/`biome-ignore`/`# noqa`
sem razão, `|| true`, `continue-on-error`, `--no-verify`, trocar `error` por `warn`. Suprimir verificação anula o
controle que existe para detectar débito.

## Regra 9 — Hooks de governança são ativos
`.claude/settings.json` (hooks do Claude Code) e `scripts/sdd/install-git-hooks.sh` (git). Nunca copie hooks à mão
para `.git/hooks/`. `--no-verify` é decisão do humano em emergência (nunca do agente — está em `permissions.deny`) e será auditado no próximo postmortem.

## Regra 10 — Commitar e empurrar frequentemente
Sandbox reseta; o remoto é a verdade. Um commit = uma coisa lógica. Stage por caminho; nunca `git add -A`.
Sub-agentes paralelos commitam só os arquivos que tocaram e verificam `git diff --cached --stat`.

## Regra 11 — Contagens vivas, nunca fixadas
Nenhum documento fixa “N features / N ADRs”. Derive com `ls`/`wc`. O único número fixável é o travado por teste (ratchet).

## Regra 12 — Regras de memória são gatilhos duros
Releia todas ao iniciar o trabalho.
- 12.1 **Disciplina SDD:** 3+ commits no mesmo subsistema em < 1h sem tocar `.specs/` → parar, 1 commit de código +
  1 commit `docs(specs): <F-ID> vX.Y.Z reconciliação Lote N`, retomar.
- 12.2 **Rebuild antes do commit:** editou `.specs/`? `spec-index.sh` antes do commit; `index.json` no mesmo commit.
- 12.3 **Filosofia de ADR:** Regra 7.
- 12.4 **Autonomia com limites:** com plano faseado aprovado, execute sem perguntar entre fases. Exceções que
  exigem confirmação: ADR novo, emenda de Constitution, deleção, merge, custo acima do combinado — salvo
  pré-aprovação explícita do humano na sessão (“siga sem parar” / “pré-aprovado”), que vale para todos os gates.
- 12.5 **Postmortem obrigatório:** fechamento de feature, incidente, smoke real, refresh de deps.
- 12.6 **Convenção repetida vira DS:** 2ª ocorrência de um padrão, “aqui sempre fazemos X” em revisão, ou lição de
  postmortem que é convenção → `/ds-new`, doc e enforcement no mesmo commit (Regra 13).

## Regra 13 — Design System compliance
`.specs/design-system/DS-*.md` é a meta-camada normativa: COMO se escreve código aqui (fronteiras de módulos,
padrões canônicos, testes, nomes, erros). Todo módulo, handler, componente, teste ou evento novo obedece ao DS
aplicável; desviar exige ADR. Leitura mínima por trabalho: módulo/pasta nova → DS-00 · teste → DS-06 · nome → DS-07 ·
erro/API → DS-05 · padrão que já tem DS-0N → DS-0N.
Nasce no F-SETUP (semente DS-00/06/07 descrevendo o esqueleto) e cresce por demanda — nunca antes de o código
existir: **DS é snapshot do que existe, normativo dali em diante.** Regra DS sem enforcement (lint, fronteira de
dependência, hook, ratchet test) é folclore e não deve ser escrita. Contagens afirmadas em DS são travadas por
ratchet test cuja falha cita o DS a atualizar.
Por quê (ADR-093 do ai-4sdlc-platform): o DS nasceu lá com 92 arquivos e 16 agentes já escritos; toda convenção
era folclore aprendido por grep, e cada PR introduzia uma variante. Aqui pagamos esse custo no dia 1, barato.

## Anti-padrões catalogados

| Quando | O que aconteceu | Correção |
|---|---|---|
| — | (vazia — a primeira linha nasce do primeiro postmortem) | — |

Toda nova burrice catalogada vira linha nesta tabela e ganha um postmortem. Linhas com prefixo `✓ POSITIVO`
documentam padrões a replicar.

## Quando começar a trabalhar
1. Siga a “Ordem de leitura” do CLAUDE.md (este arquivo, Constitution, product-spec, Design System, feature ativa). 2. Releia a Regra 12.
3. Antes de criar ADR/package/abstração, releia as Regras 1–5; antes de módulo/teste/nome novo, a Regra 13. 4. Em dúvida entre o que o usuário pede e o que
o repo manda: surface o conflito; não escolha em silêncio.
