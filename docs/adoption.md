# Adoção e atualização

## Projeto novo

Crie seu próprio repositório pela função de template do GitHub ou pela cópia do conteúdo, incluindo pastas ocultas. Configure identidade e remoto adequados. Instale as dependências do tooling no ambiente; rode setup/check; só depois descreva produto e escolha stack.

Substitua owners genéricos e datas do bootstrap ao preencher seus documentos. Mantenha a proveniência da ADR-001; ADR-002 pertence à sua stack. F-SDD-TOOLING-V1 é contrato do método; não a use como spec ativa de uma feature de produto. O setup não ativa essa spec automaticamente.

Não copie `.sdd`, `.env`, settings.local, memória de agentes, worktrees ou credenciais de outro projeto. `.env.example` pode ser versionado com valores fictícios. Instale plugins e skills específicos apenas quando forem necessários, pela origem e licença adequadas.

## Projeto existente

1. Faça uma branch, leia regras locais e preserve trabalho de outras sessões.
2. Compare arquivos, não substitua .claude/ ou .specs/ em bloco. Seus contracts e ADRs têm prioridade como contexto do projeto.
3. Integre scripts/sdd, wrappers, hooks e testes como um conjunto; a nova base usa Python 3.9+. Verifique o README de cada atualização.
4. Se há hooks de outro sistema ou core.hooksPath, componha explicitamente o pipeline com o mantenedor; o instalador não sobrescreve.
5. Acrescente design.md às features de UI em andamento; não reescreva silenciosamente histórico concluído.
6. Rode make sdd, confira diff e index, depois make check. Rode smoke do cliente em clone temporário e verificações do produto.
7. Commit por escopo; publique no remoto do produto, não no upstream do template.

## Trabalho paralelo

Delegação só quando autorizada. Separe arquivos e defina um integrador. Numa árvore compartilhada, índice Git e active-spec também são compartilhados; agentes não alteram isso em paralelo. Uma worktree isola esses estados, mas porta, banco, simulador e credenciais podem continuar compartilhados: documente exclusão mútua e setup próprio.

Valide uma vez por lote coeso; falha ou mudança posterior exige verificação correspondente. Handoff especifica commit/diff exatos e evidência. “O agente disse que fez” não fecha task.

## Manutenção desta base

Use F-SDD-TOOLING-V1 para evoluir o próprio tooling; gere novas features apenas para contratos distintos. Mantenha PROD-001 em bootstrap pending e §2 da Constitution sem stack. Não publique spec de produto, token de design, domínio, conta ou exceção operacional local como default.

Checks: make sdd após mudanças canônicas; make check; revisão adversarial somente leitura; postmortem. CI confere sem gerar o índice, para detectar índice esquecido. Não reconfigure identidade de contribuidores nem faça merge/deploy implicitamente.
