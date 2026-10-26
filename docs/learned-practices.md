# Aprendizados do uso real e o que entrou no template

Leitura feita em 2026-10-26. Base anterior: sdlc-template `38761f5`. Projeto observado: Spectrolite, HEAD `053bc8e5db5ee7bf1332c9fd172bbf48e2fe555c` no início da leitura. Havia alterações locais em andamento; nenhum setup, build, teste ou edição foi executado nele. As referências abaixo são caminhos no projeto de origem, sem transportar seu conteúdo de produto.

“Funcionou” aqui significa que há implementação, testes ou relato de execução no repositório observado. Não significa que reexecutamos toda a aplicação ou que o padrão sirva para qualquer produto. O tooling adaptado tem verificação própria em scripts/tests/.

## Práticas incorporadas à base

| Prática | Evidência no projeto observado | Generalização aplicada |
|---|---|---|
| Design como contrato por estado | features/_TEMPLATE/design.md e designs de features | design.md com versão da spec, referência, estados, variantes, componentes, texto e evidência; sem plataformas fixas |
| Separar comportamento de aparência | design.md e guia de construção de telas | Spec governa fluxo/texto; referência visual governa aparência; divergência fica registrada |
| UI pronta só após ser vista | AGENTS Regra 18; PM-feature-close-2026-10-23 | Captura persistente, imagem inspecionada, commit/revisor; interação e acessibilidade são verificações distintas |
| Tasks têm estado verdadeiro e prova | PM-feature-close-2026-10-23, tarefas dadas como feitas sem implementação | Coluna de evidência; verificar código/teste antes de done; deferimento com dono |
| Testes cobrem efeito, não só forma | PM-incident-2026-10-19 e AGENTS antipadrões | Contraprovas para proteção; regex/contagem isolada não prova comportamento |
| Dublês reproduzem recusas | DS-06 R9 e postmortems de deploy | Testar código de saída, mensagem e conteúdo de erro; proibir falso “aceita tudo” sem justificativa |
| Guard decide pelo caminho efetivo | _hook-lib.sh, pre-edit-guard.sh e hooks.test.sh | Resolver cwd, .. e symlinks; worktree irmã usa sua própria sessão |
| Guard Bash complementa Edit/Write | bash-guard.sh | Versão conservadora para escrita simples, bypass Git e operações sensíveis; execução opaca pede avaliação |
| Enforcement também é código revisável | AGENTS Regra 9; PM-enforcement-edit-2026-10-21 | Mudança em settings/hooks/SDD/CI é identificada; diff e regressões; autorização já dada continua válida |
| Falha de controle não libera operação | pre-edit-guard.sh e hooks.test.sh | Entrada inválida/falta de runtime → exit 2; status da spec em lista explícita |
| PostToolUse não engole falha do índice | post-spec-edit.sh | Erro de lint/ID duplicado chega ao agente com exit 2 |
| Stop tem protocolo, não só exit 0 | PM-stop-hook-2026-10-21 | Um objeto JSON, stderr para diagnóstico, bloqueio com motivo e proteção contra loop |
| Contexto de início explica pendências | session-start.sh | Bootstrap pendente, spec ativa, escopo, fechamento anterior, escape e drift; sem rede/build no início |
| Disparo real é diferente de execução manual | AGENTS Regra 9 | /sdd-status não prova hooks ativos; guia de sonda inofensiva no cliente real |
| Índice determinístico | spec-index.sh; spec-index.test.sh | Sem timestamp variável; ordem estável; não regravar sem mudança |
| Commit confere o stage | git-pre-commit.sh, revisões de 2026-10-25 | Snapshot com validators staged; trabalho fora do stage não altera o resultado |
| Trailer corresponde à spec commitada | git-prepare-commit-msg.sh | Hash staged, atualização no amend, preservação das referências de tasks/ACs |
| Setup preserva trabalho local | setup.sh e setup.test.sh | Idempotência, worktree, estado ativo preservado; sem commit/identidade automáticos |
| Revisor não é implementador | agents/spec-reviewer.md | Somente leitura; inclui untracked, testa hipóteses e informa o que não executou |
| Revisão em lentes e contraprova do conserto | AGENTS padrões positivos; PM-incident-2026-10-19 | Consistência, usuário novo, hooks/segurança e stack; procurar variantes da mesma família após corrigir |
| Lotes têm integrador | PM-feature-close-2026-10-23 | Validar por lote coeso, sem builds concorrentes sobre o mesmo recurso; agente não commita trabalho alheio |
| Handoff autocontido | AGENTS fluxo entre construtor, design e auditor | Template com commit, spec, ACs, arquivos, evidência, pendências e responsável; sem nomes/canais fixos |
| ADR é decisão transversal | CLAUDE fluxo; AGENTS Regra 7 | Novo endpoint/tabela que segue decisão existente não gera ADR nova |
| DS surge de padrão comprovado | DS-00/06/07; DS-03 e DS-11; skill ds-new | Snapshot real, regra verificável, enforcement no mesmo commit; engenharia separada do design de tela |
| Testes herméticos e integração explícita | AGENTS Regra 16; DS-06 | Suíte padrão sem serviços; validar destino efetivo antes de integração; recurso de teste isolado |
| Memória não vira autoridade paralela | AGENTS 12.7 | Decisões duráveis nas specs/ADRs; memória não substitui contrato e não recebe segredos |
| Fechamento encerra autorização da spec antiga | antipadrão do setup em AGENTS | Limpar active-spec; aviso quando existe postmortem de fechamento |
| Postmortem fecha o aprendizado | postmortems e skill postmortem | Spec gap + convenção + evidência + pendência com dono; sem números copiados |

## Melhorias adicionais ao generalizar

A cópia literal perpetuaria algumas lacunas. Esta adaptação também:

- Aceita somente in_review/approved para implementar: status desconhecido, vazio ou deprecated não libera código.
- Gera índice de forma atômica e não substitui índice válido quando detecta duplicata.
- Verifica a revisão realmente enviada no pre-push, em vez de uma árvore local que pode estar diferente.
- Preserva hooks de terceiros e core.hooksPath em vez de sobrescrevê-los silenciosamente.
- Retira permissões amplas de npm, Python, Docker e outros runtimes ainda não escolhidos.
- Conta a sequência recente de commits sem spec, para um commit antigo de spec não esconder uma sequência posterior.
- Evita dependências de modelos, plugins, paths pessoais e adaptadores de ferramentas específicas.

## Padrões bons, mas opcionais

Há evidência útil para contratos compartilhados, exemplos de contrato imutáveis, migrações que só crescem, tokens gerados de uma fonte, erros tipados sem segredos e comandos administrativos que validam o papel real da conexão. O princípio é reutilizável; a implementação depende da arquitetura. Os roteiros estão em optional-patterns.md, sem DS normativo inventado para código que o usuário ainda não escreveu.

## O que ficou fora

| Específico da origem | Por que não vira padrão universal |
|---|---|
| Swift/SwiftUI/Vapor, versões Apple, pacotes e DTOs do produto | Stack e fronteiras devem ser escolhidas em ADR-002 |
| Ferramentas Xcode, exportação apple-* e regras de pbxproj | Só projetos Apple têm esse ciclo; documentar adaptador se adotado |
| AWS/Cognito/KMS, infraestrutura em máquinas específicas, scripts de deploy e políticas locais | Exigem contas, ambientes, segurança e operação próprios |
| Banco, papéis, prefixos, filas, RLS e catálogo de erros do produto | Contratos e domínio específicos; só os princípios foram extraídos |
| Biblioteca Figma, IDs, textos, cores, tokens e screenshots | Identidade e material de produto não pertencem ao template |
| Nomes de pessoas/agentes, chats e pastas de handoff locais | Papéis e protocolo são reutilizáveis; endereços e identidades não |
| enabledPlugins e settings.local | São decisões de ambiente, não dependências implícitas do template |
| Revisão após push e CI desligada | Escolha circunstancial de ritmo/custo; base mantém revisão antes da entrega e CI ativa |
| Exceções temporárias para ler segredos ou liberar deploy em desenvolvimento | Autorização localizada no tempo e no projeto; nunca herdada |
| Proibição universal de worktrees | A origem dependia de estado local não versionado; a base suporta setup e estado próprios por worktree |

## Limites de evidência

A existência de um teste ou postmortem no Spectrolite não equivale a prova atual de todos os caminhos. Parte dos controles é heurística; algumas revisões de acessibilidade na origem usaram capturas/árvores sem exercitar tecnologia assistiva. A adaptação exige dizer isso explicitamente. O teste automatizado do script também não prova que Claude Code o carregou: o smoke do cliente real segue sendo verificação de adoção.

## Organização das instruções em .claude

A leitura das skills de design e desenvolvimento e das regras por camada também mostrou práticas reutilizáveis:

- **Regras por caminho:** UI, contrato compartilhado, backend, infraestrutura e testes carregam instruções próprias, reduzindo contexto irrelevante. A base inclui regras de design/tooling/testes; o usuário adiciona as da sua stack.
- **Skills com referências por tema:** um índice curto aponta detalhes de movimento, acessibilidade, plataforma e materiais. O formato é reutilizável; as recomendações Apple não são default universal.
- **Proveniência e incerteza explícitas:** a skill de design separa regra do produto, recomendação, API disponível e afirmação não confirmada. Isso evita transformar conselho ou lembrança em lei.
- **Revisor da stack complementa revisor da spec:** um confere semântica/contrato, outro peculiaridades do runtime e framework. O revisor especializado deve nascer depois da escolha da stack.
- **Previews determinísticos por estado:** dados fictícios e estado injetado evitam que a imagem dependa de rede ou tarefa assíncrona. O padrão entra no guia de design, sem copiar a implementação Swift.

O roteiro reutilizável está em templates/stack-adapter.md e a revisão visual em .claude/skills/design-review/SKILL.md.
