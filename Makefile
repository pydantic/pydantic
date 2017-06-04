.PHONY: install
install:
	pip install -U setuptools pip
	pip install -r requirements.txt
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

.PHONY: docs-lint
docs-lint:
	make -C docs lint

.PHONY: deploy-docs
publish: docs-lint docs
	cd docs/_build/ && cp -r html site && zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@docs/_build/site.zip" https://api.netlify.com/api/v1/sites/pydantic-docs.netlify.com/deploys
