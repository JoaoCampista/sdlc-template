# Hooks: contrato, cobertura e limites

Configuração do Claude Code: .claude/settings.json. Dependências: Bash e Python 3.9+; lint-all também usa jq. O setup instala wrappers Git versionados por scripts/sdd/install-git-hooks.sh. Não copie arquivos à mão para .git/hooks.

| Evento | O que confere | Resposta |
|---|---|---|
| SessionStart | Produto/feature ativa, drift, fechamento anterior e escapes | Contexto curto; não instala nem executa serviços |
| PreToolUse Edit/Write/MultiEdit/NotebookEdit | Caminho real; spec ativa; índice gerado; Git/enforcement | Objeto JSON com deny/ask ou objeto vazio |
| PreToolUse Bash | Escritas simples, alguns comandos Git/destrutivos, execução opaca | deny/ask ou objeto vazio; não executa o comando inspecionado |
| PostToolUse Edit/Write/MultiEdit | Lint do documento e reconstrução do índice | Falhas propagadas com exit 2, diagnóstico stderr |
| Stop | Drift e sequência de commits sem specs | JSON block; repetição retorna {} e diagnóstico stderr |
| Git pre-commit | Specs e índice de snapshot do stage, com validators staged | Falha impede commit |
| Git prepare-commit-msg | Spec ativa presente no stage | Atualiza Spec-Hash e preserva refs adicionais |
| Git commit-msg | Conventional Commits | Falha impede commit |
| Git pre-push | Snapshots das revisões locais anunciadas no protocolo Git | Falha impede push; exclusão de ref não tem árvore para validar |

## O que isso não prova

- O lint lê um subconjunto de frontmatter (campos escalares de primeiro nível; listas inline são mantidas como texto). Não é um parser YAML geral nem um avaliador semântico de ACs. Use os formatos dos templates.
- Drift compara os documentos canônicos e seus metadados/hashes; não compara a intenção da spec com cada linha de código.
- Spec ativa válida não prova que a edição está dentro de suas ACs nem autentica aprovação humana. A revisão continua necessária.
- Guard Bash não é sandbox, não executa expansão de shell e não lê todos os scripts. Comandos opacos e construções dinâmicas detectadas pedem avaliação; flags alternativas, programas personalizados e ferramentas MCP podem exigir cobertura adicional. Use permissões nativas do cliente e os checks Git/CI.
- Hooks de .claude não são instalados automaticamente no Codex ou em outro cliente. Nenhum adaptador de MCP da stack é presumido.
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
