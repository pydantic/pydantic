.DEFAULT_GOAL := all
isort = isort -rc pydantic tests
black = black -S -l 120 --target-version py38 pydantic tests

.PHONY: install
install:
	python -m pip install -U setuptools pip
	pip install -U -r requirements.txt
	SKIP_CYTHON=1 pip install -e .

.PHONY: build-cython-trace
build-cython-trace:
	python setup.py build_ext --force --inplace --define CYTHON_TRACE

.PHONY: build-cython
build-cython:
	python setup.py build_ext --inplace

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: lint
lint:
	flake8 pydantic/ tests/
	$(isort) --check-only -df
	$(black) --check --diff

.PHONY: check-dist
check-dist:
	python setup.py check -ms
	SKIP_CYTHON=1 python setup.py sdist
	twine check dist/*

.PHONY: mypy
mypy:
	mypy pydantic

.PHONY: test
test:
	pytest --cov=pydantic
	@python tests/try_assert.py

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@coverage html

.PHONY: testcov-compile
testcov-compile: build-cython-trace test
	@echo "building coverage html"
	@coverage html

.PHONY: test-examples
test-examples:
	@echo "running examples"
	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'python {} >/dev/null 2>&1 || (echo "{} failed")'

.PHONY: test-codecov
test-codecov: test
ifeq (,$(wildcard ./codecov.sh))
	curl https://codecov.io/bash -o codecov.sh
	chmod +x codecov.sh
endif
	./codecov.sh -e COMPILED,DEPS,PYTHON,OS
	rm .coverage coverage.xml

.PHONY: all
all: lint mypy testcov

.PHONY: benchmark-all
benchmark-all:
	python benchmarks/run.py

.PHONY: benchmark-pydantic
benchmark-pydantic:
	python benchmarks/run.py pydantic-only

.PHONY: benchmark-json
benchmark-json:
	TEST_JSON=1 python benchmarks/run.py

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -f pydantic/*.c pydantic/*.so
	python setup.py clean
	rm -rf site
	rm -rf docs/_build
	rm -rf docs/.changelog.md docs/.version.md docs/.tmp_schema_mappings.html
	rm -rf fastapi/test.db
	rm -rf codecov.sh
	rm -rf coverage.xml

.PHONY: docs
docs:
	flake8 --max-line-length=80 docs/examples/
	python docs/build/main.py
	mkdocs build

.PHONY: docs-serve
docs-serve:
	python docs/build/main.py
	mkdocs serve

.PHONY: publish-docs
publish-docs: docs
	zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@site.zip" https://api.netlify.com/api/v1/sites/pydantic-docs.netlify.com/deploys

fastapi:
	git clone https://github.com/tiangolo/fastapi.git

.PHONY: test-fastapi
test-fastapi: install fastapi
	./tests/test_fastapi.sh
