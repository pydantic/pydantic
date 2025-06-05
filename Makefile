.DEFAULT_GOAL := all
sources = python/pydantic_core tests wasm-preview/run_tests.py

mypy-stubtest = uv run python -m mypy.stubtest pydantic_core._pydantic_core --allowlist .mypy-stubtest-allowlist

# using pip install cargo (via maturin via pip) doesn't get the tty handle
# so doesn't render color without some help
export CARGO_TERM_COLOR=$(shell (test -t 0 && echo "always") || echo "auto")
# maturin develop only makes sense inside a virtual env, is otherwise
# more or less equivalent to pip install -e just a little nicer
USE_MATURIN = $(shell [ "$$VIRTUAL_ENV" != "" ] && (which maturin))

.PHONY: .uv  ## Check that uv is installed
.uv:
	@uv -V || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pre-commit  ## Check that pre-commit is installed
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: install
install: .uv .pre-commit
	uv pip install -U wheel
	uv sync --frozen --group all
	uv pip install -v -e .
	pre-commit install

.PHONY: rebuild-lockfiles  ## Rebuild lockfiles from scratch, updating all dependencies
rebuild-lockfiles: .uv
	uv lock --upgrade

.PHONY: install-rust-coverage
install-rust-coverage:
	cargo install rustfilt coverage-prepare
	rustup component add llvm-tools-preview

.PHONY: install-pgo
	rustup component add llvm-tools-preview

.PHONY: build-dev
build-dev:
	@rm -f python/pydantic_core/*.so
	uv run maturin develop --uv

.PHONY: build-prod
build-prod:
	@rm -f python/pydantic_core/*.so
	uv run maturin develop --uv --release

.PHONY: build-profiling
build-profiling:
	@rm -f python/pydantic_core/*.so
	uv run maturin develop --uv --profile profiling

.PHONY: build-coverage
build-coverage:
	@rm -f python/pydantic_core/*.so
	RUSTFLAGS='-C instrument-coverage' uv run maturin develop --uv --release

.PHONY: build-pgo
build-pgo:
	@rm -f python/pydantic_core/*.so
	$(eval PROFDATA := $(shell mktemp -d))
	RUSTFLAGS='-Cprofile-generate=$(PROFDATA)' uv run maturin develop --uv --release
	pytest tests/benchmarks
	$(eval LLVM_PROFDATA := $(shell rustup run stable bash -c 'echo $$RUSTUP_HOME/toolchains/$$RUSTUP_TOOLCHAIN/lib/rustlib/$$(rustc -Vv | grep host | cut -d " " -f 2)/bin/llvm-profdata'))
	$(LLVM_PROFDATA) merge -o $(PROFDATA)/merged.profdata $(PROFDATA)
	RUSTFLAGS='-Cprofile-use=$(PROFDATA)/merged.profdata' uv run maturin develop --uv --release
	@rm -rf $(PROFDATA)


.PHONY: build-wasm
build-wasm:
	@echo 'This requires python 3.12, maturin and emsdk to be installed'
	uv run maturin build --release --target wasm32-unknown-emscripten --out dist -i 3.12
	ls -lh dist

.PHONY: format
format:
	uv run ruff check --fix $(sources)
	uv run ruff format $(sources)
	cargo fmt

.PHONY: lint-python
lint-python:
	uv run ruff check $(sources)
	uv run ruff format --check $(sources)
	uv run griffe dump -f -d google -LWARNING -o/dev/null python/pydantic_core
	$(mypy-stubtest)

.PHONY: lint-rust
lint-rust:
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy --tests -- -D warnings

.PHONY: lint
lint: lint-python lint-rust

.PHONY: pyright
pyright:
	uv run pyright

.PHONY: test
test:
	uv run pytest

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

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf htmlcov
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf perf.data*
	rm -rf python/pydantic_core/*.so
