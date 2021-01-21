"""
Tests for annotated types that _pydantic_ can validate like
- NamedTuple
- TypedDict
"""
import sys
from collections import namedtuple
from typing import List, NamedTuple

if sys.version_info < (3, 9):
    try:
        from typing import TypedDict as LegacyTypedDict
    except ImportError:
        LegacyTypedDict = None

    try:
        from typing_extensions import TypedDict
    except ImportError:
        TypedDict = None
else:
    from typing import TypedDict

    LegacyTypedDict = None

import pytest

from pydantic import BaseModel, ValidationError


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

    with pytest.raises(ValidationError) as exc_info:
        Model(pos=('1', 2), events=[['qwe', '2', 3, 'qwe']])
    assert exc_info.value.errors() == [
        {
            'loc': ('events', 0, 'a'),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        }
    ]


@pytest.mark.skipif(not TypedDict, reason='typing_extensions not installed')
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


@pytest.mark.skipif(not TypedDict, reason='typing_extensions not installed')
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


@pytest.mark.skipif(not TypedDict, reason='typing_extensions not installed')
def test_partial_new_typeddict():
    class OptionalUser(TypedDict, total=False):
        name: str

    class User(OptionalUser):
        id: int

    class Model(BaseModel):
        user: User

    m = Model(user={'id': 1})
    assert m.user == {'id': 1}


@pytest.mark.skipif(not LegacyTypedDict, reason='python 3.9+ is used or typing_extensions is installed')
def test_partial_legacy_typeddict():
    class OptionalUser(LegacyTypedDict, total=False):
        name: str

    class User(OptionalUser):
        id: int

    with pytest.warns(
        UserWarning,
        match='You should use `typing_extensions.TypedDict` instead of `typing.TypedDict` for better support!',
    ):

        class Model(BaseModel):
            user: User

        with pytest.raises(ValidationError) as exc_info:
            Model(user={'id': 1})
        assert exc_info.value.errors() == [
            {
                'loc': ('user', 'name'),
                'msg': 'field required',
                'type': 'value_error.missing',
            }
        ]


@pytest.mark.skipif(not TypedDict, reason='typing_extensions not installed')
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


@pytest.mark.skipif(not TypedDict, reason='typing_extensions not installed')
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
