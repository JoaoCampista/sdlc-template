---
id: PM-harness-absorption-2026-11-12
kind: postmortem
title: Segunda leitura do uso real — o harness inteiro no template
parent: F-SDD-TOOLING-V1
version: 1.0.0
status: draft
last_updated: 2026-11-12
index: false
---

# O harness inteiro no template
Tipo: marco da F-SDD-TOOLING-V1 v0.2.0 (a feature segue aberta: é a spec do próprio tooling).

## §1. Objetivo
Pedido do mantenedor em 2026-11-12: absorver todo o conceito do harness do projeto de origem (hooks, agentes, tudo que funciona lá) e levá-lo ao template. O projeto de origem foi só lido. O que entrou é reescrita genérica, sem stack, nuvem, IDE, ferramenta de desenho ou pessoa fixas.

## §2. Funcionou
- Separar o mecanismo (Python do tooling) do que é do projeto (.claude/harness.json, vazio até o esqueleto) deixou as travas de papel e de infra inertes num clone novo, em vez de bloquear por caminhos que não existem.
- Um runner único deu registro a todos os hooks sem mudar a resposta de nenhum; o teste do wiring virou catraca contra hook fora dele.
- As 24 regressões anteriores seguiram verdes depois da troca do guard, com um ajuste de contrato declarado (ver §3).
- Cada controle novo de segurança tem contraprova em cópia temporária.

## §3. Deu errado
- O guard anterior respondia "perguntar" para todo rm. Ao classificar o caminho, apagar arquivo de código sem spec passou a ser negado, e dois testes antigos esperavam a pergunta. Era mudança de contrato (apagar código é escrever código, como na origem): os casos antigos passaram a usar um caminho livre e ganharam o caso de código negado. AC-4 segue valendo; registrado aqui por ter tocado teste existente.
- O primeiro teste do task-sync esperava recusa numa ref nova sem remoto; nesse caso todo o histórico sobe junto, inclusive o tasks.md, e passar é o certo. O teste passou a simular a ref remota.
- A sessão desta entrega não tinha os hooks do template carregados (aberta fora da raiz dele): as regras foram seguidas à mão e parte dos arquivos foi editada por script, não por Edit/Write. Lint, índice e drift rodaram depois, pelo make sdd.

## §4. Métricas
Medições desta data, não normativas: make check verde com 43 testes; make test-mutations detectou 14 alterações erradas deliberadas (4 anteriores e 10 novas). Uma rodada de revisão adversarial somente leitura; o resultado está em §5.

## §5. Lições
- **Spec gap identificado:** a v0.1.0 tratava "pergunta ao humano" como única saída para o que o guard não avalia; faltava dizer quem decide quando ninguém está olhando. A AC-10 fixa o estágio. Faltava também dizer que o enforcement tem dono (AC-14) e que registro atrasado é defeito cobrado (AC-12, AC-13, AC-15).
- **Convenção descoberta:** o que é de um projeto mora em configuração do projeto, nunca num ramo do código do tooling; trava do Stop bloqueia uma vez, informa na repetição e tem um "conferido" com motivo registrado. As duas estão em .claude/rules/tooling.md e têm teste.
- A revisão adversarial desta rodada: ver "Revisão" abaixo.

### Revisão
(preenchido depois da rodada)

## §6. Pendências
- Mantenedor: smoke dos hooks novos no Claude Code real (SessionStart com o bloco novo; negação a subagente no enforcement; SendMessage de subagente; a marca de papel num Agent de verdade; o scratchpad_dir do revisor). Os testes provam os scripts, não o disparo nem o payload do cliente.
- Mantenedor: exercitar make codex-hooks numa sessão real do Codex; a tradução só foi testada com fixtures.
- Mantenedor (G2): a Constitution cita a ADR-001, revisada depois dela; o enunciado da Constitution continua verdadeiro, e a emenda, se quiser listar as travas novas, é decisão dele. O SessionStart aponta isso.
- Quem adotar: preencher .claude/harness.json no esqueleto do produto e decidir o estágio; ligar a marca de apply no script de apply do projeto.
- CI remota em Linux e macOS com Python 3.9: conferir no push; a execução local foi Linux com Python 3.13.

## §7. Evidências
- scripts/tests/test_harness.py
- scripts/tests/test_team.py
- scripts/tests/test_hooks.py
- scripts/tests/mutation_checks.py
- .specs/features/F-SDD-TOOLING-V1/spec.md
- docs/learned-practices.md
- docs/hooks.md
- docs/team.md
- docs/parallel-team.md
