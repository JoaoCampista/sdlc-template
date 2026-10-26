# CLAUDE.md — contexto para trabalhar com o template

.specs é a fonte dos contratos; AGENTS.md define as regras. Este repositório distribui um método, sem escolher a stack do produto. A F-SDD-TOOLING-V1 documenta o mecanismo distribuído.

## Primeiro uso
Rode `bash scripts/setup.sh` na raiz. O comando instala wrappers Git, confere specs, gera o índice e cria estado local se ausente; não instala dependências, cria commit, troca remoto, altera identidade ou zera spec ativa. Se já existirem hooks de outro sistema ou core.hooksPath, preserve-os e faça integração explícita.

Dependências: Bash 3.2+, Git, jq e Python 3.9+ (sem pip). `make doctor` confere ambiente. Abra o Claude na raiz e verifique SessionStart; uma sessão iniciada em outra pasta pode não ter estes hooks. Outros agentes leem AGENTS.md e rodam os checks, sem presumir hooks do Claude.

## Ordem de leitura
1. AGENTS.md e Constitution.
2. Product spec e ADRs relevantes.
3. DS aplicável; feature ativa com spec, plan, tasks, risks e design quando UI.
4. Estado do Git e resultado real das verificações anteriores.

## Comandos
| Comando | Efeito |
|---|---|
| make setup | Instala tooling do clone, preservando estado existente |
| make doctor | Confere dependências, hooks e drift; não prova disparo do cliente |
| make sdd | Lint, reindexação explícita e drift |
| make check | Lint, drift e testes do tooling; não reescreve índice |
| make test | Testes herméticos de hooks, Git e templates |

No bootstrap, amplie check com build/lint/testes do produto e crie comando separado de integração. Não coloque deploy ou operações destrutivas em check.

## Bootstrap do produto
1. Entenda público, problema, fronteiras e dados. Pergunte só o que muda o desenho; use contexto já disponível e registre premissas.
2. Preencha PROD-001; G0 confirma o produto. `bootstrap: pending` passa para `complete` após esse aceite.
3. ADR-002 escolhe stack, com alternativas e custos; G2. Preencha Constitution §2 e os comandos do produto. Dependências Python do tooling não obrigam produto Python.
4. F-SETUP-V1 especifica esqueleto, primeiro teste, lint/build, CI e a semente DS-00/06/07. G1 → in_review e spec ativa → código.
5. Descreva no DS o esqueleto real e os controles que já existem. Valide, revise e feche com postmortem.

## Fluxo de uma feature
1. `/spec-new`: spec/plan/tasks/risks; design.md se UI (ou não aplicabilidade explícita). ACs verificáveis com @test:caminho. G1 usa autorização já existente no escopo; registre sua origem. in_review libera implementação, não significa aceite final.
2. Decisão arquitetural nova → `/adr-new` e G2. Extensão de padrão existente fica na spec/Revisões da ADR; não gere uma ADR por endpoint.
3. Leia o DS; identifique fronteiras, fonte dos contratos e riscos. Design mapeia cada estado para referência e evidência esperada.
4. Teste comportamento antes do conserto; implemente o mínimo; rode testes. Controles críticos também precisam de contraprova (remover a proteção em uma cópia faz o teste falhar). Dublês reproduzem erros reais. Atualize tasks com evidência no commit da AC.
5. Revisão adversarial por subagente `spec-reviewer`, somente leitura, antes do commit final/PR. Confira também arquivos não rastreados. Reproduza achados; depois ataque variantes da mesma família de defeito. Não afirme que uma revisão independente ocorreu se ela não ocorreu.
6. `make check` e verificações do produto aplicáveis. Integração explícita; UI vista e evidências persistidas. “Não executado” e “falhou” não são verde.
7. `/postmortem`: spec gap, convenção descoberta, evidências verificadas e pendências com dono. Só marque tasks done com comprovação.
8. Limpe .sdd/active-spec. Aceite final/approved só com autorização registrada. Resuma entrega, verificação e limites. Push/PR conforme pedido vigente; merge/deploy não são consequência automática.

## Gates e autonomia
G0 = produto; G1 = contrato de implementação; G2 = decisão arquitetural. Este template usa esses nomes operacionais, não a numeração inteira do framework acadêmico. A instrução do humano pode autorizar esses gates para a tarefa; preserve autorização entre turnos. “Siga sem parar” não expande o escopo para ações irreversíveis não pedidas. Aprovação de produto não substitui resultado de teste, nem “in_review” substitui aceite final.

## Playbooks
| Demanda | Sequência |
|---|---|
| Bug | AC violada → regressão reproduzida → correção mínima → verificação → postmortem proporcional |
| Refactor | Contrato mudou? spec primeiro. Sem mudança de comportamento, use spec vigente e testes existentes |
| Drift / código legado | /sdd-reconcile: derive verdade do código, compare spec, revise independentemente |
| Convenção repetida | /ds-new: exemplo real + regra verificável + controle no mesmo commit |
| UI | design.md por estado → implementação → build + inspeção + interação → evidência/revisão |
| Incidente / operação real | Destino e autorização → procedimento rastreado → evidência → postmortem e prevenção |

## Limites importantes
Guard Bash é heurístico e não lê todo programa executado. MCPs e outros clientes precisam de adaptadores. Detalhes: docs/hooks.md. Nunca use outra ferramenta para burlar regra. Memória é contexto, repositório é contrato. Templates ficam sem dados do projeto de origem; docs/learned-practices.md explica o que foi generalizado.
