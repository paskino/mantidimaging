AUTHENTICATION_PARAMS=--user $$UPLOAD_USER --token $$ANACONDA_API_TOKEN

#Needed because each command is run in a new shell
SHELL=/bin/bash

SOURCE_DIRS=mantidimaging scripts docs/ext/

CHANNELS:=$(shell cat environment.yml | sed -ne '/channels:/,/dependencies:/{//!p}' | grep '^  -' | sed 's/ - / --append channels /g' | tr -d '\n')

install-build-requirements:
	@echo "Installing packages required for starting the build process"
	conda create -n build-env --yes boa anaconda-client conda-verify
	conda run -n build-env conda config --env $(CHANNELS)

build-conda-package: install-build-requirements
	conda run -n build-env conda mambabuild conda --label unstable

build-conda-package-nightly: .remind-for-user .remind-for-anaconda-api install-build-requirements
	conda run -n build-env conda-build conda $(AUTHENTICATION_PARAMS) --label nightly

build-conda-package-release: .remind-for-user .remind-for-anaconda-api install-build-requirements
	conda run -n build-env conda-build conda $(AUTHENTICATION_PARAMS)

.remind-for-user:
	@if [ -z "$$UPLOAD_USER" ]; then echo "Environment variable UPLOAD_USER not set!"; exit 1; fi;

.remind-for-anaconda-api:
	@if [ -z "$$ANACONDA_API_TOKEN" ]; then echo "Environment variable ANACONDA_API_TOKEN not set!"; exit 1; fi;


install-dev-requirements:
	python ./setup.py create_dev_env

test:
	python -m pytest

mypy:
	python -m mypy --ignore-missing-imports --no-site-packages ${SOURCE_DIRS}

yapf:
	python -m yapf --parallel --diff --recursive ${SOURCE_DIRS}

yapf_apply:
	python -m yapf -i --parallel --recursive ${SOURCE_DIRS}

ruff:
	ruff ${SOURCE_DIRS}

check: ruff yapf mypy test
