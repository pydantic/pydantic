# Library startup benchmarks

These benchmarks measure the startup time of libraries built on Pydantic. Each
sample starts a fresh Python interpreter from the current environment, recursively
imports the library's modules (including all model definitions), and waits for the
process to exit. A failed import fails the benchmark.

CLI entry points are excluded, along with explicitly listed compatibility shims
and optional integrations without model definitions. MCP includes both `mcp` and
`mcp_types`, covering server and authentication models as well as every protocol
version. These workloads measure eager loading of all models, even when ordinary
library startup uses lazy imports.

OpenAI includes every module under `openai.types` and the rest of the SDK,
including streaming event and pagination models. Optional audio and WebSocket
integrations without model definitions are excluded. SDK defaults such as deferred
schema building are preserved: importing every model does not force deferred
schemas to be built.

Anthropic likewise includes every module under `anthropic.types`, plus pagination,
streaming, tool-runner, and other SDK models. Its optional aiohttp transport is
excluded because it contains no model definitions.

Google Gen AI includes all production model modules under `google.genai`, including
its complete types module and the nested `_gaos` models. Bundled tests, their test
harness, and optional tokenizer modules without Pydantic models are excluded.
Version 2.34.0 requires Python 3.11 or later, so its dependency is conditional and
the benchmark skips on Python 3.10.

The result includes Python startup, all of the library's dependencies, Pydantic
model building, and interpreter shutdown. It measures elapsed time for the whole
process, rather than attributing time specifically to Pydantic. Every sample has
fresh Python module and Pydantic caches; filesystem caches and compiled Python
files can be warm. This is not a cold-disk benchmark.

## Benchmarked libraries

The current workloads pin MCP 2.3.0, OpenAI 3.41.0, Anthropic 2.3.0, and Google
Gen AI 2.34.0 (the latest stable releases checked on 2026-10-29). The lockfile also
pins their dependencies.

To add a library:

1. Pin it to an exact version in the `benchmark-startup` group in `pyproject.toml`
   and update `uv.lock`.
2. Add an entry to `LIBRARIES` in [`test_library_startup.py`](./test_library_startup.py),
   mapping the distribution name to the code to run (typically imports of the modules
   defining the library's Pydantic models).

## Running

Run locally with a release build of pydantic-core:

```bash
uv sync --all-packages --group benchmark-startup --no-editable --frozen
uv run --no-sync pytest tests/benchmarks/library_startup --benchmark-enable
```

Or use CodSpeed's elapsed-time measurements locally:

```bash
uv run --no-sync pytest tests/benchmarks/library_startup --codspeed --codspeed-mode=walltime --codspeed-max-rounds=20
```
