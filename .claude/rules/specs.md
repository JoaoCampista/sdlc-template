---
paths:
  - ".specs/**/*.md"
---
# Ao editar qualquer arquivo em .specs/
- Frontmatter completo (R1): `id kind title parent version status last_updated`. `parent` é obrigatório; nunca invente metadados.
- Mudança não-trivial → bump semver em `version`, `last_updated` hoje, nova entrada em `status_history` com nota do delta.
- Seções literais (R2) e ACs no formato `- **AC-N.** … @test:<path>` (R3). Toda AC verificável; toda task aponta 1+ AC.
- `status: approved` só sem `NEEDS_CLARIFICATION` aberto (R4) e com `@test:` existentes (R5).
- Nunca apague história: risco fechado, AC removida, decisão revertida ganham **lápide** datada.
- Depois de editar: `scripts/sdd/spec-lint.sh <arquivo>` e `scripts/sdd/spec-index.sh`; `index.json` vai no mesmo commit.
- Commit: `docs(specs): <ID> vX.Y.Z — <descritor>` ou `feat(specs): <ID> vX.Y.Z — <descritor> (ADR-NNN)`.
