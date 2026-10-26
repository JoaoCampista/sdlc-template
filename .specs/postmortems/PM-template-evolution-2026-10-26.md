---
id: PM-template-evolution-2026-10-26
kind: postmortem
title: Evolução reutilizável do template a partir do uso real
parent: F-SDD-TOOLING-V1
version: 1.0.0
status: draft
last_updated: 2026-10-26
index: false
---

# Evolução do template
Tipo: feature-close.

## §1. Objetivo
Extrair práticas de um projeto real para uma base sem stack, sem editar o projeto observado. Templates, hooks, instruções, testes e guias foram atualizados. Não houve execução da aplicação de origem.

## §2. Funcionou
- Separar contratos universais de adaptadores e decisões do produto evitou copiar o guard específico de infraestrutura.
- Fixtures temporárias exercitam Git real com stage divergente, worktrees e ambiente herdado.
- Revisão independente reproduziu defeitos e verificou os consertos. Veredito final APROVAR no escopo revisado, sem alegar smoke de cliente ou CI remoto.

## §3. Deu errado
- Raiz herdada da sessão podia fazer hook Git conferir outro repositório. Fix: raiz explícita da operação Git nos wrappers e regressão entre dois repositórios.
- shlex descartava newline e depois newline consumido por comentário. Fix: preservar fronteiras simples; comentário multilinha pede avaliação conservadora; regressões de ambas as formas.
- Lint perdeu placeholders existentes. Fix: restaurar cobertura e exercitar templates parcialmente preenchidos.
- PostToolUse recebendo array JSON retornava erro não bloqueante. Fix: validar schema e normalizar falha inesperada para exit 2 nos wrappers.
- Path.resolve com ciclo difere entre versões Python. Fix: recusar symlink ainda não resolvido, inclusive com spec ativa; não depender só da exceção de uma versão.

- Primeiro commit real revelou falta de linha em branco antes de Refs; o título absorvia o trailer. Fix: bloco de trailers separado, preservando Refs; teste usa git interpret-trailers e confere o assunto.
- CI inicial encontrou Ubuntu 26.04 sem pacote Python 3.9; macOS executou check com sucesso. Fix: fixar Ubuntu 24.04, disponível no manifesto oficial, e não cancelar a outra plataforma por fail-fast.

## §4. Métricas
Medições locais desta entrega, não contagens normativas: make check passou com 24 testes; make test-mutations detectou 4 alterações deliberadamente erradas em cópias temporárias (guard removido, JSON inválido, índice com timestamp, stage sem validação); setup repetido e make doctor passaram. Suíte inicial: 18/19 antes da correção de schema; cobertura cresceu com os achados reais.

## §5. Lições
- **Spec gap identificado:** “falha fechada” precisa cobrir também erro inesperado do runtime; “raiz do repo” é a raiz efetiva do Git; multiline exige contraprova com comentário. AC-3, AC-4 e AC-6 ganharam regressões concretas.
- **Convenção descoberta:** validar o contrato de saída e o efeito real é uma prática reutilizável; registrada em AGENTS e regras de testes/tooling, com os testes correspondentes.
- Documentação distingue scripts testados de disparo automático do cliente. Aprovação final da spec não foi inferida.

## §6. Pendências
- Mantenedor/usuário do clone: executar smoke de carregamento dos eventos no Claude Code real antes de confiar na automação desse cliente. Esta sessão Codex validou scripts e wiring, não o disparo do Claude.
- CI remota: conferir o resultado do PR em Linux e macOS; a execução local foi macOS/Python 3.14. A configuração solicita Python 3.9 no CI.
- Integração na branch padrão fica para revisão do PR; não há merge/deploy implícito.

## §7. Evidências
- scripts/tests/test_hooks.py
- scripts/tests/test_tooling.py
- scripts/tests/mutation_checks.py
- .specs/features/F-SDD-TOOLING-V1/spec.md
- docs/learned-practices.md
- docs/hooks.md
- .github/workflows/ci.yml
