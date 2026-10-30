"""Verify the frozen MCP model graph and its isolated importer."""

import ast
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from pydantic import BaseModel

from .model_corpus import CorpusImporter

# Each run temporarily replaces process-wide modules and import hooks.
pytestmark = pytest.mark.thread_unsafe

CORPUS = Path(__file__).parent / 'corpus' / 'mcp'
IMPORTER = CorpusImporter(CORPUS)
MANIFEST = IMPORTER.manifest
SOURCES = IMPORTER.sources
build_models = IMPORTER.build_models
is_corpus_module = IMPORTER.is_corpus_module


def test_mcp_model_corpus(benchmark: Callable[[Callable[[], list[type[BaseModel]]]], list[type[BaseModel]]]) -> None:
    models = benchmark(build_models)
    # Generated generic class names differ between supported Python versions.
    assert len(models) == len(MANIFEST['models'])
    declarations = {
        f'{model.__module__}:{model.__name__}'
        for model in models
        if model.__pydantic_generic_metadata__['origin'] is None
    }
    assert declarations == {f'{module}:{name}' for module, names in MANIFEST['declarations'].items() for name in names}
    assert all(model.__pydantic_complete__ for model in models)


def test_mcp_corpus_fresh_models() -> None:
    previous = {name: module for name, module in sys.modules.copy().items() if is_corpus_module(name)}
    first = {f'{model.__module__}:{model.__name__}': model for model in build_models()}
    second = {f'{model.__module__}:{model.__name__}': model for model in build_models()}
    assert first.keys() == second.keys()
    assert len(first) == len(MANIFEST['models'])
    assert all(first[name] is not second[name] for name in first)
    assert {name: module for name, module in sys.modules.copy().items() if is_corpus_module(name)} == previous
    request = first['mcp_types._types:ReadResourceRequest'].model_validate(
        {'method': 'resources/read', 'params': {'uri': 'file:///example.txt'}}
    )
    assert request.model_dump(by_alias=True)['params']['uri'] == 'file:///example.txt'


@pytest.mark.parametrize(
    ('code', 'error'),
    [('raise RuntimeError("broken corpus")', RuntimeError), ('import mcp.unvendored', ModuleNotFoundError)],
)
def test_mcp_corpus_import_failure(monkeypatch: pytest.MonkeyPatch, code: str, error: type[Exception]) -> None:
    sentinel = ModuleType('mcp')
    monkeypatch.setitem(sys.modules, 'mcp', sentinel)
    monkeypatch.setitem(SOURCES, 'mcp_types', (compile(code, '<broken corpus>', 'exec'), True))
    previous = {name: module for name, module in sys.modules.copy().items() if is_corpus_module(name)}
    previous_importers = sys.meta_path.copy()
    with pytest.raises(error):
        build_models()
    assert {name: module for name, module in sys.modules.copy().items() if is_corpus_module(name)} == previous
    assert sys.meta_path == previous_importers


def test_mcp_corpus_python310_syntax() -> None:
    for source in CORPUS.rglob('*.py'):
        ast.parse(source.read_text(), filename=str(source), feature_version=(3, 10))
