---
id: F-SDD-TOOLING-V1
kind: feature_spec
title: Base reutilizável de templates e governança
parent: PROD-001
version: 0.2.0
status: in_review
risk_tier: limited
data_classification: public
owners: [maintainers]
slo: { deterministic_checks: true }
deps: []
related_adrs: [ADR-001]
issue: none
last_updated: 2026-11-12
spec_hash: pending
status_history:
  - { version: 0.2.0, status: in_review, date: 2026-10-26, note: "escopo solicitado pelo mantenedor: absorver melhorias do uso real, preservando produto e stack em aberto; não é aprovação final" }
  - { version: 0.2.0, status: in_review, date: 2026-11-12, note: "pedido do mantenedor em 2026-11-12 (absorver todo o conceito do harness do projeto de origem: hooks, agentes, tudo que funciona lá): registro de cada rodada, travas de governança no Stop, papéis, estágio, time e adaptador do Codex (AC-9 a AC-16); não é aprovação final" }
---

# F-SDD-TOOLING-V1 — Ferramentas do próprio template

Esta feature descreve o método distribuído, não o produto que o usuário criará. O bootstrap do PROD-001 continua pendente.

## WHAT/HOW
### WHAT
Novos usuários recebem templates de spec e design, instruções coerentes e verificações reproduzíveis sem dados, infraestrutura ou decisões do projeto de origem.
### HOW
Shell portátil para os comandos; Python 3 (biblioteca padrão) para caminhos, JSON, inspeção conservadora de comandos e testes do tooling. Isso não escolhe a linguagem do produto. Sem instalar pacotes ou plugins automaticamente.

Desde a v0.2.0: scripts/sdd/harness.py (runner, relatório, veredito, estágio, junção), scripts/sdd/sync.py (governança, papéis, infra, tasks, painel), scripts/sdd/codex.py (adaptador) e .claude/hooks/team.py (travas do Stop, marca de papel, mensagens e revisor). O que é do projeto (caminhos de cada papel, raízes de IaC, travas da junção, alvos longos) mora em .claude/harness.json, vazio até o bootstrap; o estágio em .claude/deploy-stage.json, ausente por padrão. Os papéis produto, design, arquiteto e juridico são subagentes sem ferramenta de design, nuvem ou lei fixas.

## User Stories
- **US-1.** Como usuário do template, quero começar com produto e stack indefinidos e saber quais controles estão ativos.
- **US-2.** Como mantenedor, quero que uma alteração inválida seja detectada pelo seu efeito, inclusive com stage diferente do disco.

## Acceptance Criteria
- **AC-1.** Setup repetido preserva spec ativa e identidade, aceita worktree, não cria commit nem sobrescreve hooks de terceiros. @test:scripts/tests/test_tooling.py
- **AC-2.** Índice determinístico preserva bytes/mtime sem mudanças; IDs duplicados e dados inválidos falham sem substituir índice válido; drift detecta remoção, adição e alteração. @test:scripts/tests/test_tooling.py
- **AC-3.** Guard de edição exige spec in_review/approved, resolve symlinks/cwd, protege o índice e pede revisão do enforcement; entrada inválida falha com exit 2. @test:scripts/tests/test_hooks.py
- **AC-4.** Guard Bash identifica escritas simples, bypass de hooks e comandos destrutivos; comandos opacos pedem avaliação, sem alegar ser sandbox. @test:scripts/tests/test_hooks.py
- **AC-5.** Stop emite exatamente um objeto JSON, bloqueia drift/iteração sem spec e evita repetição infinita; PostToolUse propaga falhas do índice. @test:scripts/tests/test_hooks.py
- **AC-6.** Pre-commit confere snapshot do stage; trailer usa hash staged, inclusive amend; pre-push confere as revisões enviadas. @test:scripts/tests/test_tooling.py
- **AC-7.** Templates incluem design independente de plataforma, tasks com evidência e handoff; lint aceita design e rejeita artefatos inválidos. @test:scripts/tests/test_tooling.py
- **AC-8.** Documentação distingue práticas incorporadas, padrões opcionais e escolhas do produto; configuração não contém caminhos pessoais, plugins ou permissões de stacks não escolhidas. @test:scripts/tests/test_hooks.py

- **AC-9.** Todo hook do settings roda por um runner que devolve a mesma saída e o mesmo código, falha fechado com hook ausente e grava uma linha por rodada (decisão, motivo mascarado, alvo, tempo; nunca o comando); o relatório mede intervenções, motivos e insistência, e linha ilegível é contada. @test:scripts/tests/test_harness.py
- **AC-10.** O estágio declarado decide o que pedia o humano: fora de desenvolvimento, pergunta; em desenvolvimento, o irreversível é negado com o motivo e o resto passa com registro; arquivo ausente ou inválido vale como o estágio que pergunta; trocar o estágio sempre pede o humano. @test:scripts/tests/test_harness.py
- **AC-11.** Rodada longa num pipe sem tee para arquivo é negada; make check grava o veredito (commit, resultado, o que falhou) e a sessão o mostra; a verificação da junção roda só as travas que leem arquivos mudados e falha fechada sem a base. @test:scripts/tests/test_harness.py
- **AC-12.** O Stop bloqueia documento de cima atrasado (status de feature sem o product-spec depois do bootstrap, ADR citada sem a Constitution, feature sem task aberta com clarificação aberta); marca ausente ou inválida bloqueia; o conferido se registra com motivo; clarificação aberta de spec in_review vira aviso na edição. @test:scripts/tests/test_team.py
- **AC-13.** Caminhos de um papel mudados depois do último pedido ao subagente dele bloqueiam o Stop; a marca só avança quando o pedido rodou; IaC commitada depois do último apply registrado bloqueia uma vez por achado; sem caminhos configurados, as duas travas ficam inertes. @test:scripts/tests/test_team.py
- **AC-14.** Subagente não edita o enforcement, só manda mensagem à sessão principal, e o revisor escreve só na própria memória e na cópia de mutação fora do repositório, pelo caminho real. @test:scripts/tests/test_team.py
- **AC-15.** O push que cita task de uma feature em commit de código sem mudar o tasks.md dela é recusado; os hooks Git passam pelo runner com registro. @test:scripts/tests/test_team.py
- **AC-16.** O adaptador do Codex traduz sessão, Bash, patch e Stop para os guards canônicos, transforma pergunta em negação e recusa payload ou gramática inválidos; o instalador preserva configuração diferente. @test:scripts/tests/test_harness.py

## Risks
Ver risks.md: heurística de shell, adoção indevida de regras específicas, falsa confiança nos testes, trava que prende o turno e registro com dado sensível.

## Out of scope
- Modificar o projeto de origem; copiar sua identidade, features, tokens, credenciais ou infraestrutura.
- Escolher stack do produto, instalar ferramentas, promover aprovação humana ou efetuar deploy/merge.

## NFRs
Testes herméticos em diretórios temporários; Bash 3.2+, Python 3.9+, Git e jq. Falha de verificação não vira sucesso.

## NEEDS_CLARIFICATION
- nenhum
