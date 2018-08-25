.DEFAULT_GOAL := all

.PHONY: install
install:
	pip install -U setuptools pip
	pip install -U -r requirements.txt
	pip install -U .

.PHONY: isort
isort:
	isort -rc -w 120 pydantic
	isort -rc -w 120 tests

.PHONY: lint
lint:
	python setup.py check -rms
	flake8 pydantic/ tests/
	pytest pydantic -p no:sugar -q

.PHONY: test
test:
	pytest --cov=pydantic

.PHONY: mypy
mypy:
	@echo "testing simple example with mypy (and python to check it's sane)..."
	mypy --ignore-missing-imports --follow-imports=skip --strict-optional tests/mypy_test_success.py
	python tests/mypy_test_success.py
	@echo "checking code with bad type annotations fails..."
	@mypy --ignore-missing-imports --follow-imports=skip tests/mypy_test_fails.py 1>/dev/null; \
	  test $$? -eq 1 || \
	  (echo "mypy passed when it shouldn't"; exit 1)
	python tests/mypy_test_fails.py

.PHONY: testcov
testcov:
	pytest --cov=pydantic
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: testcov mypy lint

.PHONY: benchmark-all
benchmark-all:
	python benchmarks/run.py

.PHONY: benchmark-pydantic
benchmark-pydantic:
	python benchmarks/run.py pydantic-only

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	python setup.py clean
	make -C docs clean

.PHONY: docs
docs:
	make -C docs html

.PHONY: publish
publish: docs
	cd docs/_build/ && cp -r html site && zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@docs/_build/site.zip" https://api.netlify.com/api/v1/sites/pydantic-docs.netlify.com/deploys
