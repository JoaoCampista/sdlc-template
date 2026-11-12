---
id: RISK-F-SDD-TOOLING-V1
kind: risks
title: Riscos da evolução do template
parent: F-SDD-TOOLING-V1
version: 0.2.0
status: in_review
last_updated: 2026-11-12
---

| ID | Sev | Risco | Mitigação | Status |
|---|---|---|---|---|
| R-1 | ALTO | Tratar análise de shell como fronteira de segurança | Documentar limites; pedir avaliação para execução opaca; permissões nativas e revisão | mitigado |
| R-2 | MÉDIO | Herdar decisões e dados do projeto de origem | Base sem stack; padrões específicos só como guias; revisão do diff | mitigado; ver postmortem |
| R-3 | ALTO | Testes verdes sem cobrir o efeito | Contraprovas, stage divergente, parsing JSON e revisão independente | mitigado; ver postmortem |
| R-4 | MÉDIO | Trava do Stop prende o turno sem saída (marca ausente, achado que só o humano destrava) | Segunda parada só informa; IaC bloqueia uma vez por achado; conferido com motivo registrado; travas inertes sem configuração | mitigado; testes em test_team.py |
| R-5 | MÉDIO | Registro do harness guarda comando, segredo ou conteúdo | A linha leva decisão, alvo e motivo mascarado e cortado; nunca o comando; .sdd fora do Git | mitigado; teste do mascaramento |
| R-6 | MÉDIO | Estágio de desenvolvimento ligado onde há dado real | Ausente por padrão; trocar pede o humano por Edit e é negado pelo shell em desenvolvimento; a sessão anuncia o estágio | mitigado; decisão de ligar é do projeto |
| R-7 | BAIXO | Adaptador do Codex e payload do scratchpad do revisor dependem do runtime do cliente | Tradução testada com fixtures; disparo real fica como verificação de adoção | aberto; smoke no cliente real |
