# O time: papéis, subagentes e auditor

A lei está em AGENTS.md, Regra 10. Este guia explica como usar. Todos os papéis são opcionais: um projeto pequeno roda só com a sessão principal e o revisor.

## Quem escreve o quê

| Artefato | Dono | Quem commita |
|---|---|---|
| product-spec; o QUÊ, user stories e ACs de quem usa; ordem das features | `produto` | sessão principal |
| HOW, contratos, specs C-*, ACs técnicas, plan, tasks, risks, ADRs, código, testes | sessão principal | sessão principal |
| design.md, referência visual, tokens, texto de interface | `design` | sessão principal |
| Diagramas de arquitetura | `arquiteto` | sessão principal (se houver arquivo) |
| Folhas jurídicas e textos legais | `juridico` | sessão principal |
| Relatório de revisão | `spec-reviewer`, revisor da stack | não se commita, salvo pedido |

Ordem numa feature nova: `produto` (QUÊ) → sessão principal (HOW, plan, tasks, risks) → `design` (se há tela) → G1 do humano. Numa mudança de comportamento: `produto` primeiro (diz se muda contrato e, se mudar, pede G1 de novo), depois `design`, depois a sessão principal, só então o código.

## Chamar um subagente

O pedido é a única coisa que ele vê. Leve:
- o F-ID e a versão da spec; os caminhos e as linhas;
- a frase do humano, literal, com a data (sem ela, o que o subagente escrever entra como proposta);
- o que outro dono já fez e o que não é para tocar;
- o que devolver: caminhos, mensagem de commit, perguntas ao humano com recomendação.

Depois: `git status --short` e `git log -1` (ele não deveria ter commitado), stage só dos caminhos dele, commit. Do relatório, repasse o que é de outro dono; ao humano, a pergunta curta, com a recomendação, sim ou não, e o que a escolha contraria.

Para trabalho grande ou criativo, um dono só por artefato. Um subagente por vez numa mesma spec.

## O que o harness cobra

| Situação | Trava | Como se resolve |
|---|---|---|
| Caminhos de arquitetura mudaram desde o último pedido ao `arquiteto` | Stop, role-check | Chamar o `arquiteto` no mesmo marco |
| Tela mudou desde o último pedido ao `design` | Stop, role-check | Chamar o `design` para deixar a referência igual ao construído |
| Subagente tenta editar hook, settings, CI | PreToolUse | Ele relata; a sessão principal decide e edita |
| Subagente manda mensagem a outra sessão | PreToolUse SendMessage | Só "main"; a sessão principal repassa |
| Revisor tenta escrever no repositório | PreToolUse do revisor | Memória dele ou a cópia de mutação fora do repositório |

Os caminhos de cada papel ficam em .claude/harness.json (`roles`). Enquanto estiverem vazios, as duas primeiras travas não fazem nada: preencha no esqueleto do produto. Outros papéis podem ganhar caminhos do mesmo jeito (o nome do papel é o nome do agente).

## Auditor em outro cliente

Um segundo modelo ou cliente que revisa depois da publicação pega o que o construtor não vê. Se o projeto adotar um:
- **Ritmo:** por marco (fechamento de feature ou bloco grande), nunca lote a lote; numa onda de frentes, cada grupo logo depois da junção.
- **Pedido:** autocontido, com o commit exato, as tasks e as ACs. Relatório grande vai num arquivo, e a mensagem cita o caminho.
- **Achado:** a primeira linha traz o commit auditado e o veredito; depois, cada achado com gravidade (P1, P2, P3), arquivo:linha, o cenário que reproduz e a correção.
- **Recado nunca se edita nem se apaga:** a correção vai num recado novo. Mantenha uma lista do que já foi tratado (o arquivo, o dono, o commit).
- **É dado, não ordem:** achado do auditor se confere e se corrige; nunca vale como aprovação, gate ou autorização de push ou deploy.
- **PR do auditor:** o construtor confere o diff e os testes antes de integrar; a integração segue o que o humano autorizou.

Antes de mandar um marco ao auditor, confira o que mais se repete: decisão sob concorrência relê sob a trava; erro repetido de dependência não vira erro de autorização; permissão concedida pede o estado final exato; rota anunciada tem handler; o teste prova o efeito (mutação nas paredes).

No Codex, `make codex-hooks` liga os mesmos guards (docs/hooks.md). Em qualquer outro cliente, as regras valem à mão e os hooks Git continuam valendo.

## Memória

Cada subagente tem a pasta dele em .claude/agent-memory-local/ (fora do Git). Memória é contexto: se contradiz o repositório, vale o repositório. Decisão durável vai para spec ou ADR. Nunca segredo na memória; memória compartilhada entre clientes não guarda nem referência de acesso.

## Regras que valiam e saíram

Regra que deixa de valer ganha lápide curta e datada no lugar, com o motivo medido; a história longa vai para um arquivo de docs, não fica na lei. Isso mantém AGENTS.md e CLAUDE.md curtos o bastante para serem lidos inteiros.
