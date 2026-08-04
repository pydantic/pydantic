import collections
import typing
from collections import OrderedDict

import pytest

from pydantic import BaseModel, ValidationError


def test_ordered_dict():
    class Model(BaseModel):
        v: OrderedDict

    assert Model(v=OrderedDict([(1, 10), (2, 20)])).v == OrderedDict([(1, 10), (2, 20)])
    assert Model(v={1: 10, 2: 20}).v == OrderedDict([(1, 10), (2, 20)])

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': ('v',), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.OrderedDict, id='typing.OrderedDict'),
        pytest.param(collections.OrderedDict, id='collections.OrderedDict'),
    ],
)
def test_ordered_dict_from_ordered_dict(field_type):
    class Model(BaseModel):
        od_field: field_type

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    m = Model(od_field=od_value)

    assert isinstance(m.od_field, collections.OrderedDict)
    assert m.od_field == od_value
    # we don't make any promises about preserving instances
    # at the moment we always copy them for consistency and predictability
    # so this is more so documenting the current behavior than a promise
    # we make to users
    assert m.od_field is not od_value

    assert m.model_json_schema() == {
        'properties': {'od_field': {'title': 'Od Field', 'type': 'object', 'additionalProperties': True}},
        'required': ['od_field'],
        'title': 'Model',
        'type': 'object',
    }


def test_ordered_dict_from_ordered_dict_typed():
    class Model(BaseModel):
        od_field: typing.OrderedDict[str, int]

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    m = Model(od_field=od_value)

    assert isinstance(m.od_field, collections.OrderedDict)
    assert m.od_field == od_value

    assert m.model_json_schema() == {
        'properties': {
            'od_field': {
                'additionalProperties': {'type': 'integer'},
                'title': 'Od Field',
                'type': 'object',
            }
        },
        'required': ['od_field'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.OrderedDict, id='typing.OrderedDict'),
        pytest.param(collections.OrderedDict, id='collections.OrderedDict'),
    ],
)
def test_ordered_dict_from_dict(field_type):
    class Model(BaseModel):
        od_field: field_type

    od_value = {'a': 1, 'b': 2}

    m = Model(od_field=od_value)

    assert isinstance(m.od_field, collections.OrderedDict)
    assert m.od_field == collections.OrderedDict(od_value)

    assert m.model_json_schema() == {
        'properties': {'od_field': {'title': 'Od Field', 'type': 'object', 'additionalProperties': True}},
        'required': ['od_field'],
        'title': 'Model',
        'type': 'object',
    }
