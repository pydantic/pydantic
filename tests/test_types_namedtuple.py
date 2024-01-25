from collections import namedtuple
from typing import Generic, NamedTuple, Optional, Tuple, TypeVar

import pytest
from typing_extensions import NamedTuple as TypingExtensionsNamedTuple

from pydantic import BaseModel, ConfigDict, PositiveInt, TypeAdapter, ValidationError
from pydantic.errors import PydanticSchemaGenerationError


def test_namedtuple_simple():
    Position = namedtuple('Pos', 'x y')

    class Model(BaseModel):
        pos: Position

    model = Model(pos=('1', 2))
    assert isinstance(model.pos, Position)
    assert model.pos.x == '1'
    assert model.pos == Position('1', 2)

    model = Model(pos={'x': '1', 'y': 2})
    assert model.pos == Position('1', 2)


def test_namedtuple():
    class Event(NamedTuple):
        a: int
        b: int
        c: int
        d: str

    class Model(BaseModel):
        # pos: Position
        event: Event

    model = Model(event=(b'1', '2', 3, 'qwe'))
    assert isinstance(model.event, Event)
    assert model.event == Event(1, 2, 3, 'qwe')
    assert repr(model) == "Model(event=Event(a=1, b=2, c=3, d='qwe'))"

    with pytest.raises(ValidationError) as exc_info:
        Model(pos=('1', 2), event=['qwe', '2', 3, 'qwe'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('event', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'qwe',
        }
    ]


def test_namedtuple_schema():
    class Position1(NamedTuple):
        x: int
        y: int

    Position2 = namedtuple('Position2', 'x y')

    class Model(BaseModel):
        pos1: Position1
        pos2: Position2
        pos3: Tuple[int, int]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        '$defs': {
            'Position1': {
                'maxItems': 2,
                'minItems': 2,
                'prefixItems': [{'title': 'X', 'type': 'integer'}, {'title': 'Y', 'type': 'integer'}],
                'type': 'array',
            },
            'Position2': {
                'maxItems': 2,
                'minItems': 2,
                'prefixItems': [{'title': 'X'}, {'title': 'Y'}],
                'type': 'array',
            },
        },
        'properties': {
            'pos1': {'$ref': '#/$defs/Position1'},
            'pos2': {'$ref': '#/$defs/Position2'},
            'pos3': {
                'maxItems': 2,
                'minItems': 2,
                'prefixItems': [{'type': 'integer'}, {'type': 'integer'}],
                'title': 'Pos3',
                'type': 'array',
            },
        },
        'required': ['pos1', 'pos2', 'pos3'],
    }


def test_namedtuple_right_length():
    class Point(NamedTuple):
        x: int
        y: int

    class Model(BaseModel):
        p: Point

    assert isinstance(Model(p=(1, 2)), Model)

    with pytest.raises(ValidationError) as exc_info:
        Model(p=(1, 2, 3))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'unexpected_positional_argument',
            'loc': ('p', 2),
            'msg': 'Unexpected positional argument',
            'input': 3,
        }
    ]


def test_namedtuple_postponed_annotation():
    """
    https://github.com/pydantic/pydantic/issues/2760
    """

    class Tup(NamedTuple):
        v: 'PositiveInt'

    class Model(BaseModel):
        t: Tup

    # The effect of issue #2760 is that this call raises a `PydanticUserError` even though the type declared on `Tup.v`
    # references a binding in this module's global scope.
    with pytest.raises(ValidationError):
        Model.model_validate({'t': [-1]})


def test_namedtuple_arbitrary_type():
    class CustomClass:
        pass

    class Tup(NamedTuple):
        c: CustomClass

    class Model(BaseModel):
        x: Tup

        model_config = ConfigDict(arbitrary_types_allowed=True)

    data = {'x': Tup(c=CustomClass())}
    model = Model.model_validate(data)
    assert isinstance(model.x.c, CustomClass)

    with pytest.raises(PydanticSchemaGenerationError):

        class ModelNoArbitraryTypes(BaseModel):
            x: Tup


def test_recursive_namedtuple():
    class MyNamedTuple(NamedTuple):
        x: int
        y: Optional['MyNamedTuple']

    ta = TypeAdapter(MyNamedTuple)
    assert ta.validate_python({'x': 1, 'y': {'x': 2, 'y': None}}) == (1, (2, None))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'x': 1, 'y': {'x': 2, 'y': {'x': 'a', 'y': None}}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('y', 'y', 'x'),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]


def test_recursive_generic_namedtuple():
    # Need to use TypingExtensionsNamedTuple to make it work with Python <3.11
    T = TypeVar('T')

    class MyNamedTuple(TypingExtensionsNamedTuple, Generic[T]):
        x: T
        y: Optional['MyNamedTuple[T]']

    ta = TypeAdapter(MyNamedTuple[int])
    assert ta.validate_python({'x': 1, 'y': {'x': 2, 'y': None}}) == (1, (2, None))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'x': 1, 'y': {'x': 2, 'y': {'x': 'a', 'y': None}}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('y', 'y', 'x'),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]


def test_namedtuple_defaults():
    class NT(NamedTuple):
        x: int
        y: int = 33

    assert TypeAdapter(NT).validate_python([1]) == (1, 33)
    assert TypeAdapter(NT).validate_python({'x': 22}) == (22, 33)


def test_eval_type_backport():
    class MyNamedTuple(NamedTuple):
        foo: 'list[int | str]'

    class Model(BaseModel):
        t: MyNamedTuple

    assert Model(t=([1, '2'],)).model_dump() == {'t': ([1, '2'],)}

    with pytest.raises(ValidationError) as exc_info:
        Model(t=('not a list',))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': ('t', 0),
            'msg': 'Input should be a valid list',
            'input': 'not a list',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(t=([{'not a str or int'}],))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_type',
            'loc': ('t', 0, 0, 'int'),
            'msg': 'Input should be a valid integer',
            'input': {'not a str or int'},
        },
        {
            'type': 'string_type',
            'loc': ('t', 0, 0, 'str'),
            'msg': 'Input should be a valid string',
            'input': {'not a str or int'},
        },
    ]
