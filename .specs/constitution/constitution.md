---
id: CONST-001
kind: constitution
title: Constitution — camada de governança computável
parent: none
version: 1.0.0
status: approved
owners: [ceia]
last_updated: 2026-09-05
status_history:
  - { version: 1.0.0, status: approved, date: 2026-09-05, note: "adoção do método SDD (ADR-001); stack a definir no bootstrap" }
---

# Constitution

Tudo o que estiver aqui é regra; o linter, os hooks e o agente devem cobrá-las. Mudanças exigem PR aprovado e bump de versão.

## §1 Princípios diretores (não-negociáveis; em conflito, o de número menor vence)

1. **Spec antes de código.** Nenhuma mudança não-trivial entra sem spec correspondente em `.specs/`.
   Enforcement: hook `PreToolUse` bloqueia edição de código sem `.sdd/active-spec`; trailer `Spec-Hash` no commit; `spec-drift` em pre-commit/pre-push (e no CI, a criar no F-SETUP).
2. **Humano decide o irreversível.** ADR, emenda desta Constitution, deleção de dados, merge e deploy exigem aprovação humana explícita, registrada.
3. **Auditável por construção.** Toda decisão relevante deixa rastro: ADR, `status_history`, postmortem, trailer de commit. Faltar rastro é falha.
4. **Determinismo onde possível, LLM onde necessário.** Verificações determinísticas (testes, lint, hooks, hashes) precedem julgamento de modelo.
5. **Forma humana, parsing máquina.** Specs, planos, ADRs e postmortems são Markdown legível; validação usa frontmatter YAML, nunca regex sobre prosa livre.

## §2 Stack canônica

| Camada | Decisão | ADR |
|---|---|---|
| Linguagem/runtime | a definir no bootstrap | ADR-002 (pendente) |
| Framework | a definir no bootstrap | ADR-002 (pendente) |
| Persistência | a definir no bootstrap | ADR-002 (pendente) |
| Testes / lint | a definir no bootstrap | ADR-002 (pendente) |

Preencher esta tabela pela primeira vez (ADR-002, no bootstrap) é bump `minor` (1.0.0 → 1.1.0), aprovado no gate G2. Trocar uma linha depois disso exige ADR-v2 (`supersedes`) e bump `major`.

## §3 NFRs default (ISO 25010), herdados por toda Feature Spec salvo override justificado em ADR

- Adequação funcional: 100% das ACs com `@test:` passando.
- Confiabilidade: sem regressão em suíte; erro é tratado, nunca engolido.
- Segurança: segredos fora do repo; entrada validada na borda; erros em formato único e documentado.
- Manutenibilidade: lint verde; regra suprimida só com razão de domínio.

## §7 Regras de spec (computáveis, sob pena de rejeição pelo lint)

1. Frontmatter válido (R1). 2. Seções literais (R2). 3. ≥1 AC com `@test:` (R3). 4. Sem `NEEDS_CLARIFICATION` aberto em `approved` (R4).
5. `@test:` existe (R5). 6. ID hifenado `F-{DOMINIO}-V{N}` / `C-{NOME}`; `parent` obrigatório. 7. Hash da spec batido no trailer `Spec-Hash:` do commit que a aprova.

## §9 Governança (emendas)

`patch` (texto, sem efeito computável): PR normal. `minor` (novo princípio/NFR/regra; primeiro preenchimento de §2): aprovação humana explícita registrada (gate G2 ou revisão de PR).
`major` (revogar princípio, trocar stack já definida em §2): ADR-v2 + aprovação humana explícita; em time, RFC antes do PR. **Toda regra computável tem teste co-localizado. Regra sem teste é regra inexistente.**
Cada bump ganha entrada em `status_history` e bloco `## Changelog` ao final.

## §13 Hierarquia

> Numeração de seções herdada do CONST-001 do ai-4sdlc-platform; §4–§6, §8 e §10–§12 ficam reservados para as extensões correspondentes (NFRs por tier, orquestração, regulatório).

```
Constitution (CONST-001)
  ├── Design System (DS-0N, parent CONST-001) — meta-camada: COMO se escreve código (§14)
  └── Product Spec (PROD-001)
       ├── Feature Spec (F-*) ── PLAN-F-*, TASKS-F-*, RISK-F-*
       └── Component Spec (C-*) ── PLAN-C-*, RISK-C-*   (parent: F-* ou C-*)
ADRs — transversais · Postmortems — via parent, fora do índice
```

Cada subcomponente com ciclo de evolução próprio merece Component Spec dedicada.

## §14 Design System (meta-camada)

`.specs/design-system/DS-*.md` (`kind: design_system_spec`, `parent: CONST-001`) é normativo para todo código novo:
fronteiras de módulos, padrões canônicos, testes, nomes, erros. Regras computáveis: (1) todo DS tem `## Enforcement`
com uma linha por regra apontando lint/fronteira/hook/ratchet — o lint rejeita DS com regra sem linha de enforcement;
(2) DS descreve o que existe (exemplos com path real) e obriga dali em diante; (3) desvio exige ADR; (4) F-SETUP
entrega a semente DS-00 (arquitetura/fronteiras), DS-06 (testes) e DS-07 (nomes). Ver Regra 13 em AGENTS.md.

## Changelog
- 1.0.0 (2026-09-05): versão inicial (§1–§13 + §14 Design System).
