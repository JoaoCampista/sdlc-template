# Padrões opcionais para a stack escolhida

Estes são roteiros de decisão, não regras DS já aprovadas para código inexistente. Adote quando houver necessidade; implemente exemplo e teste antes de torná-los normativos.

| Padrão | Quando ajuda | Decisões e teste necessário |
|---|---|---|
| Contrato único | Vários consumidores da mesma API/evento | Schema/pacote fonte, geração/importação, versão e compatibilidade; consumidor antigo com exemplo publicado |
| Fixtures imutáveis | Clientes instalados recebem contratos versionados | Exemplo novo para versão nova; teste de alteração, remoção e renomeação contra histórico relevante; clone raso falha quando histórico é requisito |
| Migrações que só crescem | Banco mantém histórico de deploy | Migração aplicada não é reescrita; validar hash/ordem, lock e caso de concorrência; rollback decidido por risco |
| Tokens com geração determinística | Biblioteca visual e código precisam concordar | Fonte única, overrides explícitos, comando, comparação de saída e stage coerente; não editar gerado |
| Erro tipado na borda | API/CLI trata falhas de SDK e configuração | Código estável, status e mensagem; causa técnica protegida; teste de ausência de segredo e resultado em falha |
| Validação do destino efetivo | CLI/driver aceita variável, perfil ou contexto | Resolver host/banco/papel real antes do efeito; testar override de ambiente e alvo errado |
| Teste hermético + integração separada | Serviços externos existem | Padrão isolado; integração só no ambiente de teste validado; conexão inválida recusa antes de conectar |
| Comando administrativo de uso único | Migração, rotação, provisionamento | Menor privilégio, papel conferido antes do primeiro efeito, idempotência, registro e falhas visíveis |
| Autorização antes do efeito | Operação tem escopo de usuário/organização | Toda negativa deixa zero efeito observável; testar acesso negado e corrida, não só HTTP de resposta |
| Orçamento de concorrência | Integração/DDL/consumidores disputam recursos | Pool e workers dimensionados, isolamento de dados, deadline e locks explícitos; teste de concorrência real |
| Adaptador de IDE/MCP | Ferramenta mantém projeto em memória | Payload real, quais ferramentas escrevem, estado de workspace e verificação pós-edição; não copiar regras de Xcode para toda stack |
| Procedimento de operação | Deploy, restauração e backup | Separar leitura/planejamento/execução; verificar artefato e destino, ensaiar falhas e evidenciar restauração real |

A lista explica o que aproveitar do projeto observado; não inclui sua implementação, serviços, versões, papéis de banco ou política de retenção. Uma convenção repetida comprovada pode virar DS com enforcement no mesmo commit.

Para serviços, também vale decidir explicitamente: liveness separada de readiness, inicialização que tolera dependência indisponível quando isso é requisito, deadlines nas sondas, recuperação após mudança de DNS e nenhuma operação bloqueante no event loop. A decisão depende do produto; o teste precisa simular indisponibilidade e recuperação. Escrita no banco seguida de publicação externa exige decidir consistência, repetição e falha parcial (por exemplo, outbox), em vez de esconder o risco numa chamada de SDK.
