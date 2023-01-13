.DEFAULT_GOAL := all
isort = isort pydantic_core tests generate_self_schema.py
black = black pydantic_core tests generate_self_schema.py wasm-preview/run_tests.py
ruff = ruff pydantic_core tests generate_self_schema.py wasm-preview/run_tests.py

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
	@rm -f pydantic_core/*.so
	cargo build
	@rm -f target/debug/lib_pydantic_core.d
	@rm -f target/debug/lib_pydantic_core.rlib
	@mv target/debug/lib_pydantic_core.* pydantic_core/_pydantic_core.so

.PHONY: build-prod
build-prod:
	@rm -f pydantic_core/*.so
	cargo build --release
	@rm -f target/release/lib_pydantic_core.d
	@rm -f target/release/lib_pydantic_core.rlib
	@mv target/release/lib_pydantic_core.* pydantic_core/_pydantic_core.so

.PHONY: build-coverage
build-coverage:
	pip uninstall -y pydantic_core
	rm -f pydantic_core/*.so
	RUSTFLAGS='-C instrument-coverage -A incomplete_features' cargo build
	@rm -f target/debug/lib_pydantic_core.d
	@rm -f target/debug/lib_pydantic_core.rlib
	mv target/debug/lib_pydantic_core.* pydantic_core/_pydantic_core.so

.PHONY: build-wasm
build-wasm:
	@echo 'This requires python 3.10, maturin and emsdk to be installed'
	maturin build --release --target wasm32-unknown-emscripten --out dist -i 3.10
	ls -lh dist

.PHONY: format
format:
	$(isort)
	$(black)
	$(ruff) --fix --exit-zero
	cargo fmt

.PHONY: lint-python
lint-python:
	$(ruff)
	$(isort) --check-only --df
	$(black) --check --diff

.PHONY: lint-rust
lint-rust:
	cargo fmt --version
	cargo fmt --all -- --check
	cargo clippy --version
	cargo clippy -- -D warnings -A incomplete_features -W clippy::dbg_macro -W clippy::print_stdout

.PHONY: lint
lint: lint-python lint-rust

.PHONY: pyright
pyright:
	pyright

.PHONY: test
test:
	coverage run -m pytest

.PHONY: py-benchmark
py-benchmark: BRANCH=$(shell git rev-parse --abbrev-ref HEAD)
py-benchmark: build-prod
	@echo "running the \"complete\" python benchmarks, saving to: $(BRANCH)"
	pytest tests/benchmarks/test_complete_benchmark.py --benchmark-enable --benchmark-save=$(BRANCH)

.PHONY: rust-benchmark
rust-benchmark:
	cargo rust-bench

.PHONY: testcov
testcov: build-coverage test
	@rm -rf htmlcov
	@mkdir -p htmlcov
	coverage html -d htmlcov/python
	coverage-prepare html pydantic_core/*.so

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
	rm -rf pydantic_core/*.so
