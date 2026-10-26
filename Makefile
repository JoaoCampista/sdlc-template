.PHONY: help setup doctor sdd lint test check
help:
	@printf '%s\n' 'setup: instala hooks e gera índice' 'doctor: verifica ambiente sem alterar' 'sdd: atualiza índice + lint + drift' 'check: lint + drift + testes herméticos (sem gerar arquivos)'
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
test:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
check: lint
	bash scripts/sdd/spec-drift.sh
	$(MAKE) test

.PHONY: test-mutations
test-mutations:
	PYTHONDONTWRITEBYTECODE=1 python3 scripts/tests/mutation_checks.py
