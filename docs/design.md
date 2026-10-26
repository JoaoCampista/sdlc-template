# Design que acompanha a implementação

Há três coisas diferentes: spec descreve comportamento; design.md liga estados a decisões e evidências visuais; .specs/design-system registra convenções de engenharia verificáveis. Biblioteca visual e tokens têm fonte própria escolhida pelo projeto.

Copie design.md junto da feature. Se não existe UI, marque applicable: false e justifique. Se existe, mapeie cada estado e variante relevante, inclusive erro, vazio, carregamento, recuperação e acessibilidade. Plataforma/tema/idioma são dimensões da tabela, não pastas obrigatórias.

A referência pode ser Figma, outro editor ou artefato local versionado. Use links de frames específicos e a versão da spec lida. Não trate captura sem versão como verdade permanente. Para cada componente, registre qual implementação existente o representa e quais tokens consome.

Antes de codificar, registre divergências: comportamento/texto segue a spec; aparência segue a referência visual aceita. Se as duas não explicam uma decisão relevante, registre lacuna e resolva com o responsável; não invente comportamento.

Antes de concluir, construa, execute e inspecione as imagens. Salve em docs/images/F-ID-estado-variante.png ou no armazenamento de evidência escolhido pelo time, com link persistente, commit, resultado, revisor e data. Não coloque credenciais ou dados de clientes nos prints. Confira que a imagem mostra o estado e build certos.

Uma árvore de acessibilidade ou screenshot não prova teclado, foco durante transições ou leitor de tela. Execute os testes interativos previstos e declare o que não foi verificado. Uma task pode estar implementada e continuar pendente de validação visual.

Previews reproduzíveis usam dados fictícios e estado injetado, sem depender de rede ou operação assíncrona para chegar à tela certa. Separe recomendações de plataforma das regras normativas do produto e marque fonte, versão e incerteza. O comando /design-review orienta essa conferência; adaptadores específicos seguem docs/templates/stack-adapter.md.
