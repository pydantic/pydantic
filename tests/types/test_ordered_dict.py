import collections
import typing
from collections import OrderedDict
from typing import Annotated

import pytest

from pydantic import Field, TypeAdapter, ValidationError


def test_ordered_dict():
    ta = TypeAdapter(OrderedDict)

    assert ta.validate_python(OrderedDict([(1, 10), (2, 20)])) == OrderedDict([(1, 10), (2, 20)])
    assert ta.validate_python({1: 10, 2: 20}) == OrderedDict([(1, 10), (2, 20)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.OrderedDict, id='typing.OrderedDict'),
        pytest.param(collections.OrderedDict, id='collections.OrderedDict'),
    ],
)
def test_ordered_dict_from_ordered_dict(field_type):
    ta = TypeAdapter(field_type)

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    v = ta.validate_python(od_value)

    assert isinstance(v, collections.OrderedDict)
    assert v == od_value
    # we don't make any promises about preserving instances
    # at the moment we always copy them for consistency and predictability
    # so this is more so documenting the current behavior than a promise
    # we make to users
    assert v is not od_value

    assert ta.json_schema() == {'type': 'object', 'additionalProperties': True}


def test_ordered_dict_from_ordered_dict_typed():
    ta = TypeAdapter(typing.OrderedDict[str, int])

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    v = ta.validate_python(od_value)

    assert isinstance(v, collections.OrderedDict)
    assert v == od_value

    assert ta.json_schema() == {
        'type': 'object',
        'additionalProperties': {'type': 'integer'},
    }


def test_ordered_dict_json_schema_with_length_constraints() -> None:
    ta = TypeAdapter(Annotated[OrderedDict[str, int], Field(min_length=1, max_length=3)])

    assert ta.json_schema() == {
        'type': 'object',
        'additionalProperties': {'type': 'integer'},
        'minProperties': 1,
        'maxProperties': 3,
    }


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.OrderedDict, id='typing.OrderedDict'),
        pytest.param(collections.OrderedDict, id='collections.OrderedDict'),
    ],
)
def test_ordered_dict_from_dict(field_type):
    ta = TypeAdapter(field_type)

    od_value = {'a': 1, 'b': 2}

    v = ta.validate_python(od_value)

    assert isinstance(v, collections.OrderedDict)
    assert v == collections.OrderedDict(od_value)
