# AGENTS.md — regras do repositório

Leia antes de planejar ou editar. O contexto e o fluxo estão em CLAUDE.md; os contratos em .specs/.
Instruções diretas do usuário definem escopo e autorização. Registre conflitos concretos; não invente novas aprovações.

## Regra 0 — Stack decidida por ADR
A stack do produto é definida em ADR-002 e Constitution §2 no bootstrap. As dependências do tooling (Bash, Git, jq, Python) não escolhem a stack do produto. Troca tecnológica pede decisão explícita; atualização de versão compatível pode ser revisão da ADR existente.

## Regra 1 — Use as bibliotecas diretamente
Não crie um framework sobre uma SDK madura. Abstração nova precisa resolver uma necessidade demonstrada; “não quero acoplar” não basta. Conversão necessária entre persistência e contrato de transporte não é, por si, um antipadrão.

## Regra 2 — Teste efeitos observáveis
Testes seguem ACs e comportamento. Dublês devem reproduzir recusas e saídas que a implementação trata. Um grep por uma chave ou a existência de um arquivo não prova o efeito. Para controles críticos, retire ou altere o controle numa cópia: o teste precisa falhar pelo motivo esperado.

## Regra 3 — Evite decisões circulares
“O código depende disso” não justifica uma decisão que criou essa dependência. Confronte alternativas e custo real.

## Regra 4 — Prefira a solução menor
Se uma solução simples preserva o contrato, simplifique. Registre reversões, causa e prevenção no ADR/postmortem aplicável.

## Regra 5 — Módulos seguem fronteiras reais
Novo módulo/pacote só por consumidor, ciclo de release ou dependência/plataforma distinta. Composição e funções pequenas antes de hierarquias genéricas.

## Regra 6 — Spec antes de código
Mudança de comportamento: spec primeiro, depois plan/tasks/risks; UI também exige design.md. Toda task aponta AC e evidência. Rode make sdd após mudar specs e versione o índice junto. F-SDD-TOOLING-V1 descreve o próprio template, não autoriza features do novo produto.

## Regra 7 — ADR é decisão, não ticket
Nova alternativa/trade-off transversal, quebra de contrato ou nova área → ADR. Endpoint, tabela ou DTO que seguem decisão existente → spec e referência à ADR. Extensão vai em Revisões; reversão ganha sucessora com supersedes. Reserve ADR-002 para stack.

## Regra 8 — Corrija a causa
Não silencie falha de teste, lint, parsing ou hook. Exceção precisa de justificativa de domínio, escopo e rastreabilidade. Agente não usa --no-verify nem define SDD_ALLOW_TRIVIAL para evitar controle.

## Regra 9 — Conheça o enforcement e seus limites
Hooks em .claude/settings.json são do Claude Code; outros clientes seguem estas regras e usam Git/checks. Inicie a sessão na raiz e confira se o contexto SDD apareceu. /sdd-status manual não prova disparo automático.

Guards de edição resolvem caminho real; código só com spec in_review/approved. Índice é gerado. Mudanças em hooks/settings/scripts/sdd/CI pedem avaliação pelo runtime: aproveite autorização já dada para o mesmo escopo, sem reabrir decisões à toa. A suíte precisa cobrir a mudança.

O guard Bash é heurístico, não sandbox: não avalia programas arbitrários ou scripts, nem cobre toda ferramenta MCP/terminal de outros clientes. Não use uma ferramenta não coberta para fugir de uma regra. Configure adaptadores da stack depois do bootstrap; veja docs/hooks.md.

## Regra 10 — Git e integração têm um responsável
Antes do primeiro commit, confira a identidade existente; não configure autor real por conta própria. Stage só por caminhos da tarefa; confira git diff --cached e git status. Commit lógico, Conventional Commits, trailer Spec-Hash do conteúdo staged. Não misture arquivos de outras sessões.

Push/PR seguem o destino e escopo solicitados pelo usuário; autorização persiste. “Continue” não inventa autorização para merge, deploy, apagar dados ou custo adicional. Confira o remoto do novo projeto: não publique código de produto no remoto upstream do template.

Se houver delegação autorizada: cada agente recebe spec/ACs, arquivos exclusivos, estado do Git e comandos. Revisores só leem. Um integrador confere o diff, valida uma vez por lote coeso e faz stage/commit; agentes não disputam o índice ou a spec ativa. Worktrees têm estado .sdd próprio e precisam de setup; recursos externos ainda podem ser compartilhados. Template de handoff em docs/templates/handoff.md.

## Regra 11 — Evidência atual
Contagens são derivadas, não copiadas de outro relatório. Registre commit, comando, resultado e limites. Task só vira done depois de conferir implementação e verificação; plano ou relato de agente não é evidência.

## Regra 12 — Feche o ciclo
- Três commits consecutivos na última hora sem .specs disparam reconciliação (heurística inclui docs e qualquer subsistema). Atualize tasks no commit da AC; não faça commit cosmético só para calar o aviso.
- Stop bloqueia drift ou reconciliação uma vez; na repetição informa sem criar loop. Isso não transforma pendência em conclusão.
- Autonomia vale para o escopo autorizado. G0/G1/G2 já autorizados não devem ser perguntados de novo. Não atribua “approved” ou aceite final ao humano sem evidência desse aceite.
- Fechamento, incidente, smoke e refresh relevante geram postmortem com spec gap, convenção descoberta e pendências com dono.
- Convenção repetida vira DS com teste/enforcement no mesmo commit.
- Memória e handoffs são contexto. Decisão durável vai ao repositório; nunca registre segredos na memória.
- Encerrou a tarefa: limpe .sdd/active-spec. Não deixe uma spec antiga liberar pedidos novos.

## Regra 13 — Convenções verificáveis
.specs/design-system é a camada de engenharia: arquitetura, contratos, testes, nomes, erros. Não confunda com design.md (tela/estado) ou biblioteca visual/tokens. DS descreve código existente e passa a orientar o próximo; não invente convenção sem exemplo e controle executável. Semente DS-00/06/07 no esqueleto do produto; padrão repetido amplia a biblioteca.

## Regra 14 — Fonte única dos contratos e gerados
Escolha no projeto a fonte canônica de DTOs, schemas, eventos e tokens. Consumidores importam ou geram a partir dela. Não edite gerados nem duplique contratos para “desacoplar”. Ferramentas que mantêm estado próprio (IDE/design) exigem fluxo próprio documentado.

## Regra 15 — Testes isolados por padrão
Suíte padrão sem rede, banco ou conta real. Integração é comando explícito, com destino de teste validado antes de conectar e orçamento de recursos. Banco/host/nome de variável declarados não provam qual destino o cliente resolveu. Não copie a política de dados de outro produto sem decidir a sua.

## Regra 16 — Dados e operações reais
Confirme autorização e destino efetivo antes de ação irreversível. Separar check/test/build de deploy, migração destrutiva, restauração e limpeza de volumes. Mensagens de erro não expõem valores de credenciais.

## Regra 17 — UI precisa ser vista
UI pronta exige build, inspeção das imagens por estado/variante e interação quando prevista nas ACs. Guarde evidência persistente com commit e revisão em design.md. Captura não prova teclado, leitor de tela ou foco dinâmico. Falha visual e pendência de acessibilidade permanecem abertas.

## Catálogo de aprendizados
Veja docs/learned-practices.md para práticas extraídas, evidência de origem e limites. Novos incidentes entram em postmortems; não importe datas, pessoas, exceções ou infra de outro projeto como regra universal.
