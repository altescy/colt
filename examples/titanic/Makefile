PWD=$(shell pwd)
PYTHON=pipenv run python
KAGGLE=pipenv run kaggle
JUPYTER=pipenv run jupyter
DATADIR=$(PWD)/data
MODULE=titanic
CONFIG=$(PWD)/configs/lgbm.jsonnet
OUTPUT=$(PWD)/submit.csv


dataset:
	$(KAGGLE) competitions download -c titanic -p $(DATADIR)
	unzip -d$(DATADIR) $(DATADIR)/*.zip
	rm -f $(DATADIR)/*.zip

run:
	PYTHONPATH=$(PWD) $(PYTHON) scripts/run.py --module $(MODULE) --config $(CONFIG) --output $(OUTPUT)

clean: clean-pyc

clean-pyc:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
