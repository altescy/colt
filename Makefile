PWD      := $(shell pwd)
PYTHON   := uv run python
PYTEST   := uv run pytest
RUFF     := uv run ruff
PYRIGHT  := uv run pyright
MODULE   := colt

.PHONY: all
all: format lint test

.PHONY: test
test:
	PYTHONPATH=$(PWD) $(PYTEST)

.PHONY: lint
lint:
	PYTHONPATH=$(PWD) $(RUFF) check
	PYTHONPATH=$(PWD) $(PYRIGHT) $(MODULE)

.PHONY: format
format:
	PYTHONPATH=$(PWD) $(RUFF) check --select I --fix
	PYTHONPATH=$(PWD) $(RUFF) format

.PHONY: clean
clean: clean-pyc clean-build

.PHONY: clean-pyc
clean-pyc:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-build
clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf $(MODULE).egg-info/
	rm -rf pip-wheel-metadata/
