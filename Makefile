.DEFAULT_GOAL := all
black = black python/pydantic_core tests generate_self_schema.py wasm-preview/run_tests.py
ruff = ruff python/pydantic_core tests generate_self_schema.py wasm-preview/run_tests.py
mypy-stubtest = python -m mypy.stubtest pydantic_core._pydantic_core --allowlist .mypy-stubtest-allowlist

.PHONY: install
install:
	pip install -U pip wheel pre-commit
	pip install -r tests/requirements.txt
	pip install -r tests/requirements-linting.txt
	pip install -e .
	pre-commit install

.PHONY: install-rust-coverage
install-rust-coverage:
	cargo install rustfilt coverage-prepare
	rustup component add llvm-tools-preview

.PHONY: build-dev
build-dev:
	@rm -f python/pydantic_core/*.so
	cargo build --features extension-module
	@rm -f target/debug/lib_pydantic_core.d
	@rm -f target/debug/lib_pydantic_core.rlib
	@mv target/debug/lib_pydantic_core.* python/pydantic_core/_pydantic_core.so

.PHONY: build-prod
build-prod:
	@rm -f python/pydantic_core/*.so
	maturin develop --release

.PHONY: build-coverage
build-coverage:
	rm -f python/pydantic_core/*.so
	maturin develop -- -C instrument-coverage

.PHONY: build-wasm
build-wasm:
	@echo 'This requires python 3.11, maturin and emsdk to be installed'
	maturin build --release --target wasm32-unknown-emscripten --out dist -i 3.11
	ls -lh dist

.PHONY: format
format:
	$(black)
	$(ruff) --fix --exit-zero
	cargo fmt

.PHONY: lint-python
lint-python:
	$(ruff)
	$(black) --check --diff
	$(mypy-stubtest)
	griffe dump -f -d google -LWARNING -o/dev/null python/pydantic_core

.PHONY: lint-rust
lint-rust:
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy --tests -- \
		-D warnings \
		-W clippy::pedantic \
		-W clippy::dbg_macro \
		-W clippy::print_stdout \
		-A clippy::cast-possible-truncation \
		-A clippy::cast-possible-wrap \
		-A clippy::cast-precision-loss \
		-A clippy::cast-sign-loss \
		-A clippy::doc-markdown \
		-A clippy::float-cmp \
		-A clippy::fn-params-excessive-bools \
		-A clippy::if-not-else \
		-A clippy::manual-let-else \
		-A clippy::match-bool \
		-A clippy::match-same-arms \
		-A clippy::missing-errors-doc \
		-A clippy::missing-panics-doc \
		-A clippy::module-name-repetitions \
		-A clippy::must-use-candidate \
		-A clippy::needless-pass-by-value \
		-A clippy::similar-names \
		-A clippy::single-match-else \
		-A clippy::struct-excessive-bools \
		-A clippy::too-many-lines \
		-A clippy::unnecessary-wraps \
		-A clippy::unused-self \
		-A clippy::used-underscore-binding

.PHONY: lint
lint: lint-python lint-rust

.PHONY: pyright
pyright:
	pyright

.PHONY: test
test:
	pytest

.PHONY: testcov
testcov: build-coverage
	@rm -rf htmlcov
	@mkdir -p htmlcov
	coverage run -m pytest
	coverage report
	coverage html -d htmlcov/python
	coverage-prepare html python/pydantic_core/*.so

.PHONY: all
all: format build-dev lint test

.PHONY: flame
flame:
	@rm -rf perf.data*
	@rm -rf flame
	@mkdir -p flame
	perf record -g profiling/dict_model.py
	perf script --max-stack 20 | stackcollapse-perf.pl | flamegraph.pl > flame/python.svg
	perf script --max-stack 20 | stackcollapse-perf.pl > flame/python.txt
	@rm perf.data
	JSON=1 perf record -g profiling/dict_model.py
	perf script --max-stack 20 | stackcollapse-perf.pl | flamegraph.pl > flame/json.svg
	perf script --max-stack 20 | stackcollapse-perf.pl > flame/json.txt
	@rm perf.data

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf src/self_schema.py
	rm -rf .cache
	rm -rf flame
	rm -rf htmlcov
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf perf.data*
	rm -rf python/pydantic_core/*.so
