---
id: RISK-F-SDD-TOOLING-V1
kind: risks
title: Riscos da evolução do template
parent: F-SDD-TOOLING-V1
version: 0.1.0
status: in_review
last_updated: 2026-10-26
---

| ID | Sev | Risco | Mitigação | Status |
|---|---|---|---|---|
| R-1 | ALTO | Tratar análise de shell como fronteira de segurança | Documentar limites; pedir avaliação para execução opaca; permissões nativas e revisão | mitigado |
| R-2 | MÉDIO | Herdar decisões e dados do projeto de origem | Base sem stack; padrões específicos só como guias; revisão do diff | mitigado; ver postmortem |
| R-3 | ALTO | Testes verdes sem cobrir o efeito | Contraprovas, stage divergente, parsing JSON e revisão independente | mitigado; ver postmortem |
