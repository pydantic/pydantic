# Benchmarks

## SDK import time

`test_imports_mcp.py` measures importing the MCP Python SDK in a fresh Python
interpreter. Each sample starts the current environment's Python, imports `mcp`,
and waits for the process to exit. A failed import fails the benchmark.

The result includes Python startup, all SDK dependencies, Pydantic model building,
and interpreter shutdown. It measures elapsed time for the whole process, rather
than attributing time specifically to Pydantic. Every sample has fresh Python
module and Pydantic caches; filesystem caches and compiled Python files can be
warm. This is not a cold-disk benchmark.

The `benchmark-imports` dependency group pins MCP 2.0.0, and `uv.lock` fixes its
transitive dependencies. Keep this workload unchanged when comparing Pydantic
revisions. Updating these dependencies changes the workload and should be reviewed
as a benchmark change.

Run locally with a release build of pydantic-core:

```bash
uv sync --all-packages --group benchmark-imports --no-editable --frozen
uv run --no-sync pytest tests/benchmarks/test_imports_mcp.py --benchmark-enable
```

Or use CodSpeed's elapsed-time measurements locally:

```bash
uv run --no-sync pytest tests/benchmarks/test_imports_mcp.py --codspeed --codspeed-mode=walltime --codspeed-max-rounds=20
```

The benchmark skips when MCP is not installed, so ordinary test and CPU benchmark
runs do not require the SDK. The CodSpeed workflow installs it in a separate job
using the walltime instrument: CPU simulation does not include subprocess work by
default. This job uses a standard GitHub-hosted runner, so interpret small changes
with care; scheduling and filesystem activity can affect elapsed-time results.

For diagnosis, use the model-building benchmarks alongside this whole-SDK result.
`test_imports.py` measures repeated imports within the already running test
interpreter, which does not exercise SDK startup.
