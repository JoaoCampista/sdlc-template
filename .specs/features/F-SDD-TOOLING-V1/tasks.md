---
id: TASKS-F-SDD-TOOLING-V1
kind: tasks
title: Tarefas de evolução do tooling
parent: F-SDD-TOOLING-V1
version: 0.1.0
status: in_review
last_updated: 2026-10-26
---

| ID | Descrição | AC | Status | Evidência |
|---|---|---|---|---|
| T-001 | Setup e Git verificam o conteúdo efetivo | AC-1, AC-6 | done | scripts/tests/test_tooling.py |
| T-002 | Índice e lint determinísticos | AC-2, AC-7 | done | scripts/tests/test_tooling.py |
| T-003 | Guards e ciclo de sessão com contrato testado | AC-3, AC-4, AC-5 | done | scripts/tests/test_hooks.py |
| T-004 | Templates e relato de aprendizados sem dados de produto | AC-7, AC-8 | done | docs/learned-practices.md |

Validação do integrador em 2026-10-26: make check (24 testes), make test-mutations (4 contraprovas), make doctor e revisão adversarial independente após correções. Smoke automático do Claude e CI remota são limites registrados no postmortem.
