.DEFAULT_GOAL := all
sources = pydantic tests docs/plugins

.PHONY: .pdm
.pdm:  ## Check that PDM is isntallced
	@pdm -V || echo 'Please install PDM: https://pdm.fming.dev/latest/\#installation'

.PHONY: .pre-commit
.pre-commit:  ## Check that pre-commit is installed
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: install
install: .pdm .pre-commit
	pdm install --group :all
	pre-commit install --install-hooks

.PHONY: refresh-lockfiles
refresh-lockfiles: .pdm       ## Sync lockfiles with requirements files.
	pdm lock --refresh --dev --group :all

.PHONY: rebuild-lockfiles
rebuild-lockfiles: .pdm       ## Rebuild lockfiles from scratch, updating all dependencies
	pdm lock --dev --group :all

.PHONY: format
format: .pdm
	pdm run black $(sources)
	pdm run ruff --fix $(sources)

.PHONY: lint
lint: .pdm
	pdm run ruff $(sources)
	pdm run black $(sources) --check --diff

.PHONY: codespell
codespell: .pre-commit
	pre-commit run codespell --all-files

.PHONY: typecheck
typecheck: .pre-commit .pdm
	pre-commit run typecheck --all-files

.PHONY: test-mypy
test-mypy: .pdm
	pdm run coverage run -m pytest tests/mypy --test-mypy

.PHONY: test-pyright
test-pyright: .pdm
	pdm run bash -c 'cd tests/pyright && pyright'

.PHONY: test
test: .pdm
	pdm run coverage run -m pytest --durations=10

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@pdm run coverage html

.PHONY: testcov-compile
testcov-compile: .pdm build-trace test
	@echo "building coverage html"
	@pdm run coverage html

.PHONY: test-examples
test-examples: .pdm
	@echo "running examples"
	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'pdm run python {} >/dev/null 2>&1 || (echo "{} failed")'

.PHONY: test-fastapi
test-fastapi: .pdm
	git clone https://github.com/tiangolo/fastapi.git --single-branch
	pdm run ./tests/test_fastapi.sh

.PHONY: all
all: lint typecheck codespell testcov

.PHONY: clean
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

.PHONY: docs
docs:
	pdm run mkdocs build
