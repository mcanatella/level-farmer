.PHONY: lint mypy

lint:
	black . --check

mypy:
	mypy .
