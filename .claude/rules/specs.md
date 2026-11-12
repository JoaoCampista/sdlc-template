---
paths:
  - ".specs/**/*.md"
---
# Ao editar qualquer arquivo em .specs/
- Frontmatter completo (R1): `id kind title parent version status last_updated`. `parent` é obrigatório; nunca invente metadados.
- Mudança não-trivial → bump semver em `version`, `last_updated` hoje, nova entrada em `status_history` com nota do delta.
- Seções literais (R2) e ACs no formato `- **AC-N.** … @test:<path>` (R3). Toda AC verificável; toda task aponta 1+ AC.
- `status: approved` só sem `NEEDS_CLARIFICATION` aberto (R4) e com `@test:` existentes (R5).
- Status de task começa pelo estado verdadeiro (todo, doing, blocked com o motivo, done, deferred com dono) e sobe no mesmo push do código que a cita (o pre-push cobra).
- Quem escreve o quê: o `produto`, o QUÊ e as ACs de quem usa; a sessão principal, o HOW, as ACs técnicas, plan, tasks, risks e ADRs; o `design`, o design.md e os textos de interface. AC nova ou mudança de comportamento vai ao `produto` antes do código.
- Clarificação aberta numa spec in_review gera AVISO R4 a cada edição: trate na hora.
- Nunca apague história: risco fechado, AC removida, decisão revertida ganham **lápide** datada.
- Depois de editar: `scripts/sdd/spec-lint.sh <arquivo>` e `scripts/sdd/spec-index.sh`; `index.json` vai no mesmo commit.
- Commit: `docs(specs): <ID> vX.Y.Z — <descritor>` ou `feat(specs): <ID> vX.Y.Z — <descritor> (ADR-NNN)`.
