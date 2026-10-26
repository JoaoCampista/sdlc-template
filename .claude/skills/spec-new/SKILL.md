---
name: spec-new
description: Cria feature ou componente com contrato verificável, plano, riscos e design quando há UI.
argument-hint: "F-DOMINIO-V1 | C-NOME [título]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(bash scripts/sdd/*), Bash(git status *), Bash(git log *)
---

1. Leia produto, Constitution, ADRs e DS aplicáveis. Use contexto existente; pergunte só o que altera o desenho. Registre premissas e não invente aprovação.
2. Produto → F-DOMINIO-V1, parent PROD-001; componente interno → C-NOME, parent de feature/componente existente. Mudança trivial coberta reutiliza o contrato vigente.
3. Copie o _TEMPLATE apropriado, preencha frontmatter, WHAT/HOW, stories, ACs com @test:caminho, NFRs e clarificações. Preencha risco/dados/owners conforme contexto, indicando premissas. Template não é documento pronto.
4. Plan descreve arquivos, contratos e ordem; tasks ligam AC, dependência e evidência; risks registra riscos reais com mitigação (não invente três para cumprir contagem).
5. UI exige design.md com cada estado/variante, referência visual, componentes, texto, foco/acessibilidade e plano de evidências. Sem UI: não aplicabilidade explícita; componente sem UI não precisa desse arquivo.
6. Decisão transversal nova → /adr-new. Seguir padrão já decidido não exige ADR por endpoint/DTO/tabela.
7. `make sdd`; apresente contrato e premissas para G1 quando ainda não autorizado. Autorização existente para o mesmo escopo persiste. Registre sua origem no status_history; não atribua aceite final.
8. G1 → in_review; grave ID em .sdd/active-spec. Commit lógico com índice. Siga CLAUDE.md: implementação, testes, revisão, evidência, postmortem e limpar spec ativa. approved só com aceite final registrado.
