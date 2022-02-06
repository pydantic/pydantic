.DEFAULT_GOAL := all
isort = isort pydantic tests
black = black -S -l 120 --target-version py38 pydantic tests

.PHONY: help
help: ## List all make commands available
	@grep -E '^[\.a-zA-Z_%-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk -F ":" '{print $1}' | sed 's/\\//g' | sort | awk 'BEGIN {FS = ":[^:]*?##"}; {printf "\033[0;94m%-50s\033[0m %s\n", $$1, $$2}'

.PHONY: install-linting
install-linting: ## Install linting tools
	pip install -r tests/requirements-linting.txt
	pre-commit install

.PHONY: install-pydantic
install-pydantic: ## Install pydantic
	python -m pip install -U wheel pip
	pip install -r requirements.txt
	SKIP_CYTHON=1 pip install -e .

.PHONY: install-testing
install-testing: install-pydantic ## Install testing tools
	pip install -r tests/requirements-testing.txt

.PHONY: install-docs
install-docs: install-pydantic ## Install docs
	pip install -U -r docs/requirements.txt

.PHONY: install-benchmarks
install-benchmarks: install-pydantic ## Install benchmarks
	pip install -U -r benchmarks/requirements.txt

.PHONY: install
install: install-testing install-linting install-docs ## Install everything
	@echo 'installed development requirements'

.PHONY: build-trace
build-trace: ## Build trace
	python setup.py build_ext --force --inplace --define CYTHON_TRACE

.PHONY: build
build: ## Build
	python setup.py build_ext --inplace

.PHONY: format
format: ## Format code
	$(isort)
	$(black)

.PHONY: lint
lint: ## Lint code
	flake8 pydantic/ tests/
	$(isort) --check-only --df
	$(black) --check --diff

.PHONY: check-dist
check-dist: ## Check distribution
	python setup.py check -ms
	SKIP_CYTHON=1 python setup.py sdist
	twine check dist/*

.PHONY: mypy
mypy: ## Check type annotations
	mypy pydantic

.PHONY: test
test: ## Run tests
	pytest --cov=pydantic

.PHONY: testcov
testcov: test ## Run tests with coverage
	@echo "building coverage html"
	@coverage html

.PHONY: testcov-compile
testcov-compile: build-trace test ## Run tests with coverage and compile
	@echo "building coverage html"
	@coverage html

.PHONY: test-examples
test-examples: ## Run examples
	@echo "running examples"
	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'python {} >/dev/null 2>&1 || (echo "{} failed")'

.PHONY: test-fastapi
test-fastapi: ## Run fastapi tests
	git clone https://github.com/tiangolo/fastapi.git --single-branch
	./tests/test_fastapi.sh

.PHONY: all
all: lint mypy testcov ## Run linter, type checker, and tests with coverage

.PHONY: benchmark-all
benchmark-all: ## Run all benchmarks
	python benchmarks/run.py

.PHONY: benchmark-pydantic
benchmark-pydantic: ## Run pydantic benchmarks
	python benchmarks/run.py pydantic-only

.PHONY: benchmark-json
benchmark-json: ##	Run json benchmarks
	TEST_JSON=1 python benchmarks/run.py

.PHONY: clean
clean: ## Clean
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -f `find . -type f -name '.*~'`
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
	rm -rf coverage.xml

.PHONY: docs
docs: ## Generate docs
	flake8 --max-line-length=80 docs/examples/
	python docs/build/main.py
	mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve docs
	python docs/build/main.py
	mkdocs serve

.PHONY: publish-docs
publish-docs: ## Publish docs
	zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@site.zip" https://api.netlify.com/api/v1/sites/pydantic-docs.netlify.com/deploys
