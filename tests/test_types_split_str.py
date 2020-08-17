from typing import Optional, Union

import pytest

from pydantic import BaseModel, CommaSeparated, CommaSeparatedStripped, SpaceSeparated, ValidationError


def test_comma_separated_int_from_str():
    class Model(BaseModel):
        v: CommaSeparated[int] = []

    m = Model(v='1,2,3')
    assert m.v == [1, 2, 3]


def test_comma_separated_int_from_list():
    class Model(BaseModel):
        v: CommaSeparated[int] = []

    m = Model(v=[1, 2, 3])
    assert m.v == [1, 2, 3]


def test_comma_separated_int_default():
    class Model(BaseModel):
        v: CommaSeparated[int] = []

    m = Model()
    assert m.v == []


def test_comma_separated_int_none():
    class Model(BaseModel):
        v: CommaSeparated[int] = None

    m = Model()
    assert m.v is None


def test_comma_separated_int_optional():
    class Model(BaseModel):
        v: Optional[CommaSeparated[int]] = None

    m = Model()
    assert m.v is None


def test_comma_separated_int_optional_str():
    class Model(BaseModel):
        v: Optional[CommaSeparated[int]] = None

    m = Model(v='2,3,4')
    assert m.v == [2, 3, 4]


def test_comma_separated_int_optional_required():
    class Model(BaseModel):
        v: Optional[CommaSeparated[int]]

    m = Model(v=None)
    assert m.v is None


def test_comma_separated_int_invalid_str():
    class Model(BaseModel):
        v: CommaSeparated[int] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v='foo,bar')

    assert exc_info.value.errors() == [
        {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_comma_separated_int_invalid_list():
    class Model(BaseModel):
        v: CommaSeparated[int] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v=['foo', 'bar'])

    assert exc_info.value.errors() == [
        {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_comma_separated_int_invalid_value():
    class Model(BaseModel):
        v: CommaSeparated[int] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v={'foo': 'bar'})

    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_comma_separated_int_required():
    class Model(BaseModel):
        v: CommaSeparated[int]

    with pytest.raises(ValidationError) as exc_info:
        Model()

    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_space_separated_int_from_str():
    class Model(BaseModel):
        v: SpaceSeparated[int] = []

    m = Model(v='1 234 5678')
    assert m.v == [1, 234, 5678]


def test_space_separated_int_from_list():
    class Model(BaseModel):
        v: SpaceSeparated[int] = []

    m = Model(v=[1, 2, 3])
    assert m.v == [1, 2, 3]


def test_space_separated_int_default():
    class Model(BaseModel):
        v: SpaceSeparated[int] = []

    m = Model()
    assert m.v == []


def test_space_separated_int_none():
    class Model(BaseModel):
        v: SpaceSeparated[int] = None

    m = Model()
    assert m.v is None


def test_space_separated_int_optional():
    class Model(BaseModel):
        v: Optional[SpaceSeparated[int]] = None

    m = Model()
    assert m.v is None


def test_space_separated_int_optional_str():
    class Model(BaseModel):
        v: Optional[SpaceSeparated[int]] = None

    m = Model(v='2 3 4')
    assert m.v == [2, 3, 4]


def test_space_separated_int_optional_none():
    class Model(BaseModel):
        v: Optional[SpaceSeparated[int]] = None

    m = Model(v=None)
    assert m.v == None


def test_space_separated_int_invalid_str():
    class Model(BaseModel):
        v: SpaceSeparated[int] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v='foo bar')

    assert exc_info.value.errors() == [
        {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_space_separated_int_invalid_list():
    class Model(BaseModel):
        v: SpaceSeparated[int] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v=['foo', 'bar'])

    assert exc_info.value.errors() == [
        {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_space_separated_int_required():
    class Model(BaseModel):
        v: SpaceSeparated[int]

    with pytest.raises(ValidationError) as exc_info:
        Model()

    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_space_separated_int_invalid_value():
    class Model(BaseModel):
        v: SpaceSeparated[int] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v={'foo': 'bar'})

    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_comma_separated_str_spaces():
    class Model(BaseModel):
        v: CommaSeparated[str] = []

    m = Model(v='foo ,  bar ,baz \n')
    assert m.v == ['foo ', '  bar ', 'baz \n']


def test_comma_separated_stripped_str():
    class Model(BaseModel):
        v: CommaSeparatedStripped[str] = []

    m = Model(v='foo ,  bar ,baz \n')
    assert m.v == ['foo', 'bar', 'baz']


def test_comma_separated_stripped_list():
    class Model(BaseModel):
        v: CommaSeparatedStripped[str] = []

    m = Model(v=['foo ', '  bar ', 'baz \n'])
    assert m.v == ['foo ', '  bar ', 'baz \n']


def test_comma_separated_stripped_optional_none():
    class Model(BaseModel):
        v: Optional[CommaSeparatedStripped[int]] = None

    m = Model(v=None)
    assert m.v == None


def test_comma_separated_stripped_invalid():
    class Model(BaseModel):
        v: CommaSeparatedStripped[str] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v={'foo': 'bar'})

    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_comma_separated_union_str():
    class Model(BaseModel):
        v: CommaSeparatedStripped[Union[bool, float]] = []

    m = Model(v='true, 3, 0, FALSE, 3.14159')
    assert m.v == [True, 3, False, False, 3.14159]


def test_comma_separated_union_list():
    class Model(BaseModel):
        v: CommaSeparatedStripped[Union[bool, float]] = []

    m = Model(v=[True, 3, 0, False, 3.14159])
    assert m.v == [True, 3, False, False, 3.14159]


def test_comma_separated_union_str_invalid():
    class Model(BaseModel):
        v: CommaSeparatedStripped[Union[bool, int]] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v='true, 3, 0, FALSE, 3.14159')

    assert exc_info.value.errors() == [
        {'loc': ('v', 4), 'msg': 'value could not be parsed to a boolean', 'type': 'type_error.bool'},
        {'loc': ('v', 4), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_comma_separated_sub_model():
    class Model(BaseModel):
        v: CommaSeparatedStripped[Union[bool, float]] = []

    class SuperModel(BaseModel):
        data: Model

    m = SuperModel(data={'v': 'true, 3, 0, FALSE, 3.14159'})
    assert m.data.v == [True, 3, False, False, 3.14159]


def test_comma_separated_sub_model_invalid():
    class Model(BaseModel):
        v: CommaSeparatedStripped[Union[bool, int]] = []

    class SuperModel(BaseModel):
        data: Model

    with pytest.raises(ValidationError) as exc_info:
        SuperModel(data={'v': 'true, 3, 0, FALSE, 3.14159'})

    assert exc_info.value.errors() == [
        {'loc': ('data', 'v', 4), 'msg': 'value could not be parsed to a boolean', 'type': 'type_error.bool'},
        {'loc': ('data', 'v', 4), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_split_str_schema():
    class Model(BaseModel):
        comma_separated_stripped: CommaSeparatedStripped[int] = []
        comma_separated_union: CommaSeparated[Union[bool, float]] = []
        space_separated_required: SpaceSeparated[str]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'comma_separated_stripped': {
                'title': 'Comma Separated Stripped',
                'default': [],
                'anyOf': [{'type': 'array', 'items': {'type': 'integer'}}, {'type': 'string'}],
            },
            'comma_separated_union': {
                'title': 'Comma Separated Union',
                'default': [],
                'anyOf': [
                    {'type': 'array', 'items': {'anyOf': [{'type': 'boolean'}, {'type': 'number'}]}},
                    {'type': 'string'},
                ],
            },
            'space_separated_required': {
                'title': 'Space Separated Required',
                'anyOf': [{'type': 'array', 'items': {'type': 'string'}}, {'type': 'string'}],
            },
        },
        'required': ['space_separated_required'],
    }
