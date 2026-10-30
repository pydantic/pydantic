"""Build complete frozen SDK model graphs under CPU simulation."""

import ast
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from pydantic import BaseModel

from .model_corpus import CorpusImporter

# Import isolation changes process-wide module state.
pytestmark = pytest.mark.thread_unsafe
LIBRARIES = ['openai', 'anthropic']


@pytest.fixture(scope='module', params=LIBRARIES)
def corpus(request: pytest.FixtureRequest) -> CorpusImporter:
    return CorpusImporter(Path(__file__).parent / 'corpus' / request.param)


def test_sdk_model_corpus(
    benchmark: Callable[[Callable[[], list[type[BaseModel]]]], list[type[BaseModel]]], corpus: CorpusImporter
) -> None:
    models = benchmark(corpus.build_models)
    # Source declaration identities are stable even when generic display names vary.
    actual = {
        f'{model.__module__}:{model.__name__}'
        for model in models
        if model.__pydantic_generic_metadata__['origin'] is None
    }
    expected = {f'{module}:{name}' for module, names in corpus.manifest['declarations'].items() for name in names}
    assert actual == expected
    assert all(model.__pydantic_complete__ for model in models)


def test_sdk_corpus_fresh_models(corpus: CorpusImporter) -> None:
    before = {name: module for name, module in sys.modules.copy().items() if corpus.is_corpus_module(name)}
    first = corpus.build_models()
    second = corpus.build_models()
    assert len(first) == len(second)
    assert set(first).isdisjoint(second)
    assert {name: module for name, module in sys.modules.copy().items() if corpus.is_corpus_module(name)} == before


@pytest.mark.parametrize(
    ('code', 'error'),
    [('raise RuntimeError("broken corpus")', RuntimeError), ('import {root}.unvendored', ModuleNotFoundError)],
)
def test_sdk_corpus_import_failure(
    corpus: CorpusImporter, monkeypatch: pytest.MonkeyPatch, code: str, error: type[Exception]
) -> None:
    root = corpus.roots[0]
    monkeypatch.setitem(sys.modules, root, ModuleType(root))
    monkeypatch.setitem(corpus.sources, root, (compile(code.format(root=root), '<broken corpus>', 'exec'), True))
    before = {name: module for name, module in sys.modules.copy().items() if corpus.is_corpus_module(name)}
    importers = sys.meta_path.copy()
    with pytest.raises(error):
        corpus.build_models()
    assert {name: module for name, module in sys.modules.copy().items() if corpus.is_corpus_module(name)} == before
    assert sys.meta_path == importers


def test_sdk_corpus_syntax(corpus: CorpusImporter) -> None:
    minimum = tuple(corpus.manifest['minimum_python'])
    for source in corpus.directory.rglob('*.py'):
        ast.parse(source.read_text(), filename=str(source), feature_version=minimum)


def test_sdk_corpus_validation(corpus: CorpusImporter) -> None:
    models = {f'{model.__module__}:{model.__name__}': model for model in corpus.build_models()}
    model, data = {
        'openai': (
            'openai.types.completion_usage:CompletionUsage',
            {'completion_tokens': 1, 'prompt_tokens': 2, 'total_tokens': 3},
        ),
        'anthropic': ('anthropic.types.usage:Usage', {'input_tokens': 2, 'output_tokens': 1}),
        'google-genai': ('google.genai.types:Content', {'role': 'user', 'parts': [{'text': 'hello'}]}),
    }[corpus.directory.name]
    result = models[model].model_validate(data).model_dump(exclude_none=True)
    for name, value in data.items():
        assert result[name] == value
