---
name: spec-new
description: Cria uma Feature Spec (F-*) ou Component Spec (C-*) completa a partir dos templates de .specs/, eliciando requisitos antes. Use quando o usuário pedir feature/recurso/endpoint/componente novo, ou quando o hook bloquear edição de código por falta de spec.
argument-hint: "<F-DOMINIO-V1 | C-NOME> [título]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(scripts/sdd/*), Bash(ls *), Bash(date *), Bash(xargs *), Bash(basename *), Bash(grep *), Bash(sort *), Bash(tail *)
---
## Contexto
Specs existentes: !`ls -d .specs/features/F-* .specs/components/C-* 2>/dev/null | xargs -n1 basename`
Hoje: !`date +%Y-%m-%d`
Último ADR: !`ls .specs/adr | grep -v template | sort | tail -1`

## Procedimento para $ARGUMENTS
1. **Elicite só o que muda o desenho** — no máximo 3 perguntas, uma por vez (limites/erros, o que fica fora, dado pessoal?). O que der para inferir do product-spec, infira e registre como premissa na spec.
2. Decida o tipo: intenção de produto → `F-<DOMINIO>-V1` (`parent: PROD-001`); contrato técnico interno → `C-<NOME>` (`parent:` F-* ou C-* existente). Se a mudança é trivial e já coberta por spec existente, diga isso e pare: não infle.
3. Copie o template (`.specs/features/_TEMPLATE/*` ou `.specs/components/_TEMPLATE/*`) para a pasta do ID e preencha **tudo**: sem placeholders `<…>`.
4. ACs: verificáveis, uma por comportamento, cada uma com `@test:<path>` real no local que o DS-06 define (co-location ou pasta de testes); o arquivo pode ainda não existir em draft. Erros e limites são ACs também.
5. `plan.md` (passos), `tasks.md` (toda task → 1+ AC), `risks.md` (≥3 riscos com mitigação).
6. Se a spec implica decisão arquitetural (stack, persistência, integração, contrato público) → invoque `/adr-new` e referencie em `related_adrs`.
7. Rode `scripts/sdd/spec-lint.sh <spec>` até OK; `scripts/sdd/spec-index.sh`.
8. **Gate G1:** mostre um resumo (ACs, riscos, premissas) e pergunte “aprova a spec <ID>?”. Se o usuário já disse “siga sem parar”/“pré-aprovado”, considere aprovada.
9. Aprovada → `status: in_review` (+ `status_history`), `echo <ID> > .sdd/active-spec`, `scripts/sdd/spec-index.sh`, commit `feat(specs): <ID> v0.1.0 — <descritor>`. Nunca marque `approved` sozinho (Constitution §1.2).
10. Continue o fluxo do CLAUDE.md: passo 3 (ADR?) → implementação por AC → spec-reviewer → postmortem.
