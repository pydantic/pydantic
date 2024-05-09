.DEFAULT_GOAL := all
sources = pydantic tests docs/plugins

.PHONY: .pdm  ## Check that PDM is installed
.pdm:
	@pdm -V || echo 'Please install PDM: https://pdm.fming.dev/latest/#installation'

.PHONY: .pre-commit  ## Check that pre-commit is installed
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: install  ## Install the package, dependencies, and pre-commit for local development
install: .pdm .pre-commit
	pdm info
	pdm install --group :all
	pre-commit install --install-hooks

.PHONY: refresh-lockfiles  ## Sync lockfiles with requirements files.
refresh-lockfiles: .pdm
	pdm update --update-reuse --group :all

.PHONY: rebuild-lockfiles  ## Rebuild lockfiles from scratch, updating all dependencies
rebuild-lockfiles: .pdm
	pdm update --update-eager --group :all

.PHONY: format  ## Auto-format python source files
format: .pdm
	pdm run ruff check --fix $(sources)
	pdm run ruff format $(sources)

.PHONY: lint  ## Lint python source files
lint: .pdm
	pdm run ruff check $(sources)
	pdm run ruff format --check $(sources)

.PHONY: codespell  ## Use Codespell to do spellchecking
codespell: .pre-commit
	pre-commit run codespell --all-files

.PHONY: typecheck  ## Perform type-checking
typecheck: .pre-commit .pdm
	pre-commit run typecheck --all-files

.PHONY: test-mypy  ## Run the mypy integration tests
test-mypy: .pdm
	pdm run coverage run -m pytest tests/mypy --test-mypy

.PHONY: test-mypy-update  ## Update the mypy integration tests for the current mypy version
test-mypy-update: .pdm
	pdm run coverage run -m pytest tests/mypy --test-mypy --update-mypy

.PHONY: test-mypy-update-all  ## Update the mypy integration tests for all mypy versions
test-mypy-update-all: .pdm
	rm -rf tests/mypy/outputs
	pip install --force mypy==1.0.1 && make test-mypy-update
	pip install --force mypy==1.1.1 && make test-mypy-update
	pip install --force mypy==1.2.0 && make test-mypy-update
	pip install --force mypy==1.4.1 && make test-mypy-update
	pip install --force mypy==1.5.0 && make test-mypy-update

.PHONY: test-pyright  ## Run the pyright integration tests
test-pyright: .pdm
	pdm run bash -c 'cd tests/pyright && pyright'

.PHONY: test  ## Run all tests, skipping the type-checker integration tests
test: .pdm
	pdm run coverage run -m pytest --durations=10

.PHONY: benchmark  ## Run all benchmarks
benchmark: .pdm
	pdm run coverage run -m pytest --durations=10 --benchmark-enable tests/benchmarks

.PHONY: testcov  ## Run tests and generate a coverage report, skipping the type-checker integration tests
testcov: test
	@echo "building coverage html"
	@pdm run coverage html
	@echo "building coverage lcov"
	@pdm run coverage lcov

.PHONY: test-examples  ## Run only the tests from the documentation
test-examples: .pdm
	@echo "running examples"
	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'pdm run python {} >/dev/null 2>&1 || (echo "{} failed")'

.PHONY: test-fastapi  ## Run the FastAPI tests with this version of pydantic
test-fastapi:
	git clone https://github.com/tiangolo/fastapi.git --single-branch
	./tests/test_fastapi.sh

.PHONY: test-pydantic-settings  ## Run the pydantic-settings tests with this version of pydantic
test-pydantic-settings: .pdm
	git clone https://github.com/pydantic/pydantic-settings.git --single-branch
	bash ./tests/test_pydantic_settings.sh

.PHONY: test-pydantic-extra-types  ## Run the pydantic-extra-types tests with this version of pydantic
test-pydantic-extra-types: .pdm
	git clone https://github.com/pydantic/pydantic-extra-types.git --single-branch
	bash ./tests/test_pydantic_extra_types.sh

.PHONY: all  ## Run the standard set of checks performed in CI
all: lint typecheck codespell testcov

.PHONY: clean  ## Clear local caches and build artifacts
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -f `find . -type f -name '.*~'`
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -rf site
	rm -rf docs/_build
	rm -rf docs/.changelog.md docs/.version.md docs/.tmp_schema_mappings.html
	rm -rf fastapi/test.db
	rm -rf coverage.xml

.PHONY: docs  ## Generate the docs
docs:
	pdm run mkdocs build --strict

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'

.PHONY: update-v1  ## Update V1 namespace
update-v1:
	pdm run ./update_v1.sh
