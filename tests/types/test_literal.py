import typing
from typing import Literal

import pytest
import typing_extensions

from pydantic import TypeAdapter, ValidationError, create_model


def test_literal_single():
    ta = TypeAdapter(Literal['a'])

    assert ta.validate_python('a') == 'a'
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('b')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be 'a'",
            'input': 'b',
            'ctx': {'expected': "'a'"},
        }
    ]


def test_literal_multiple():
    ta = TypeAdapter(Literal['a', 'b'])

    assert ta.validate_python('a') == 'a'
    assert ta.validate_python('b') == 'b'
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('c')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be 'a' or 'b'",
            'input': 'c',
            'ctx': {'expected': "'a' or 'b'"},
        }
    ]


@pytest.mark.parametrize(
    'typing_literal',
    [
        pytest.param(typing.Literal, id='typing.Literal'),
        pytest.param(typing_extensions.Literal, id='typing_extensions.Literal'),
    ],
)
def test_literal_field(typing_literal):
    ta = TypeAdapter(typing_literal['foo'])

    assert ta.validate_python('foo') == 'foo'


@pytest.mark.thread_unsafe
@pytest.mark.parametrize(
    'values',
    [
        ['x' * 8192],
        ['😀' * 4096],
        [b'x' * 8192],
        [f'value-{i:04}-xxxxxxxxxxxxxxxx' for i in range(256)],
    ],
    ids=['string', 'unicode', 'bytes', 'many-small-values'],
)
@pytest.mark.parametrize('shape', ['T', 'list[T]', 'dict[str, T]', 'T | None'])
def test_oversized_literal_bypasses_schema_cache(
    values: list[typing.Any], shape: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """https://github.com/pydantic/pydantic/pull/13542#discussion_r3907667492"""
    from pydantic._internal import _generate_schema

    cache = {}
    monkeypatch.setattr(_generate_schema, '_pure_annotation_schema_cache', cache)
    annotation = eval(shape, {'T': Literal[tuple(values)]})
    value = values[0]
    invalid = 'not a literal'
    if shape == 'list[T]':
        value, invalid = [value], [invalid]
    elif shape == 'dict[str, T]':
        value, invalid = {'a': value}, {'a': invalid}

    for _ in range(2):
        model = create_model('Model', v=(annotation, ...))
        assert cache == {}
        assert model(v=value).v == value
        with pytest.raises(ValidationError, check=lambda err: err.errors()[0]['type'] == 'literal_error'):
            model(v=invalid)


@pytest.mark.thread_unsafe
def test_literal_budget_is_shared_across_nested_annotations(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic._internal import _generate_schema, _schema_cache

    # Keep individual values within the field cache's cap while exceeding the total budget.
    monkeypatch.setattr(_schema_cache, 'PURE_ANNOTATION_MAX_LITERAL_BYTES', 4096)
    cache = {}
    monkeypatch.setattr(_generate_schema, '_pure_annotation_schema_cache', cache)
    a, b, c, d, e, f = [chr(i) * 1000 for i in range(97, 103)]
    annotation = tuple[Literal[a], list[Literal[b]], dict[str, Literal[c]], Literal[d], Literal[e], Literal[f]]
    model = create_model('Model', v=(annotation, ...))
    value = (a, [b], {'c': c}, d, e, f)
    assert model(v=value).v == value
    assert cache == {}

    # Each component fits independently; only their combined payload is oversized.
    for component in (Literal[a], list[Literal[b]], dict[str, Literal[c]]):
        create_model('Small', v=(component, ...))
    assert len(cache) == 3


@pytest.mark.thread_unsafe
def test_small_literals_remain_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic._internal import _generate_schema

    cache = {}
    monkeypatch.setattr(_generate_schema, '_pure_annotation_schema_cache', cache)
    for _ in range(2):
        model = create_model('Model', v=(list[Literal['a', 'b']], ...))
        assert model(v=['a', 'b']).v == ['a', 'b']
        assert len(cache) == 1
