.DEFAULT_GOAL := all
sources = pydantic tests docs/plugins

.PHONY: install
install:
	python -m pip install -U pip
	pip install -r requirements/all.txt
	pip install -e .

.PHONY: refresh-lockfiles
refresh-lockfiles:
	@echo "Updating requirements/*.txt files using pip-compile"
	pip-compile -q --resolver backtracking -o requirements/all.txt --strip-extras requirements/all.in

	pip-compile -q --resolver backtracking -o requirements/docs.txt requirements/docs-constrained.in
	pip-compile -q --resolver backtracking -o requirements/linting.txt requirements/linting-constrained.in
	pip-compile -q --resolver backtracking -o requirements/testing.txt  requirements/testing-constrained.in
	pip-compile -q --resolver backtracking -o requirements/testing-extra.txt requirements/testing-extra-constrained.in
	pip-compile -q --resolver backtracking -o requirements/pyproject-min.txt --pip-args '-c requirements/all.txt' pyproject.toml
	pip-compile -q --resolver backtracking -o requirements/pyproject-all.txt --pip-args '-c requirements/all.txt' --all-extras pyproject.toml

	pip install --dry-run -r requirements/all.txt

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
all: lint typecheck testcov

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
