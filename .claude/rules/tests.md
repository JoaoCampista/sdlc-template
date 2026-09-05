---
paths:
  - "tests/**"
  - "**/*.test.*"
  - "**/*_test.*"
  - "**/test_*"
  - "**/*.spec.*"
  - "test/**"
  - "__tests__/**"
---
# Ao editar testes
- Cada teste nasce de uma AC e a cita no nome ou docstring (`AC-3`). Teste sem AC referenciada = super-decomposição.
- Nunca altere um teste existente para fazê-lo passar. Se a AC estava errada, corrija a AC primeiro (playbook Bug do CLAUDE.md) e só então o teste.
- Teste primeiro, confirme que falha pelo motivo certo, implemente. Não use `skip`/`xfail` sem razão de domínio no comentário (Regra 8).
