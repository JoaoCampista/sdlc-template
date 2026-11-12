.PHONY: help setup doctor sdd lint test check _check check-verdict test-mutations harness painel junction-check codex-hooks
help:
	@printf '%s\n' 'setup: instala hooks e gera índice' 'doctor: verifica ambiente sem alterar' 'sdd: atualiza índice + lint + drift' \
	  'check: o portão do marco (lint + drift + testes herméticos, sem gerar arquivos); grava o veredito em .sdd/check-verdict' \
	  'check-verdict: mostra o último veredito e se ele é do HEAD' 'junction-check [BASE=origin/main]: na junção, só as travas que leem o que mudou' \
	  'harness [HORAS=24] [JSON=1]: mede o harness pelo registro de cada rodada de hook' 'painel: tasks por estado, clarificações e pendências' \
	  'test-mutations: contraprovas em cópias temporárias' 'codex-hooks: instala o adaptador do Codex (.codex/hooks.json)'
setup:
	bash scripts/setup.sh
doctor:
	bash scripts/doctor.sh
sdd:
	bash scripts/sdd/spec-lint-all.sh
	bash scripts/sdd/spec-index.sh
	bash scripts/sdd/spec-drift.sh
lint:
	bash scripts/sdd/spec-lint-all.sh
	@find scripts .claude/hooks -name '*.sh' -exec bash -n {} \;
	python3 -m json.tool .claude/settings.json >/dev/null
	python3 -m json.tool .claude/harness.json >/dev/null
test:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
# O veredito só é gravado por uma rodada que terminou; make -n, -t, -q e -i não gravam.
check:
	@bash scripts/sdd/check-verdict.sh run $(MAKE) --no-print-directory _check
_check: lint
	bash scripts/sdd/spec-drift.sh
	$(MAKE) test
check-verdict:
	@bash scripts/sdd/check-verdict.sh show
test-mutations:
	PYTHONDONTWRITEBYTECODE=1 python3 scripts/tests/mutation_checks.py
harness:
	@bash scripts/sdd/harness-report.sh $(if $(HORAS),--horas $(HORAS),) $(if $(JSON),--json,)
painel:
	@bash scripts/sdd/painel.sh
junction-check:
	@bash scripts/sdd/junction-check.sh $(or $(BASE),origin/main)
codex-hooks:
	bash scripts/sdd/install-codex-hooks.sh
