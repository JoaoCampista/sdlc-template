---
name: adr-new
description: Cria ou revisa um Architecture Decision Record em .specs/adr seguindo a Regra 7 (ADR é decisão, não ticket). Use quando houver escolha de stack, persistência, integração, contrato público, padrão arquitetural, ou reversão de decisão anterior.
argument-hint: "<título da decisão>"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls *), Bash(date *), Bash(scripts/sdd/*), Bash(grep *)
---
## Contexto
ADRs existentes: !`ls .specs/adr | grep -v template`
Hoje: !`date +%Y-%m-%d`

## Procedimento para: $ARGUMENTS
1. Leia os títulos acima. Pergunte-se e responda por escrito: “isto é decisão NOVA, extensão de ADR-YYY, ou reversão de ADR-YYY?”
   - Extensão → edite ADR-YYY: adicione item datado em `## Revisões`, bump `version` minor, `last_updated`. Pare aqui.
   - Reversão → novo `ADR-YYY-v2-<slug>.md` com `supersedes: [ADR-YYY]`; no original, `status: superseded` + `superseded_by`.
   - Nova → próximo número (3 dígitos), `ADR-NNN-<slug>.md` a partir de `.specs/adr/ADR-000-template.md`.
2. Escreva Contexto sem citar “o código já depende disso” (Regra 3). Liste ≥2 alternativas reais e por que perderam.
3. Em Consequências, registre honestamente o que se PERDE. Em Fences, diga qual teste/hook/ratchet impede regressão silenciosa.
4. `status: in_review`. **Gate G2:** peça o aceite ao humano (se ele disse “siga sem parar”, considere aceito) → `status: accepted`.
5. Atualize `related_adrs` das specs afetadas. Se tocar stack: primeiro preenchimento de §2 (ADR-002) = bump `minor` da Constitution; troca posterior = ADR-v2 + bump `major` (§9).
6. `scripts/sdd/spec-lint.sh <adr>`; `scripts/sdd/spec-index.sh`. Commit: `docs(adr): ADR-NNN — <título>`.
