# Adaptador da stack — modelo de adoção

Preencha depois da ADR-002; não distribua este modelo como se já houvesse stack definida.

| Item | Registrar |
|---|---|
| Regras por caminho | Pastas reais de UI, contratos, backend, infra e testes; `.claude/rules/` carrega só o contexto relevante |
| Skill operacional | Entradas, passos, ferramentas, verificações e recuperação de falha; exemplos do código real |
| Referências progressivas | SKILL.md curto como índice; arquivos separados para tópicos especializados |
| Proveniência | Fonte primária, data consultada, versão mínima e limites por plataforma; marcar o não confirmado |
| Revisor da stack | Somente leitura, checks reais e padrões/antipadrões específicos; complementa spec-reviewer |
| Ferramentas que escrevem | Nome exato, matcher e payload; inclusive ferramenta sem caminho de arquivo |
| Formatação | Hook por extensão com erro visível; fallback para editores/MCP que não disparam o hook |
| Bootstrap e doctor | Dependências verificadas sem instalação silenciosa; comandos de setup idempotentes |
| Testes e CI | Herméticos por padrão; integração separada; build de cada plataforma realmente suportada |

Modelo de regra por caminho: frontmatter `paths` com globs reais, seguido de regras curtas que referenciam ADR/DS e enforcement. Não invente ferramentas ou caminhos; teste matchers e payloads com fixtures antes de declarar cobertura.
