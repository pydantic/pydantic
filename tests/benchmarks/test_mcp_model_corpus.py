"""Build all frozen MCP model graphs without importing the installed SDK."""

import ast
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import CodeType, ModuleType

import pytest

from pydantic import BaseModel

CORPUS = Path(__file__).parent / 'corpus' / 'mcp'
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
SOURCES: dict[str, tuple[CodeType, bool]] = {}
for source in sorted(CORPUS.rglob('*.py')):
    parts = source.relative_to(CORPUS).with_suffix('').parts
    is_package = parts[-1] == '__init__'
    name = '.'.join(parts[:-1] if is_package else parts)
    SOURCES[name] = compile(source.read_text(), str(source), 'exec'), is_package


def is_corpus_module(name: str) -> bool:
    return name.split('.')[0] in ('mcp', 'mcp_types')


class CorpusImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(
        self, fullname: str, path: Sequence[str] | None = None, target: ModuleType | None = None
    ) -> importlib.machinery.ModuleSpec | None:
        if not is_corpus_module(fullname):
            return None
        if fullname not in SOURCES:
            raise ModuleNotFoundError(f'Module missing from frozen MCP corpus: {fullname}', name=fullname)
        return importlib.util.spec_from_loader(fullname, self, is_package=SOURCES[fullname][1])

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> None:
        return None

    def exec_module(self, module: ModuleType) -> None:
        exec(SOURCES[module.__name__][0], module.__dict__)


def build_models() -> list[type[BaseModel]]:
    previous = {name: module for name, module in sys.modules.copy().items() if is_corpus_module(name)}
    for name in previous:
        sys.modules.pop(name)
    importer = CorpusImporter()
    sys.meta_path.insert(0, importer)
    try:
        modules = [importlib.import_module(name) for name in MANIFEST['declarations']]
        models = list(
            dict.fromkeys(
                value
                for module in modules
                for value in vars(module).values()
                if isinstance(value, type) and issubclass(value, BaseModel) and is_corpus_module(value.__module__)
            )
        )
        for model in sorted(models, key=lambda cls: (cls.__module__, cls.__name__)):
            model.model_rebuild()
        return models
    finally:
        sys.meta_path.remove(importer)
        for name in list(sys.modules):
            if is_corpus_module(name):
                sys.modules.pop(name)
        sys.modules.update(previous)


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
