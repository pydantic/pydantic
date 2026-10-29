"""Measure library startup in a fresh interpreter, including Python startup and shutdown."""

import importlib.metadata
import subprocess
import sys
from collections.abc import Callable

import pytest

IMPORT_ALL_MODULES = """\
import importlib
import pkgutil
from types import ModuleType

from pydantic import BaseModel

modules: list[ModuleType] = []

def import_all(name: str) -> None:
    if name in {excluded!r} or name.rsplit('.', 1)[-1] in ('__main__', 'cli'):
        return
    module = importlib.import_module(name)
    modules.append(module)
    if hasattr(module, '__path__'):
        for child in pkgutil.iter_modules(module.__path__, module.__name__ + '.'):
            import_all(child.name)

for name in {packages!r}:
    import_all(name)

# Wait for all modules so forward references can resolve before building schemas.
models = {{
    value
    for module in modules
    for value in vars(module).values()
    if isinstance(value, type) and issubclass(value, BaseModel) and value is not BaseModel
}}
for model in sorted(models, key=lambda cls: (cls.__module__, cls.__qualname__)):
    model.model_rebuild()
"""

# Distributions pinned in the `benchmark-startup` dependency group, mapped to the code
# run in the child interpreter.
LIBRARIES = {
    'anthropic': IMPORT_ALL_MODULES.format(
        packages=('anthropic',),
        # Optional HTTP transport without model definitions.
        excluded=('anthropic._vendor.httpx_aiohttp',),
    ),
    'google-genai': IMPORT_ALL_MODULES.format(
        packages=('google.genai',),
        # Bundled tests/test harness and optional tokenizers, without production models.
        excluded=(
            'google.genai.tests',
            'google.genai._test_api_client',
            'google.genai._local_tokenizer_loader',
            'google.genai.local_tokenizer',
        ),
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
        subprocess.run([sys.executable, '-X', 'perf', '-c', code], check=True)

    benchmark(run)
