"""Measure library startup in a fresh interpreter, including Python startup and shutdown."""

import importlib.metadata
import subprocess
import sys
from collections.abc import Callable

import pytest

IMPORT_ALL_MODULES = """\
import importlib
import pkgutil

def import_all(name: str) -> None:
    if name in {excluded!r} or name.rsplit('.', 1)[-1] in ('__main__', 'cli'):
        return
    module = importlib.import_module(name)
    if hasattr(module, '__path__'):
        for child in pkgutil.iter_modules(module.__path__, module.__name__ + '.'):
            import_all(child.name)

for name in {packages!r}:
    import_all(name)
"""

# Distributions pinned in the `benchmark-startup` dependency group, mapped to the code
# run in the child interpreter.
LIBRARIES = {
    'anthropic': IMPORT_ALL_MODULES.format(
        packages=('anthropic',),
        # Optional HTTP transport without model definitions.
        excluded=('anthropic._vendor.httpx_aiohttp',),
    ),
    'mcp': IMPORT_ALL_MODULES.format(
        packages=('mcp', 'mcp_types'),
        # Migration-error shim with no model definitions.
        excluded=('mcp.server.fastmcp',),
    ),
    'openai': IMPORT_ALL_MODULES.format(
        packages=('openai',),
        # Optional audio/WebSocket integrations; none defines Pydantic models.
        excluded=(
            'openai._vendor.httpx_aiohttp',
            'openai.helpers',
            'openai.lib._azure_websocket',
            'openai.lib._websocket',
        ),
    ),
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
