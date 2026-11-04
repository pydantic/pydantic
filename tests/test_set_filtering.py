import json
from typing import Any

import pytest
from pydantic_core import PydanticSerializationError

from pydantic import BaseModel, ConfigDict, TypeAdapter


@pytest.mark.parametrize('collection', [set, frozenset])
@pytest.mark.parametrize('typed', [False, True])
@pytest.mark.parametrize('mode', ['python', 'json', 'json_bytes'])
@pytest.mark.parametrize('operation', ['include', 'exclude'])
def test_set_all_nested_filter(collection, typed, mode, operation):
    """https://github.com/pydantic/pydantic/issues/11101"""
    adapter = TypeAdapter(collection[tuple[int, int]] if typed else Any)
    value = collection([(1, 2), (3, 4)])
    filters = {operation: {'__all__': {0 if operation == 'include' else 1}}}
    if mode == 'json_bytes':
        result = json.loads(adapter.dump_json(value, **filters))
    else:
        result = adapter.dump_python(value, mode=mode, **filters)
    assert sorted(tuple(item) for item in result) == [(1,), (3,)]
    if mode == 'python':
        assert type(result) is collection


@pytest.mark.parametrize('collection', [set, frozenset])
@pytest.mark.parametrize('typed', [False, True])
@pytest.mark.parametrize('mode', ['python', 'json', 'json_bytes'])
@pytest.mark.parametrize('operation', ['include', 'exclude'])
def test_set_all_entire_items(collection, typed, mode, operation):
    """https://github.com/pydantic/pydantic/issues/11101"""
    adapter = TypeAdapter(collection[int] if typed else Any)
    value = collection([1, 2])
    filters = {operation: {'__all__'}}
    if mode == 'json_bytes':
        result = json.loads(adapter.dump_json(value, **filters))
    else:
        result = adapter.dump_python(value, mode=mode, **filters)
    assert sorted(result) == ([1, 2] if operation == 'include' else [])


@pytest.mark.parametrize('collection', [set, frozenset])
@pytest.mark.parametrize('operation', ['include', 'exclude'])
@pytest.mark.parametrize('invalid', [{0}, {0: True}, {'__all__': {0}, -1: True}])
def test_set_rejects_index_filters(collection, operation, invalid):
    """https://github.com/pydantic/pydantic/issues/11101"""
    adapter = TypeAdapter(collection[int])
    with pytest.raises(TypeError, match='__all__'):
        adapter.dump_python(collection([1]), **{operation: invalid})
    with pytest.raises(PydanticSerializationError, match='__all__'):
        adapter.dump_json(collection([1]), **{operation: invalid})


@pytest.mark.parametrize('collection', [set, frozenset])
def test_set_nested_model_filter(collection):
    """https://github.com/pydantic/pydantic/issues/11101"""

    class Item(BaseModel):
        model_config = ConfigDict(frozen=True)
        name: str
        secret: str

    class Container(BaseModel):
        items: collection[Item]
        other: int = 1

    model = Container(items=collection([Item(name='a', secret='hidden')]))
    options = {'include': {'items': {'__all__': {'name', 'secret'}}}, 'exclude': {'items': {'__all__': {'secret'}}}}
    assert model.model_dump(mode='json', **options) == {'items': [{'name': 'a'}]}
    assert json.loads(model.model_dump_json(**options)) == {'items': [{'name': 'a'}]}
    assert json.loads(model.model_dump_json())['items'] == [{'name': 'a', 'secret': 'hidden'}]
