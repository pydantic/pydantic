.DEFAULT_GOAL := all
sources = pydantic tests docs/build

.PHONY: install
install:
	python -m pip install -U pip
	pip install -r requirements/all.txt
	pip install -e .

.PHONY: refresh-lockfiles
refresh-lockfiles:
	@echo "Updating requirements/*.txt files using pip-compile"
	find requirements/ -name '*.txt' ! -name 'all.txt' -type f -delete
	pip-compile -q --resolver backtracking -o requirements/docs.txt requirements/docs.in
	pip-compile -q --resolver backtracking -o requirements/linting.txt requirements/linting.in
	pip-compile -q --resolver backtracking -o requirements/testing.txt requirements/testing.in
	pip-compile -q --resolver backtracking -o requirements/testing-extra.txt requirements/testing-extra.in
	pip-compile -q --resolver backtracking -o requirements/pyproject-min.txt pyproject.toml
	pip-compile -q --resolver backtracking -o requirements/pyproject-all.txt pyproject.toml --extra=email
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
	mypy pydantic docs/build --disable-recursive-aliases

.PHONY: mypy
test-mypy:
	coverage run -m pytest tests/mypy --test-mypy

.PHONY: pyright
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
	ruff docs/examples/
	python docs/build/main.py
	mkdocs build

.PHONY: docs-serve
docs-serve:
	python docs/build/main.py
	mkdocs serve
