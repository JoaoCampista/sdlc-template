---
paths:
  - "**/tests/**"
  - "**/Tests/**"
  - "**/*test*"
  - "**/*Test*"
---
# Ao trabalhar com testes

- Teste comportamento da AC, incluindo erro/limite. Não teste só formato de texto quando o efeito é executável.
- Padrão hermético: fixtures temporárias, sem rede/contas/serviços reais. Integração tem comando separado, destino de teste validado e recursos dimensionados.
- Dublê de CLI/SDK reproduz as recusas, exit codes e respostas que o código trata. Não aceite tudo silenciosamente.
- Para proteção crítica, retire a proteção em uma cópia e confirme que a regressão falha. Teste positivo também deve passar, evitando “bloqueia tudo”.
- JSON de hook: confira status, parsing e exatamente um objeto. Erro de parsing não é ausência de bloqueio.
- Nunca mude teste apenas para fazê-lo passar. Se o contrato mudou, atualize a AC primeiro e explique.
- Template: make test. Não altere Git/identidade/ambiente do projeto real em fixtures. Nada de sleeps arbitrários para sincronização.
