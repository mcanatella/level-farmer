.PHONY: lint mypy isort

lint:
	black . --check

mypy:
	mypy .

isort:
	isort . --check-only --diff
