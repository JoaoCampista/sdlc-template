---
id: PLAN-F-SDD-TOOLING-V1
kind: plan
title: Plano de evolução do tooling
parent: F-SDD-TOOLING-V1
version: 0.1.0
status: in_review
last_updated: 2026-10-26
---

## Estratégia
Extrair os contratos observados e implementar uma base menor, sem transplantar o guard específico de infraestrutura. Ampliar ADR-001; reservar ADR-002 para a stack do usuário.
## Arquivos tocados
AGENTS.md, CLAUDE.md, README.md, .claude/, .specs/, scripts/, Makefile, docs/ e CI.
## Passos
1. Templates e guias, com fonte e limites de cada aprendizado.
2. Regressões em fixtures, índice, hooks e setup.
3. Revisão adversarial independente, correções e postmortem.
## Verificação
make check; instalação e commits reais em repositórios temporários; contraprovas com corrupção, stage divergente e remoção de controles.
