---
id: F-SDD-TOOLING-V1
kind: feature_spec
title: Base reutilizável de templates e governança
parent: PROD-001
version: 0.1.0
status: in_review
risk_tier: limited
data_classification: public
owners: [maintainers]
slo: { deterministic_checks: true }
deps: []
related_adrs: [ADR-001]
issue: none
last_updated: 2026-10-26
spec_hash: pending
status_history:
  - { version: 0.1.0, status: in_review, date: 2026-10-26, note: "escopo solicitado pelo mantenedor: absorver melhorias do uso real, preservando produto e stack em aberto; não é aprovação final" }
---

# F-SDD-TOOLING-V1 — Ferramentas do próprio template

Esta feature descreve o método distribuído, não o produto que o usuário criará. O bootstrap do PROD-001 continua pendente.

## WHAT/HOW
### WHAT
Novos usuários recebem templates de spec e design, instruções coerentes e verificações reproduzíveis sem dados, infraestrutura ou decisões do projeto de origem.
### HOW
Shell portátil para os comandos; Python 3 (biblioteca padrão) para caminhos, JSON, inspeção conservadora de comandos e testes do tooling. Isso não escolhe a linguagem do produto. Sem instalar pacotes ou plugins automaticamente.

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

## Risks
Ver risks.md: heurística de shell, adoção indevida de regras específicas e falsa confiança nos testes.

## Out of scope
- Modificar o projeto de origem; copiar sua identidade, features, tokens, credenciais ou infraestrutura.
- Escolher stack do produto, instalar ferramentas, promover aprovação humana ou efetuar deploy/merge.

## NFRs
Testes herméticos em diretórios temporários; Bash 3.2+, Python 3.9+, Git e jq. Falha de verificação não vira sucesso.

## NEEDS_CLARIFICATION
- nenhum
