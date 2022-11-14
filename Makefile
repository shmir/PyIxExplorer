#
# Makefile to build and upload to local pypi servers.
#

.PHONY: clean build

repo=localhost
user=pypiadmin
password=pypiadmin

help:
	@echo 'install: install pip requirements'
	@echo 'build: build the package'
	@echo 'upload: create and upload the package to local pypi index'
	@echo '        takes the following params:'
	@echo '        repo=repository-url, default localhost:8086'
	@echo '        user=user name, default pypiadmin'
	@echo '        password=user password, default pypiadmin'

clean:
	rm -rf dist/*
	rm -rf *.egg-info
	rm -rf build

install:
	make clean
	python -m pip install -U pip
	pip install -U -r requirements.txt

build:
	make clean
	python -m build . --wheel

upload:
	make build
	twine upload --repository-url http://$(repo):8036 --user $(user) --password $(password) dist/*
