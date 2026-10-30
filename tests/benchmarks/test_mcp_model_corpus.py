"""Build a frozen graph of real MCP models without importing the SDK."""

import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

from pydantic import BaseModel

SOURCE = Path(__file__).parent / 'corpus' / 'mcp' / 'models.py.txt'
CODE = compile(SOURCE.read_text(), str(SOURCE), 'exec')


def build_models() -> list[type[BaseModel]]:
    module = ModuleType('_pydantic_benchmark_mcp_corpus')
    previous = sys.modules.get(module.__name__)
    sys.modules[module.__name__] = module
    try:
        exec(CODE, module.__dict__)
        models = list(
            dict.fromkeys(
                value
                for value in vars(module).values()
                if isinstance(value, type) and issubclass(value, BaseModel) and value.__module__ == module.__name__
            )
        )
        for model in models:
            model.model_rebuild()
        return models
    finally:
        if previous is None:
            sys.modules.pop(module.__name__, None)
        else:
            sys.modules[module.__name__] = previous


def test_mcp_model_corpus(benchmark: Callable[[Callable[[], list[type[BaseModel]]]], list[type[BaseModel]]]) -> None:
    models = benchmark(build_models)
    assert len(models) == 189
    assert all(model.__pydantic_complete__ for model in models)


def test_mcp_corpus_fresh_models() -> None:
    first = {model.__name__: model for model in build_models()}
    second = {model.__name__: model for model in build_models()}
    assert first.keys() == second.keys()
    assert all(first[name] is not second[name] for name in first)
    assert '_pydantic_benchmark_mcp_corpus' not in sys.modules
    request = first['ReadResourceRequest'].model_validate(
        {'method': 'resources/read', 'params': {'uri': 'file:///example.txt'}}
    )
    assert request.model_dump(by_alias=True)['params']['uri'] == 'file:///example.txt'
