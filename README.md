# SDLC Template — spec antes de código

Base de templates, instruções e verificações para iniciar projetos com desenvolvimento dirigido por especificação (SDD). Evolui o método do ai-4sdlc-platform (CEIA/UFG) com aprendizados do uso no Spectrolite, sem herdar sua stack ou seu produto.

## Começar

Use **Use this template** no GitHub, ou copie o conteúdo para um novo repositório. Para estudar/manter esta base:

```bash
git clone https://github.com/JoaoCampista/sdlc-template.git
cd sdlc-template
bash scripts/setup.sh
make check
claude
```

Requer Bash 3.2+, Git, jq e Python 3.9+ (biblioteca padrão; sem instalar pacotes Python). `make` facilita os comandos. macOS e Linux são os alvos do tooling; Windows/WSL não foi validado nesta evolução.

Para criar um produto, descreva o caso. O fluxo define produto → stack por ADR-002 → esqueleto → features. Configure identidade e remoto do **seu** projeto antes de commitar/publicar. Setup não configura identidade, instala dependências, cria commits, limpa trabalho local nem troca remotos.

## O que vem na base

| Caminho | Uso |
|---|---|
| .specs/features/_TEMPLATE/ | spec, plan, tasks, risks e **design.md** por estado |
| .specs/components/_TEMPLATE/ | Contratos internos com ciclo próprio |
| .specs/adr/ e constitution/ | Decisões e invariantes; stack continua em aberto |
| .specs/design-system/ | Convenções de engenharia com enforcement; não é biblioteca visual pronta |
| .specs/postmortems/ | Aprendizados com evidência, spec gap e pendências |
| .claude/hooks/ | Sessão, guard de edição, guard Bash, pós-edição e Stop |
| .claude/rules/, skills/, agents/ | Regras por caminho, comandos de trabalho e revisor somente leitura |
| scripts/sdd/ | Índice determinístico, lint, drift e Git hooks que conferem stage/revisão enviada |
| scripts/tests/ | Regressões herméticas com repositórios temporários |
| docs/templates/ | Handoff e relatório de revisão reutilizáveis |

F-SDD-TOOLING-V1 é a spec das ferramentas distribuídas, não uma feature do seu produto; mantenha-a enquanto usar esse tooling. O PROD-001 ainda precisa do bootstrap. `.sdd/active-spec` e configurações locais são ignorados pelo Git.

## Uso diário

```bash
make doctor  # ambiente e instalação
make sdd     # depois de mudar specs: lint + gerar índice + drift
make check   # validação sem regenerar o que está sendo validado
```

Fluxo: `/spec-new` → contrato e decisões → implementação por AC → testes → revisão → `/postmortem`. UI tem design.md, referência por estado e evidência visual persistente. Specs passam de draft para in_review para implementar; approved é aceite final registrado.

Os hooks automáticos são configurados para Claude Code. Codex e outros clientes usam AGENTS.md, comandos e Git hooks; não presuma que carreguem .claude/settings.json. Guard Bash é uma ajuda ao processo, **não uma sandbox**.

## Guias

- [Adoção e atualização de projetos existentes](docs/adoption.md)
- [Práticas encontradas: origem, generalização e limites](docs/learned-practices.md)
- [Hooks: cobertura, teste de disparo e limitações](docs/hooks.md)
- [Design, estados e evidências](docs/design.md)
- [Padrões opcionais por tipo de projeto](docs/optional-patterns.md)

A CI executa make check em Linux e macOS. Ela valida o template; cada produto acrescenta build, testes e integração próprios. Verificação estrutural ou hash consistente não prova que todas as ACs foram implementadas.
