.DEFAULT_GOAL := all
sources = pydantic tests docs/build

.PHONY: install-linting
install-linting:
	pip install -r tests/requirements-linting.txt
	pre-commit install

.PHONY: install-pydantic
install-pydantic:
	python -m pip install -U wheel pip
	pip install -r requirements.txt
	pip install -e .

.PHONY: install-testing
install-testing: install-pydantic
	pip install -r tests/requirements-testing.txt

.PHONY: install-docs
install-docs: install-pydantic
	pip install -U -r docs/requirements.txt

.PHONY: install
install: install-testing install-linting install-docs
	@echo 'installed development requirements'

.PHONY: format
format:
	pyupgrade --py37-plus --exit-zero-even-if-changed `find $(sources) -name "*.py" -type f`
	isort $(sources)
	black $(sources)

.PHONY: lint
lint:
	flake8 $(sources)
	isort $(sources) --check-only --df
	black $(sources) --check --diff

.PHONY: mypy
mypy:
	mypy pydantic docs/build

.PHONY: pyupgrade
pyupgrade:
	pyupgrade --py37-plus `find pydantic tests -name "*.py" -type f`

.PHONY: pyright
pyright:
	cd tests/pyright && pyright

.PHONY: test
test:
	pytest --cov=pydantic

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
all: lint mypy testcov

.PHONY: clean
clean:
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
	rm -rf site
	rm -rf docs/_build
	rm -rf docs/.changelog.md docs/.version.md docs/.tmp_schema_mappings.html
	rm -rf fastapi/test.db
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
publish-docs:
	zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@site.zip" https://api.netlify.com/api/v1/sites/pydantic-docs.netlify.com/deploys
