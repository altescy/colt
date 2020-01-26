PWD=$(shell pwd)
PYTHON=python
PYLINTRC=.pylintrc
MODULE=pob
DOCKER=docker
DOCKERFILE=$(PWD)/docker/Dockerfile.dev
DOCKER_IMAGE=pob-dev
DOCKER_CONTAINER=pob-dev-container


lint:
	pylint --rcfile=$(PYLINTRC) $(MODULE)

mypy:
	mypy $(MODULE)

test:
	PYTHONPATH=$(PWD) pytest

clean: clean-pyc clean-build

clean-pyc:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf $(MODULE).egg-info/
	rm -rf pip-wheel-metadata/

docker: docker-build docker-run

docker-build:
	$(DOCKER) build -f $(DOCKERFILE) -t $(DOCKER_IMAGE) $(PWD)

docker-run:
	$(DOCKER) run -it -v $(PWD):/work --name $(DOCKER_CONTAINER) $(DOCKER_IMAGE)

docker-attach:
	$(DOCKER) attach $(DOCKER_CONTAINER)

docker-rm:
	$(DOCKER) rm $(DOCKER_CONTAINER)
