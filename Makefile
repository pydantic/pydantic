.DEFAULT_GOAL := all
isort = isort pydantic_core tests setup.py
black = black pydantic_core tests setup.py

.PHONY: install
install:
	pip install -U pip wheel setuptools setuptools_rust pre-commit
	pip install -r tests/requirements.txt
	pip install -r tests/requirements-linting.txt
	pip install -e .
	pre-commit install

.PHONY: install-rust-coverage
install-rust-coverage:
	cargo install rustfilt cargo-binutils
	rustup component add llvm-tools-preview

.PHONY: build-dev
build-dev:
	rm -f pydantic_core/*.so
	python setup.py develop

.PHONY: build-coverage
build-coverage:
	rm -f pydantic_core/*.so
	RUSTFLAGS='-C instrument-coverage' python setup.py develop

.PHONY: format
format:
	$(isort)
	$(black)
	@echo 'max_width = 120' > .rustfmt.toml
	cargo fmt

.PHONY: lint-python
lint-python:
	flake8 --max-complexity 10 --max-line-length 120 --ignore E203,W503 pydantic_core tests setup.py
	$(isort) --check-only --df
	$(black) --check --diff

.PHONY: lint-rust
lint-rust:
	cargo fmt --version
	@echo 'max_width = 120' > .rustfmt.toml
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy -- -D warnings

.PHONY: lint
lint: lint-python lint-rust

.PHONY: mypy
mypy:
	mypy pydantic_core

.PHONY: test
test:
	coverage run -m pytest

.PHONY: testcov
testcov: build-coverage test
	@rm -rf htmlcov
	@mkdir -p htmlcov
	coverage html -d htmlcov/python
	./tests/rust_coverage_html.sh

.PHONY: all
all: format lint mypy test

.PHONY: flame
flame:
	@rm -rf perf.data*
	@rm -rf flame
	@mkdir -p flame
	perf record -g benchmarks/minimal.py
	perf script --max-stack 20 | stackcollapse-perf.pl | flamegraph.pl > flame/python.svg
	perf script --max-stack 20 | stackcollapse-perf.pl > flame/python.txt
	@rm perf.data
	JSON=1 perf record -g benchmarks/minimal.py
	perf script --max-stack 20 | stackcollapse-perf.pl | flamegraph.pl > flame/json.svg
	perf script --max-stack 20 | stackcollapse-perf.pl > flame/json.txt
	@rm perf.data


.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf flame
	rm -rf htmlcov
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf perf.data*
	python setup.py clean
