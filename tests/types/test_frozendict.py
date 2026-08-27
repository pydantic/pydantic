import sys
from collections import OrderedDict
from typing import Annotated, Any

import pytest

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

if sys.version_info < (3, 15):
    pytest.skip(reason='The `frozendict` builtin type is only available in Python 3.15+', allow_module_level=True)
else:
    from builtins import frozendict


@pytest.mark.parametrize(
    'value,expected',
    [
        (frozendict({'1': 1, '2': 2}), frozendict({'1': 1, '2': 2})),
        ({'1': 1, '2': 2}, frozendict({'1': 1, '2': 2})),
        (OrderedDict({'1': 1, '2': 2}), frozendict({'1': 1, '2': 2})),
        ({'1': '1', '2': '2'}, frozendict({'1': 1, '2': 2})),
        ([('1', 1), ('2', 2)], ValidationError),
        ('not a mapping', ValidationError),
    ],
)
def test_frozendict_validation(value, expected) -> None:
    ta = TypeAdapter(frozendict[str, int])

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        result = ta.validate_python(value)
        assert result == expected
        assert isinstance(result, frozendict)


def test_frozendict_bare() -> None:
    ta = TypeAdapter(frozendict)

    result = ta.validate_python({'a': 1, 2: 'b'})
    assert result == frozendict({'a': 1, 2: 'b'})
    assert isinstance(result, frozendict)


def test_frozendict_json() -> None:
    ta = TypeAdapter(frozendict[str, int])

    result = ta.validate_json('{"a": 1}')
    assert result == frozendict({'a': 1})
    assert isinstance(result, frozendict)

    assert ta.dump_json(result) == b'{"a":1}'


def test_frozendict_strict() -> None:
    ta = TypeAdapter(frozendict[str, int], config={'strict': True})

    result = ta.validate_python(frozendict({'a': 1}))
    assert result == frozendict({'a': 1})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 1})
    assert exc_info.value.errors()[0]['type'] == 'frozen_dict_type'

    # a JSON object is the only way to create a frozendict from JSON, so it is allowed in strict mode:
    assert ta.validate_json('{"a": 1}') == frozendict({'a': 1})


def test_constrained_frozendict() -> None:
    ta = TypeAdapter(Annotated[frozendict[str, int], Field(min_length=1, max_length=2)])

    assert ta.validate_python({'a': 1}) == frozendict({'a': 1})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({})
    assert exc_info.value.errors()[0]['type'] == 'too_short'

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 1, 'b': 2, 'c': 3})
    assert exc_info.value.errors()[0]['type'] == 'too_long'


def test_frozendict_field() -> None:
    class Model(BaseModel):
        x: frozendict[str, int]
        y: frozendict = frozendict()

    m = Model(x={'a': '1'})
    assert m.x == frozendict({'a': 1})
    assert isinstance(m.x, frozendict)
    assert m.y == frozendict()

    assert m.model_dump() == {'x': frozendict({'a': 1}), 'y': frozendict()}
    assert isinstance(m.model_dump()['x'], frozendict)
    assert m.model_dump(mode='json') == {'x': {'a': 1}, 'y': {}}
    assert m.model_dump_json() == '{"x":{"a":1},"y":{}}'


def test_frozendict_nested() -> None:
    ta = TypeAdapter(frozendict[str, frozendict[str, int]])

    result = ta.validate_python({'a': {'b': '1'}})
    assert result == frozendict({'a': frozendict({'b': 1})})
    assert isinstance(result['a'], frozendict)


def test_frozendict_as_dict_key() -> None:
    # `frozendict` is hashable, so it can be used as a `dict` key:
    ta = TypeAdapter(dict[frozendict[str, int], int])

    result = ta.validate_python({frozendict({'a': 1}): 2})
    assert result == {frozendict({'a': 1}): 2}


def test_frozendict_json_schema() -> None:
    ta = TypeAdapter(frozendict[str, int])
    assert ta.json_schema() == {'type': 'object', 'additionalProperties': {'type': 'integer'}}

    ta = TypeAdapter(Annotated[frozendict[str, int], Field(min_length=1, max_length=2)])
    assert ta.json_schema() == {
        'type': 'object',
        'additionalProperties': {'type': 'integer'},
        'minProperties': 1,
        'maxProperties': 2,
    }

    ta = TypeAdapter(frozendict)
    assert ta.json_schema() == {'type': 'object', 'additionalProperties': True}


def test_frozendict_serialization_any() -> None:
    ta = TypeAdapter(Any)

    result = ta.dump_python(frozendict({'a': 1}))
    assert result == frozendict({'a': 1})
    assert isinstance(result, frozendict)

    assert ta.dump_python(frozendict({'a': 1}), mode='json') == {'a': 1}
    assert ta.dump_json(frozendict({'a': 1})) == b'{"a":1}'
