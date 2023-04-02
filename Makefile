.DEFAULT_GOAL := all
sources = pydantic tests docs/plugins

.PHONY: install
install:
	python -m pip install -U pip
	pip install -r requirements/all.txt
	pip install -e .

.PHONY: refresh-lockfiles
refresh-lockfiles:       ## Sync lockfiles with requirements files.
	bash requirements/refresh.sh


.PHONY: rebuild-lockfiles
rebuild-lockfiles:       ## Rebuild lockfiles from scratch, updating all dependencies
	bash requirements/rebuild.sh

.PHONY: format
format:
	black $(sources)
	ruff --fix $(sources)

.PHONY: lint
lint:
	ruff $(sources)
	black $(sources) --check --diff

.PHONY: typecheck
typecheck:
	mypy pydantic --disable-recursive-aliases --config-file .mypy-configs/full.toml

.PHONY: typecheck-fast
typecheck-fast:
	mypy pydantic --disable-recursive-aliases --config-file .mypy-configs/fast.toml

.PHONY: test-mypy
test-mypy:
	coverage run -m pytest tests/mypy --test-mypy

.PHONY: test-pyright
test-pyright:
	cd tests/pyright && pyright

.PHONY: test
test:
	coverage run -m pytest --durations=10

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@coverage html

.PHONY: testcov-compile
testcov-compile: build-trace test
	@echo "building coverage html"
	@coverage html

.PHONY: test-examples
test-examples:
	@echo "running examples"
	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'python {} >/dev/null 2>&1 || (echo "{} failed")'

.PHONY: test-fastapi
test-fastapi:
	git clone https://github.com/tiangolo/fastapi.git --single-branch
	./tests/test_fastapi.sh

.PHONY: all
all: lint typecheck-fast testcov

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -f `find . -type f -name '.*~'`
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
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
	mkdocs build
