PWD              := $(shell pwd)
PYTHON           := poetry run python
PYLINT           := poetry run pylint
MYPY             := poetry run mypy
PYTEST           := poetry run pytest
PYLINTRC         := $(PWD)/.pylintrc
MYPYINI          := $(PWD)/mypy.ini
MODULE           := colt


.PHONY: lint
lint:
	PYTHONPATH=$(PWD) $(PYLINT) --rcfile=$(PYLINTRC) $(MODULE)

.PHONY: mypy
mypy:
	PYTHONPATH=$(PWD) $(MYPY)  --config-file $(MYPYINI) $(MODULE)

.PHONY: test
test:
	PYTHONPATH=$(PWD) $(PYTEST)

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
