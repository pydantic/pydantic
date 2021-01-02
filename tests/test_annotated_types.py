"""
Tests for annotated types that _pydantic_ can validate like
- NamedTuple
- TypedDict
"""
import sys
from collections import namedtuple
from typing import List, NamedTuple

if sys.version_info < (3, 8):
    try:
        from typing import TypedDict
    except ImportError:
        TypedDict = None
else:
    from typing import TypedDict

import pytest

from pydantic import BaseModel, ValidationError


def test_named_tuple():
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
def test_typed_dict():
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
def test_typed_dict_non_total():
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
