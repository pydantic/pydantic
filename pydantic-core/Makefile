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

.PHONY: install  ## Install the package, dependencies, and pre-commit for local development
install: .uv
	uv sync --frozen --group all
	uv run pre-commit install --install-hooks

.PHONY: rebuild-lockfiles  ## Rebuild lockfiles from scratch, updating all dependencies
rebuild-lockfiles: .uv
	uv lock --upgrade

.PHONY: install-rust-coverage  ## Install Rust coverage tools
install-rust-coverage:
	cargo install rustfilt coverage-prepare
	rustup component add llvm-tools-preview

.PHONY: install-pgo  ## Install Rust PGO tools
install-pgo:
	rustup component add llvm-tools-preview

.PHONY: build-dev  ## Build the development version of the package
build-dev:
	@rm -f python/pydantic_core/*.so
	uvx maturin develop --uv

.PHONY: build-prod  ## Build the production version of the package
build-prod:
	@rm -f python/pydantic_core/*.so
	uvx maturin develop --uv --release

.PHONY: build-profiling  ## Build the profiling version of the package
build-profiling:
	@rm -f python/pydantic_core/*.so
	uvx maturin develop --uv --profile profiling

.PHONY: build-coverage  ## Build the coverage version of the package
build-coverage:
	@rm -f python/pydantic_core/*.so
	RUSTFLAGS='-C instrument-coverage' uvx maturin develop --uv --release

.PHONY: build-pgo  ## Build the PGO version of the package
build-pgo:
	@rm -f python/pydantic_core/*.so
	$(eval PROFDATA := $(shell mktemp -d))
	RUSTFLAGS='-Cprofile-generate=$(PROFDATA)' uvx maturin develop --uv --release
	pytest tests/benchmarks
	$(eval LLVM_PROFDATA := $(shell rustup run stable bash -c 'echo $$RUSTUP_HOME/toolchains/$$RUSTUP_TOOLCHAIN/lib/rustlib/$$(rustc -Vv | grep host | cut -d " " -f 2)/bin/llvm-profdata'))
	$(LLVM_PROFDATA) merge -o $(PROFDATA)/merged.profdata $(PROFDATA)
	RUSTFLAGS='-Cprofile-use=$(PROFDATA)/merged.profdata' uvx maturin develop --uv --release
	@rm -rf $(PROFDATA)


.PHONY: build-wasm  ## Build the WebAssembly version of the package
build-wasm:
	@echo 'This requires python 3.12, maturin and emsdk to be installed'
	uvx maturin build --release --target wasm32-unknown-emscripten --out dist -i 3.12
	ls -lh dist

.PHONY: format  ## Auto-format rust and python source files
format:
	uv run ruff check --fix $(sources)
	uv run ruff format $(sources)
	cargo fmt

.PHONY: lint-python  ## Lint python source files
lint-python:
	uv run ruff check $(sources)
	uv run ruff format --check $(sources)
	uv run griffe dump -f -d google -LWARNING -o/dev/null python/pydantic_core
	$(mypy-stubtest)

.PHONY: lint-rust  ## Lint rust source files
lint-rust:
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy --tests -- -D warnings

.PHONY: lint  ## Lint rust and python source files
lint: lint-python lint-rust

.PHONY: pyright  ## Perform type-checking with pyright
pyright:
	uv run pyright

.PHONY: test  ## Run all tests
test:
	uv run pytest

.PHONY: testcov  ## Run tests and generate a coverage report
testcov: build-coverage
	@rm -rf htmlcov
	@mkdir -p htmlcov
	coverage run -m pytest
	coverage report
	coverage html -d htmlcov/python
	coverage-prepare html python/pydantic_core/*.so

.PHONY: all  ## Run the standard set of checks performed in CI
all: format build-dev lint test

.PHONY: clean  ## Clear local caches and build artifacts
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

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-19s\033[0m %s\n", $$2, $$3}'
