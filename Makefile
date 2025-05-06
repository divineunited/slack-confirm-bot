# Makefile for packaging and testing ca-task-service

OS = $(shell uname -s)
ARCH = $(shell uname -m)

REPO_NAME=slack-confirm-bot
MODULE_NAME=slack-confirm-bot

TEST_COMMAND=COVERAGE_CORE=sysmon pytest -n auto --dist loadscope
PYTHON_VERSION=3.12.8
PIP_INSTALL_CMD=pip install
PG_CONNECTION_ARGS=postgresql://localhost:5432/

# Platform(s) docker build
PLATFORMS := linux/arm64

# Base OS (major release) for docker
DEBIAN_NAME := bookworm
# PYTHON_BUILDER_IMAGE := us-docker.pkg.dev/cph-ops-sre/cph-docker-images-dev/python/distroless:$(PYTHON_VERSION)-slim-$(DEBIAN_NAME)
PYTHON_BUILDER_IMAGE := python/distroless:$(PYTHON_VERSION)-slim-$(DEBIAN_NAME)

# Final docker container is distroless.
GOOGLE_DISTROLESS_BASE_IMAGE := gcr.io/distroless/cc-debian12:latest

DATABASE_NAME ?= $(MODULE_NAME)
export DATABASE_URL ?= ${PG_CONNECTION_ARGS}$(DATABASE_NAME)


# Sets up pyenv and the virtualenv that is managed by pyenv
.PHONY: pyenv
pyenv:
ifdef PYTHON_VERSION
	pyenv install -s ${PYTHON_VERSION}
endif
# Only make the virtualenv if it doesnt exist
	@[ ! -e ~/.pyenv/versions/${REPO_NAME} ] && pyenv virtualenv ${PYTHON_VERSION} ${REPO_NAME} || :
	pyenv local ${REPO_NAME}
ifdef PYTHON_VERSION
# If Python has been upgraded, remove the virtualenv and recreate it
	@[ `python --version | tail -n 1 | cut -f2 -d' '` != ${PYTHON_VERSION} ] && echo "Python has been upgraded since last setup. Recreating virtualenv" && pyenv uninstall -f ${REPO_NAME} && pyenv virtualenv ${PYTHON_VERSION} ${REPO_NAME} || :
endif


# Builds any mac dependencies (brew installs, pre-commit, etc). These will not be executed when on CircleCI
# Put any homebrew installs here or things that cannot be installed on Linux
.PHONY: mac_dependencies
mac_dependencies:
ifeq (${OS}, Darwin)
	command -v buf &> /dev/null || (echo 'Please run "cd ../ca-dev && make setup"' && exit 1)
endif


# Builds all dependencies for a project
.PHONY: dependencies
dependencies: mac_dependencies
	PIP_EXTRA_INDEX_URL= ${PIP_INSTALL_CMD} pip==24.2 setuptools~=70.3
	PIP_EXTRA_INDEX_URL= ${PIP_INSTALL_CMD} --upgrade twine keyrings.google-artifactregistry-auth keyring
	${PIP_INSTALL_CMD} -r requirements.txt
	pip check

# Minimal updates to ensure the repository can run locally
pre_run:
	${PIP_INSTALL_CMD} -r requirements.txt


# Sets up the database and the environment files
.PHONY: db_env_setup
db_env_setup:
	# in case database connection does not have appropriate permissions for extensions,
	# create the extension within the template database first before creating the database
	psql "${PG_CONNECTION_ARGS}template1" -c 'CREATE EXTENSION IF NOT EXISTS btree_gist;'
	psql "${PG_CONNECTION_ARGS}template1" -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
	psql "${PG_CONNECTION_ARGS}postgres" -c 'CREATE DATABASE ${DATABASE_NAME};' || true


# Performs the full development environment setup
.PHONY: setup
setup: pyenv dependencies db_env_setup

# Clean any auto-generated files
.PHONY: clean
clean:
	python setup.py clean
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg*/
	find . -type d -name  "__pycache__" -exec rm -r {} +
	find . -type f -name '*_pb2.py' -not -path '*/tests/*' -delete
	find . -type f -name '*_pb2.pyi' -not -path '*/tests/*' -delete
	find . -type f -name '*_pb2_grpc.py' -not -path '*/tests/*' -delete
	rm -f .coverage


# Drop the database
.PHONY: drop_db
drop_db:
	psql "${PG_CONNECTION_ARGS}postgres" -c "DROP DATABASE IF EXISTS ${DATABASE_NAME};"
