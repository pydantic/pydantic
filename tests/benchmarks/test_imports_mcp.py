"""Measure SDK startup in a fresh interpreter, including Python startup and shutdown."""

import importlib.util
import subprocess
import sys
from collections.abc import Callable

import pytest


@pytest.mark.skipif(sys.platform == 'emscripten', reason='Requires subprocess support')
@pytest.mark.skipif(
    importlib.util.find_spec('mcp') is None,
    reason='Install the benchmark-imports dependency group to benchmark MCP startup',
)
def test_import_mcp(benchmark: Callable[[Callable[[], None]], None]) -> None:
    def run() -> None:
        # Use this environment's interpreter so the child imports the Pydantic under test.
        # Repeating an import in this process would just measure Python's module cache.
        subprocess.run([sys.executable, '-c', 'import mcp'], check=True)

    benchmark(run)
