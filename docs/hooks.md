# Hooks: contrato, cobertura e limites

Configuração do Claude Code: .claude/settings.json. Dependências: Bash e Python 3.9+; lint-all também usa jq. O setup instala wrappers Git versionados por scripts/sdd/install-git-hooks.sh. Não copie arquivos à mão para .git/hooks.

| Evento | O que confere | Resposta |
|---|---|---|
| SessionStart | Produto/feature ativa, drift, fechamento anterior e escapes | Contexto curto; não instala nem executa serviços |
| PreToolUse Edit/Write/MultiEdit/NotebookEdit | Caminho real; spec ativa; índice gerado; Git/enforcement | Objeto JSON com deny/ask ou objeto vazio |
| PreToolUse Bash | Escritas simples, alguns comandos Git/destrutivos, execução opaca | deny/ask ou objeto vazio; não executa o comando inspecionado |
| PostToolUse Edit/Write/MultiEdit | Lint do documento e reconstrução do índice | Falhas propagadas com exit 2, diagnóstico stderr |
| PreToolUse Edit/Write (revisor) | Caminho real da escrita do spec-reviewer | deny fora da memória dele e da cópia de mutação |
| PreToolUse SendMessage | Destino da mensagem de um subagente | deny se não for "main" |
| Pre/PostToolUse Agent, Task, SendMessage | Pedido a um subagente de papel | Sem decisão; grava a marca quando o pedido rodou |
| Stop | Drift e sequência de commits sem specs | JSON block; repetição retorna {} e diagnóstico stderr |
| Stop (governança) | Product-spec, Constitution e clarificações desde a marca | block com os achados; sem achado, a marca avança |
| Stop (papéis) | Caminhos de cada papel desde o último pedido ao subagente | block; inerte sem caminhos em harness.json |
| Stop (infra) | IaC commitada depois do último apply registrado | block uma vez por achado; inerte sem raízes |
| Git pre-commit | Specs e índice de snapshot do stage, com validators staged | Falha impede commit |
| Git prepare-commit-msg | Spec ativa presente no stage | Atualiza Spec-Hash e preserva refs adicionais |
| Git commit-msg | Conventional Commits | Falha impede commit |
| Git pre-push | Snapshots das revisões locais anunciadas no protocolo Git | Falha impede push; exclusão de ref não tem árvore para validar |

Todos passam por .claude/hooks/_run.sh, que grava uma linha por rodada em .sdd/harness/ (decisão, motivo mascarado, alvo, tempo). O registro é medição local, fora do Git: não é trilha de auditoria nem guarda o comando. `make harness` lê.

## Configuração do projeto

.claude/harness.json (é enforcement: só a sessão principal edita):

| Chave | Conteúdo | Vazio significa |
|---|---|---|
| roles.NOME.paths | Pathspecs do Git cujo desenho o subagente NOME mantém; `pedido` é o texto do bloqueio | A trava do papel fica inerte |
| infra_roots | `{name, dir, exclude?, suffixes?}` por raiz de IaC | A trava de infra fica inerte |
| fences | `{name, run (argv), paths}`: as travas que `make junction-check` roda quando um arquivo dos caminhos muda | Nada roda na junção |
| long_runs | Alvos do make que não podem ir num pipe sem tee | Usa o padrão |

.claude/deploy-stage.json: `{"stage": "desenvolvimento"}` liga o estágio em que o guard não pergunta; ausente ou qualquer outra coisa é beta. O arquivo não vem no template, e criá-lo ou mudá-lo pede o humano.

O script de apply do projeto chama `bash scripts/sdd/infra-sync.sh mark PASTA` depois de um apply que deu certo; sem isso a trava de infra só destrava por ack.

## Codex

`make codex-hooks` grava .codex/hooks.json apontando para scripts/sdd/codex-hook.sh, que traduz SessionStart, Bash, apply_patch e Stop para os mesmos guards (como agent_type "codex": nunca edita o enforcement) e transforma pergunta em negação. Um hooks.json diferente é preservado. A tradução é testada com fixtures; o disparo no cliente real é verificação de adoção, não coberta aqui.

## O que isso não prova

- O lint lê um subconjunto de frontmatter (campos escalares de primeiro nível; listas inline são mantidas como texto). Não é um parser YAML geral nem um avaliador semântico de ACs. Use os formatos dos templates.
- Drift compara os documentos canônicos e seus metadados/hashes; não compara a intenção da spec com cada linha de código.
- Spec ativa válida não prova que a edição está dentro de suas ACs nem autentica aprovação humana. A revisão continua necessária.
- Guard Bash não é sandbox, não executa expansão de shell e não lê todos os scripts. Comandos opacos e construções dinâmicas detectadas pedem avaliação; flags alternativas, programas personalizados e ferramentas MCP podem exigir cobertura adicional. Use permissões nativas do cliente e os checks Git/CI.
- Hooks de .claude não são instalados automaticamente no Codex ou em outro cliente; o adaptador do Codex é opcional. Nenhum adaptador de MCP da stack é presumido.
- As travas do Stop comparam caminhos e marcas, não o conteúdo do desenho: chamar o subagente avança a marca mesmo que ele erre. O "conferido" registra o motivo, não o prova.
- A identificação de subagente depende de agent_id/agent_type no payload do cliente, e a cópia de mutação do revisor depende de scratchpad_dir; sem esses campos o guard nega a mais, nunca a menos, no revisor, mas trata a chamada como sessão principal nos demais.
- O spec-reviewer "só lê" por guard apenas em Edit/Write; pelo Bash vale o guard Bash comum e o texto do agente.
- O estágio de desenvolvimento troca pergunta por registro: é para ambiente sem dado real. O guard não sabe o que há no ambiente.
- A validação executa scripts versionados do snapshot. Como CI/testes normais, não é isolamento para código hostil; revise mudanças nos próprios validators.
- Git hook local pode ser contornado por uma pessoa. CI e revisão do PR também importam.

## Verificar adoção

1. `make setup` e `make doctor` na raiz. Setup funciona com .git diretório ou arquivo de worktree; recusa hook de terceiro/core.hooksPath sem mexer neles.
2. Abra uma nova sessão do Claude Code na raiz. Confira o contexto “Estado SDD” e o cadastro dos hooks no cliente. Executar /sdd-status à mão só testa o script.
3. Sonda inofensiva no Bash do cliente: `git add -f __hook_probe_inexistente__`. Com guard deve haver deny antes do Git; erro de pathspec sozinho indica que o guard não bloqueou. O comando não deve apontar arquivo existente.
4. Em clone temporário, exercite Write sem spec, mudança em harness (ask), PostToolUse e Stop. Registre versão do cliente, evento e saída; não diga que smoke real passou só porque testes unitários passaram.

A referência de formatos é a [documentação oficial de hooks do Claude Code](https://code.claude.com/docs/en/hooks); escopo de arquivos está em [settings](https://code.claude.com/docs/en/settings), consultados em 2026-10-26. Configurações gerenciadas pelo ambiente podem adicionar restrições.

## Contraprovas reproduzíveis

`make test-mutations` trabalha em cópias temporárias: remove o guard, quebra o JSON do Stop, adiciona timestamp ao índice e remove a validação do stage. Cada caso exige que a regressão correspondente detecte o defeito. Isso testa as proteções concretas, não certifica o sistema inteiro.

## Extensões

Após ADR-002, acrescente formatador e MCPs da stack com testes do matcher e do payload real. Ferramenta sem caminho pode alterar código/configuração: não presuma que seja leitura. Formatação deve falhar de modo visível, sem engolir erro.

Escape SDD_ALLOW_TRIVIAL só para sessão excepcional iniciada pelo humano, com mudança trivial já coberta e registro do motivo. Não o coloque no template ou ligue por iniciativa do agente. A sessão anuncia seu uso.
