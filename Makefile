# .DEFAULT_GOAL := all
sources = pydantic tests docs/plugins

.PHONY: .uv  ## Check that uv is installed
.uv:
	@uv -V || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pre-commit  ## Check that pre-commit is installed
.pre-commit: .uv
	@uv run pre-commit -V || uv pip install pre-commit

.PHONY: install  ## Install the package, dependencies, and pre-commit for local development
install: .uv
	uv sync --frozen --group all --all-extras
	uv pip install pre-commit
	pre-commit install --install-hooks

.PHONY: rebuild-lockfiles  ## Rebuild lockfiles from scratch, updating all dependencies
rebuild-lockfiles: .uv
	uv lock --upgrade

.PHONY: format  ## Auto-format python source files
format: .uv
	uv run ruff check --fix $(sources)
	uv run ruff format $(sources)

.PHONY: lint  ## Lint python source files
lint: .uv
	uv run ruff check $(sources)
	uv run ruff format --check $(sources)

.PHONY: codespell  ## Use Codespell to do spellchecking
codespell: .pre-commit
	pre-commit run codespell --all-files

.PHONY: typecheck  ## Perform type-checking
typecheck: .pre-commit
	pre-commit run typecheck --all-files

.PHONY: test-mypy  ## Run the mypy integration tests
test-mypy: .uv
	uv run coverage run -m pytest tests/mypy --test-mypy

.PHONY: test-mypy-update  ## Update the mypy integration tests for the current mypy version
test-mypy-update: .uv
	uv run coverage run -m pytest tests/mypy --test-mypy --update-mypy

.PHONY: test-mypy-update-all  ## Update the mypy integration tests for all mypy versions
test-mypy-update-all: .uv
	rm -rf tests/mypy/outputs
	uv pip install mypy==1.10.1 && make test-mypy-update
	uv pip install mypy==1.11.2 && make test-mypy-update
	uv pip install mypy==1.12.0 && make test-mypy-update

.PHONY: test-typechecking-pyright  ## Typechecking integration tests (Pyright)
test-typechecking-pyright: .uv
	uv run bash -c 'cd tests/typechecking && pyright --version && pyright -p pyproject.toml'

.PHONY: test-typechecking-mypy   ## Typechecking integration tests (Mypy). Not to be confused with `test-mypy`.
test-typechecking-mypy: .uv
	uv run bash -c 'cd tests/typechecking && mypy --version && mypy --cache-dir=/dev/null --config-file pyproject.toml .'

.PHONY: test  ## Run all tests, skipping the type-checker integration tests
test: .uv
	uv run coverage run -m pytest --durations=10

.PHONY: benchmark  ## Run all benchmarks
benchmark: .uv
	uv run coverage run -m pytest --durations=10 --benchmark-enable tests/benchmarks

.PHONY: testcov  ## Run tests and generate a coverage report, skipping the type-checker integration tests
testcov: test
	@echo "building coverage html"
	@uv run coverage html
	@echo "building coverage lcov"
	@uv run coverage lcov

.PHONY: test-examples  ## Run only the tests from the documentation
test-examples: .uv
	@echo "running examples"
	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'uv run python {} >/dev/null 2>&1 || (echo "{} failed")'

.PHONY: test-fastapi  ## Run the FastAPI tests with this version of pydantic
test-fastapi:
	git clone https://github.com/tiangolo/fastapi.git --single-branch
	./tests/test_fastapi.sh

.PHONY: test-pydantic-settings  ## Run the pydantic-settings tests with this version of pydantic
test-pydantic-settings: .uv
	git clone https://github.com/pydantic/pydantic-settings.git --single-branch
	bash ./tests/test_pydantic_settings.sh

.PHONY: test-pydantic-extra-types  ## Run the pydantic-extra-types tests with this version of pydantic
test-pydantic-extra-types: .uv
	git clone https://github.com/pydantic/pydantic-extra-types.git --single-branch
	bash ./tests/test_pydantic_extra_types.sh

.PHONY: test-no-docs  # Run all tests except the docs tests
test-no-docs: .uv
	uv run pytest tests --ignore=tests/test_docs.py

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
	uv run mkdocs build --strict

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'

.PHONY: update-v1  ## Update V1 namespace
update-v1:
	uv run ./update_v1.sh
