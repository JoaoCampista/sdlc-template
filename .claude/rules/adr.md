---
paths:
  - ".specs/adr/**"
---
# Ao criar ou editar ADRs
- Antes de criar: “é decisão arquitetural NOVA ou extensão do ADR-YYY?” Extensão → `## Revisões` em YYY. Novo só para decisão nova, reversão (`-v2`, `supersedes`) ou nova área.
- Numeração 3 dígitos crescente (`ls .specs/adr | sort | tail -1`); verifique colisão. Reversão: `ADR-NNN-v2-slug.md`; o original recebe `status: superseded` e `superseded_by`.
- Seções: Contexto · Decisão · Consequências (inclua o que se PERDE) · Alternativas consideradas · Riscos · Fences contra regressão · Revisões.
- Justificativa “o código já depende disso” é circular (Regra 3). Se a decisão cabe em 3 linhas de código, talvez não seja ADR.
- Toda ADR nova entra em `related_adrs` das specs afetadas e na tabela §2 da Constitution se tocar stack.
