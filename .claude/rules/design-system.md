---
paths:
  - ".specs/design-system/**"
---
# Ao criar ou editar docs do Design System
- DS é **snapshot do que existe**, normativo dali em diante. Toda regra cita um exemplo real (path:linha). Sem 2 ocorrências no código, ainda não é convenção — exceto a semente DS-00/06/07 do F-SETUP, que descreve o esqueleto.
- Toda regra tem linha em `## Enforcement` (lint, fronteira de dependência, hook, ratchet test), e o enforcement entra no mesmo commit que o doc. Regra sem enforcement é folclore — não escreva.
- Contagens afirmadas no DS (N módulos, N eventos) são travadas por ratchet test cuja mensagem de falha cita o DS a atualizar; mude número e doc no mesmo commit.
- Mudança de regra: bump `version`, `last_updated`, `## Changelog`. Desviar do DS no código não se resolve editando o DS: exige ADR.
- Depois de editar: `scripts/sdd/spec-lint.sh <doc>` e `scripts/sdd/spec-index.sh`. Um commit por DS, doc + fence juntos: `docs(ds): DS-0N — <tema> (+ fence)`.
