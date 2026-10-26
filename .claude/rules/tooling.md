---
paths:
  - ".claude/hooks/**"
  - ".claude/settings*.json"
  - "scripts/sdd/**"
  - "scripts/tests/**"
  - ".github/**"
---
# Ao mudar o mecanismo

- Leia F-SDD-TOOLING-V1. Mudança de contrato → spec primeiro, teste de regressão com caso que falha antes do fix.
- Setup idempotente preserva estado/identidade/hooks preexistentes. Paths com espaços e .git arquivo são casos reais.
- Guards falham com exit 2 em entrada/estado inválido; stdout respeita protocolo JSON, stderr guarda diagnóstico.
- Índice determinístico é escritor único. Commit valida stage e trailer usa o mesmo conteúdo; Git hook usa a raiz da operação Git, não a raiz herdada da sessão.
- Não ampliem promessa de segurança além dos testes; Bash é heurística, MCP precisa de adaptador específico.
- Rode make check, revisão somente leitura e contraprovas em temporários. Não use Spectrolite como fixture mutável.
