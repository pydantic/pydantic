.PHONY: install
install:
	pip install -U setuptools pip
	pip install -U .
	pip install -r tests/requirements.txt

.PHONY: isort
isort:
	isort -rc -w 120 pydantic
	isort -rc -w 120 tests

.PHONY: lint
lint:
	python setup.py check -rms
	flake8 pydantic/ tests/
	pytest pydantic -p no:sugar -q --cache-clear

.PHONY: test
test:
	pytest --cov=pydantic

.PHONY: testcov
testcov:
	pytest --cov=pydantic && (echo "building coverage html"; coverage html)

.PHONY: all
all: testcov lint

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
