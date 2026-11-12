---
id: TASKS-F-SDD-TOOLING-V1
kind: tasks
title: Tarefas de evolução do tooling
parent: F-SDD-TOOLING-V1
version: 0.2.0
status: in_review
last_updated: 2026-11-12
---

| ID | Descrição | AC | Status | Evidência |
|---|---|---|---|---|
| T-001 | Setup e Git verificam o conteúdo efetivo | AC-1, AC-6 | done | scripts/tests/test_tooling.py |
| T-002 | Índice e lint determinísticos | AC-2, AC-7 | done | scripts/tests/test_tooling.py |
| T-003 | Guards e ciclo de sessão com contrato testado | AC-3, AC-4, AC-5 | done | scripts/tests/test_hooks.py |
| T-004 | Templates e relato de aprendizados sem dados de produto | AC-7, AC-8 | done | docs/learned-practices.md |
| T-005 | Runner com registro de cada rodada, relatório e hooks Git pelo runner | AC-9, AC-15 | done | scripts/tests/test_harness.py, test_team.py (hooks Git pelo runner) |
| T-006 | Estágio, rodada longa, veredito do check e verificação da junção | AC-10, AC-11 | done | scripts/tests/test_harness.py |
| T-007 | Travas do Stop: governança, papéis e IaC; aviso de clarificação na edição | AC-12, AC-13 | done | scripts/tests/test_team.py |
| T-008 | Subagentes: enforcement, mensagens e revisor; agentes dos papéis | AC-14 | done | scripts/tests/test_team.py; .claude/agents/ |
| T-009 | Tasks acompanham o push | AC-15 | done | scripts/tests/test_team.py |
| T-010 | Adaptador do Codex e instalador | AC-16 | done | scripts/tests/test_harness.py; disparo no Codex real não exercitado |
| T-011 | Lei, contexto, guias do time e do time paralelo, relato da segunda leitura | AC-8 | done | AGENTS.md, CLAUDE.md, docs/team.md, docs/parallel-team.md, docs/hooks.md, docs/learned-practices.md |

Validação do integrador em 2026-10-26: make check (24 testes), make test-mutations (4 contraprovas), make doctor e revisão adversarial independente após correções. Smoke automático do Claude e CI remota são limites registrados no postmortem.

Validação do integrador em 2026-11-12 (v0.2.0): make check e make test-mutations executados nesta data, com o resultado no postmortem PM-harness-absorption-2026-11-12. O disparo dos hooks novos no cliente real e o adaptador do Codex no runtime dele são limites registrados lá.
