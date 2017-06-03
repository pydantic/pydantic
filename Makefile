.PHONY: install
install:
	pip install -U setuptools pip
	pip install -U .
	pip install -r tests/requirements.txt
	pip install -r benchmarks/requirements.txt

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

.PHONY: testcov
testcov:
	pytest --cov=pydantic && (echo "building coverage html"; coverage html)

.PHONY: all
all: testcov lint

.PHONY: benchmark
benchmark:
	python benchmarks/run.py

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
	@echo "open file://`pwd`/docs/_build/html/index.html"

.PHONY: deploy-docs
deploy-docs: docs
	cd docs/_build/ && cp -r html site && zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
			--data-binary "@docs/_build/site.zip" https://api.netlify.com/api/v1/sites/pydantic-docs.netlify.com/deploys
