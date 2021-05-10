"""
Tests for annotated types that _pydantic_ can validate like
- NamedTuple
- TypedDict
"""
import json
import sys
from collections import namedtuple
from typing import List, NamedTuple, Tuple

import pytest
from typing_extensions import TypedDict

from pydantic import BaseModel, ValidationError

if sys.version_info < (3, 9):
    try:
        from typing import TypedDict as LegacyTypedDict
    except ImportError:
        LegacyTypedDict = None

else:
    LegacyTypedDict = None


def test_namedtuple():
    Position = namedtuple('Pos', 'x y')

    class Event(NamedTuple):
        a: int
        b: int
        c: int
        d: str

    class Model(BaseModel):
        pos: Position
        events: List[Event]

    model = Model(pos=('1', 2), events=[[b'1', '2', 3, 'qwe']])
    assert isinstance(model.pos, Position)
    assert isinstance(model.events[0], Event)
    assert model.pos.x == '1'
    assert model.pos == Position('1', 2)
    assert model.events[0] == Event(1, 2, 3, 'qwe')
    assert repr(model) == "Model(pos=Pos(x='1', y=2), events=[Event(a=1, b=2, c=3, d='qwe')])"
    assert model.json() == json.dumps(model.dict()) == '{"pos": ["1", 2], "events": [[1, 2, 3, "qwe"]]}'

    with pytest.raises(ValidationError) as exc_info:
        Model(pos=('1', 2), events=[['qwe', '2', 3, 'qwe']])
    assert exc_info.value.errors() == [
        {
            'loc': ('events', 0, 'a'),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
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

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'pos1': {
                'title': 'Pos1',
                'type': 'array',
                'items': [
                    {'title': 'X', 'type': 'integer'},
                    {'title': 'Y', 'type': 'integer'},
                ],
            },
            'pos2': {
                'title': 'Pos2',
                'type': 'array',
                'items': [
                    {'title': 'X'},
                    {'title': 'Y'},
                ],
            },
            'pos3': {
                'title': 'Pos3',
                'type': 'array',
                'items': [
                    {'type': 'integer'},
                    {'type': 'integer'},
                ],
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
    assert exc_info.value.errors() == [
        {
            'loc': ('p',),
            'msg': 'ensure this value has at most 2 items',
            'type': 'value_error.list.max_items',
            'ctx': {'limit_value': 2},
        }
    ]


def test_typeddict():
    class TD(TypedDict):
        a: int
        b: int
        c: int
        d: str

    class Model(BaseModel):
        td: TD

    m = Model(td={'a': '3', 'b': b'1', 'c': 4, 'd': 'qwe'})
    assert m.td == {'a': 3, 'b': 1, 'c': 4, 'd': 'qwe'}

    with pytest.raises(ValidationError) as exc_info:
        Model(td={'a': [1], 'b': 2, 'c': 3, 'd': 'qwe'})
    assert exc_info.value.errors() == [
        {
            'loc': ('td', 'a'),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        }
    ]


def test_typeddict_non_total():
    class FullMovie(TypedDict, total=True):
        name: str
        year: int

    class Model(BaseModel):
        movie: FullMovie

    with pytest.raises(ValidationError) as exc_info:
        Model(movie={'year': '2002'})
    assert exc_info.value.errors() == [
        {
            'loc': ('movie', 'name'),
            'msg': 'field required',
            'type': 'value_error.missing',
        }
    ]

    class PartialMovie(TypedDict, total=False):
        name: str
        year: int

    class Model(BaseModel):
        movie: PartialMovie

    m = Model(movie={'year': '2002'})
    assert m.movie == {'year': 2002}


def test_partial_new_typeddict():
    class OptionalUser(TypedDict, total=False):
        name: str

    class User(OptionalUser):
        id: int

    class Model(BaseModel):
        user: User

    m = Model(user={'id': 1})
    assert m.user == {'id': 1}


@pytest.mark.skipif(not LegacyTypedDict, reason='python 3.9+ is used, no legacy TypedDict')
def test_partial_legacy_typeddict():
    class OptionalUser(LegacyTypedDict, total=False):
        name: str

    class User(OptionalUser):
        id: int

    with pytest.raises(TypeError, match='^You should use `typing_extensions.TypedDict` instead of `typing.TypedDict`'):

        class Model(BaseModel):
            user: User


def test_typeddict_extra():
    class User(TypedDict):
        name: str
        age: int

    class Model(BaseModel):
        u: User

        class Config:
            extra = 'forbid'

    with pytest.raises(ValidationError) as exc_info:
        Model(u={'name': 'pika', 'age': 7, 'rank': 1})
    assert exc_info.value.errors() == [
        {'loc': ('u', 'rank'), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'},
    ]


def test_typeddict_schema():
    class Data(BaseModel):
        a: int

    class DataTD(TypedDict):
        a: int

    class Model(BaseModel):
        data: Data
        data_td: DataTD

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'data': {'$ref': '#/definitions/Data'}, 'data_td': {'$ref': '#/definitions/DataTD'}},
        'required': ['data', 'data_td'],
        'definitions': {
            'Data': {
                'type': 'object',
                'title': 'Data',
                'properties': {'a': {'title': 'A', 'type': 'integer'}},
                'required': ['a'],
            },
            'DataTD': {
                'type': 'object',
                'title': 'DataTD',
                'properties': {'a': {'title': 'A', 'type': 'integer'}},
                'required': ['a'],
            },
        },
    }
