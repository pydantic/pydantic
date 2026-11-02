"""Check the MCP corpus's frozen runtime generic-model inventory."""

from pathlib import Path

import pytest

from .model_corpus import CorpusImporter

pytestmark = pytest.mark.thread_unsafe


def test_mcp_corpus_generic_models() -> None:
    corpus = CorpusImporter(Path(__file__).parent / 'corpus' / 'mcp')
    first = {f'{model.__module__}:{model.__name__}': model for model in corpus.build_models()}
    second = {f'{model.__module__}:{model.__name__}': model for model in corpus.build_models()}
    # Generic display names vary across Python versions, but counts and fresh
    # identities must agree across successive builds in the same interpreter.
    assert first.keys() == second.keys()
    assert len(first) == len(corpus.manifest['models'])
    assert all(first[name] is not second[name] for name in first)
