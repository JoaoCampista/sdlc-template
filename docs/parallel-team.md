# Time paralelo: o pedido de uma frente e os riscos

Vale quando o humano autorizou delegação (AGENTS.md, Regra 10, "Time paralelo"). A sessão principal copia o preâmbulo abaixo para um arquivo de rascunho, troca o que está em maiúsculas e manda cada frente ler esse arquivo primeiro. Depois do preâmbulo, o pedido de cada frente traz o específico dela:
- as tasks e o levantamento (o que falta, com caminho:linha);
- a lista dos arquivos que são dela;
- os números ou nomes dos recursos que a sessão principal distribuiu (migrações, portas, banco de teste, pasta de build);
- as suítes e as travas a rodar.

## Como a sessão principal conduz

1. Com o levantamento por task na mão, divide as frentes sem arquivo em comum e dispara todas de uma vez. Enquanto elas codam, prepara a junção e a spec. Ao humano, um status curto.
2. Junta uma frente por vez, na ordem das dependências, à medida que chegam: índice limpo antes, nunca em laço, commit logo depois do verde.
3. Na junção, só o nível do meio: os herméticos do que mudou, o lint e `make junction-check`. A integração completa, `make check` e a revisão adversarial ficam para o marco.
4. Registra no mesmo push: o status de cada task, as bloqueadas que destravaram, as lacunas de spec que as frentes relataram.
5. Nenhuma onda termina com agente ou laço órfão; cada onda termina com algo visível.

## Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Duas frentes no mesmo arquivo | Lista de arquivos exclusivos por frente. Pontos de registro (lista de rotas, de migrações, catálogo) aceitam só acréscimo. Arquivo de outra frente vira extensão num arquivo novo |
| Recursos com o mesmo número ou nome | Saem da sessão principal: migrações, portas, bancos de teste |
| Uma frente usa o que outra cria | Injeção e prova hermética na frente; a integração de verdade fica para a junção, na ordem das dependências |
| A máquina não aguenta | Paralelismo de build limitado e pasta de build própria por frente; no máximo uma rodada pesada por vez na junção |
| Serviço compartilhado esgota (conexões, portas) | Um recurso de teste por frente; integração em grupos pequenos |
| Agente parado esperando aprovação | No estágio de desenvolvimento o guard não pergunta; fora dele, peça só o que o allow cobre e deixe o resto no relatório |
| Limite de sessão derruba as frentes | O trabalho fica na worktree; a frente é retomada de onde parou, nunca do zero |
| Base vermelha depois da junção | O nível da junção em toda junção; as travas de lista fechada rodam mesmo fora da lista da frente |
| Frentes lendo a spec diferente | A frente nunca edita a spec: relata a linha. Comportamento novo vai ao `produto`; contrato novo só com a spec antes |
| Qualidade sem revisor por frente | O caso do efeito em cada AC e a mutação nas paredes, dentro da frente; a revisão adversarial por marco |
| Sessão principal afogada em texto | Relatório curto e com forma fixa; dado longo vai em arquivo; transcrição de agente não se lê |
| Agentes escrevendo specs na árvore principal | Todo agente que escreve trabalha numa worktree; o pre-push confere o commit que sobe, não o disco; o índice gerado se refaz pelo script |
| A junção vira gargalo | A verificação roda na worktree da frente, depois de trazer a base; a junção fica com o diff, a spec e o commit |

---

## Preâmbulo do pedido

Você é uma frente de código do time paralelo deste projeto (AGENTS.md, Regra 10). Trabalha numa worktree própria, criada a partir da base, com TDD.

### Feature
F-ID, com spec, plan, tasks, risks e design.md em `.specs/features/F-ID/`. Leia antes o que o seu pedido cita, os contratos em `.specs/components/`, as ADRs e os DS aplicáveis.

### Regras
As de CLAUDE.md e AGENTS.md valem. Destaco:
- **Guard.** Antes de editar, rode a sonda `git add -f __hook_probe_inexistente__` e anote se veio a negação. Sem ela, as regras valem do mesmo jeito.
- **Contrato.** DTO, rota, schema e evento ficam só na fonte canônica do projeto. Precisa de um que a spec não tem? Pare esse item e ponha no relatório.
- **Testes.** Herméticos por padrão. A integração usa só o recurso de teste que o pedido nomeia, pelo comando do projeto; nunca ligue a integração à mão nem aponte para outro destino.
- **Build.** Na PASTA DE BUILD do pedido, nunca na da árvore principal.
- **Arquivos.** Toque só nos do seu pedido. Ponto de registro: só acréscimo, sem mover nem reformatar. Arquivo de outra frente: extensão num arquivo novo, e diga no relatório.
- **Edição.** Só por Edit ou Write. A mutação vai pelo Edit, com a reversão, ou numa cópia fora do repositório.
- **O que não é seu.** Sem commit, push, `git add` nem `.sdd/`. Não edite `.specs/`, `.claude/`, `scripts/sdd/` nem `.github/`. Lacuna de spec vai ao relatório, com a linha.
- **Operação.** Nenhum deploy, apply ou comando de nuvem. Nada de janela ou simulador se o humano está usando a máquina.
- **O que rodar.** As suítes herméticas que tocou, o lint, `make junction-check` e as travas que o pedido cita, com a saída num arquivo. Nada de `make check` inteiro nem da integração completa: são do marco. Falha que só aponta arquivo fora da sua lista vai ao relatório, sem conserto.
- **Ritmo.** Trabalhe direto: decida como sênior e registre a decisão no relatório. Comando negado pelo guard: siga sem aquele passo e deixe o pedido no relatório.

### Pronto quando
- cada AC do pedido tem um caso que falha sem a linha que a implementa; nas paredes (autorização, cripto, trava, guard), a mutação feita e desfeita;
- as suítes tocadas e o lint passam na worktree, e a junção não acusa arquivo da sua lista.

### Relatório final
Curto (uns 5.000 caracteres):
- o que fez por AC, com arquivo:linha e o nome do teste;
- as mutações das paredes e o resultado de cada uma;
- os comandos rodados, com a saída resumida;
- o que ficou de fora, e por quê; as lacunas de spec, com a linha;
- a lista exata dos arquivos tocados.
