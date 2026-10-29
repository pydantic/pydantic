"""Measure library startup in a fresh interpreter, including Python startup and shutdown."""

import importlib.metadata
import subprocess
import sys
from collections.abc import Callable

import pytest

# Distributions pinned in the `benchmark-startup` dependency group, mapped to the code
# run in the child interpreter.
LIBRARIES = {
    'mcp': 'from mcp_types import _types, _v2025_11_25, _v2026_07_28',
}


@pytest.mark.skipif(sys.platform == 'emscripten', reason='Requires subprocess support')
@pytest.mark.parametrize(
    ['library', 'code'],
    LIBRARIES.items(),
    ids=LIBRARIES.keys(),
)
def test_library_startup(benchmark: Callable[[Callable[[], None]], None], library: str, code: str) -> None:
    try:
        importlib.metadata.distribution(library)
    except importlib.metadata.PackageNotFoundError:
        pytest.skip(f'Install the benchmark-startup dependency group to benchmark {library!r} startup')

    def run() -> None:
        subprocess.run([sys.executable, '-c', code], check=True)

    benchmark(run)
