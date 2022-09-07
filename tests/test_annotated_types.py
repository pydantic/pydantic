"""
Tests for annotated types that _pydantic_ can validate like
- NamedTuple
- TypedDict
"""
import json
import sys
from collections import namedtuple
from typing import List, NamedTuple, Optional, Tuple

import pytest
from typing_extensions import Annotated, NotRequired, Required, TypedDict

from pydantic import BaseModel, Field, PositiveInt, ValidationError

if sys.version_info < (3, 9, 2):
    try:
        from typing import TypedDict as LegacyTypedDict
    except ImportError:
        LegacyTypedDict = None

else:
    LegacyTypedDict = None

if (3, 9, 2) < sys.version_info < (3, 11):
    from typing import TypedDict as LegacyRequiredTypedDict
else:
    LegacyRequiredTypedDict = None


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
                'minItems': 2,
                'maxItems': 2,
            },
            'pos2': {
                'title': 'Pos2',
                'type': 'array',
                'items': [
                    {'title': 'X'},
                    {'title': 'Y'},
                ],
                'minItems': 2,
                'maxItems': 2,
            },
            'pos3': {
                'title': 'Pos3',
                'type': 'array',
                'items': [
                    {'type': 'integer'},
                    {'type': 'integer'},
                ],
                'minItems': 2,
                'maxItems': 2,
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


def test_namedtuple_postponed_annotation():
    """
    https://github.com/pydantic/pydantic/issues/2760
    """

    class Tup(NamedTuple):
        v: 'PositiveInt'

    class Model(BaseModel):
        t: Tup

    # The effect of issue #2760 is that this call raises a `ConfigError` even though the type declared on `Tup.v`
    # references a binding in this module's global scope.
    with pytest.raises(ValidationError):
        Model.parse_obj({'t': [-1]})


def test_namedtuple_arbitrary_type():
    class CustomClass:
        pass

    class Tup(NamedTuple):
        c: CustomClass

    class Model(BaseModel):
        x: Tup

        class Config:
            arbitrary_types_allowed = True

    data = {'x': Tup(c=CustomClass())}
    model = Model.parse_obj(data)
    assert isinstance(model.x.c, CustomClass)

    with pytest.raises(RuntimeError):

        class ModelNoArbitraryTypes(BaseModel):
            x: Tup


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

    with pytest.raises(
        TypeError,
        match='^You should use `typing_extensions.TypedDict` instead of `typing.TypedDict` with Python < 3.9.2.',
    ):

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


def test_typeddict_postponed_annotation():
    class DataTD(TypedDict):
        v: 'PositiveInt'

    class Model(BaseModel):
        t: DataTD

    with pytest.raises(ValidationError):
        Model.parse_obj({'t': {'v': -1}})


def test_typeddict_required():
    class DataTD(TypedDict, total=False):
        a: int
        b: Required[str]

    class Model(BaseModel):
        t: DataTD

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'t': {'$ref': '#/definitions/DataTD'}},
        'required': ['t'],
        'definitions': {
            'DataTD': {
                'title': 'DataTD',
                'type': 'object',
                'properties': {
                    'a': {'title': 'A', 'type': 'integer'},
                    'b': {'title': 'B', 'type': 'string'},
                },
                'required': ['b'],
            }
        },
    }


def test_typeddict_not_required():
    class DataTD(TypedDict, total=True):
        a: NotRequired[int]
        b: str

    class Model(BaseModel):
        t: DataTD

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'t': {'$ref': '#/definitions/DataTD'}},
        'required': ['t'],
        'definitions': {
            'DataTD': {
                'title': 'DataTD',
                'type': 'object',
                'properties': {
                    'a': {'title': 'A', 'type': 'integer'},
                    'b': {'title': 'B', 'type': 'string'},
                },
                'required': ['b'],
            }
        },
    }


def test_typed_dict_inheritance():
    class DataTDBase(TypedDict, total=True):
        a: NotRequired[int]
        b: str

    class DataTD(DataTDBase, total=False):
        c: Required[int]
        d: str

    class Model(BaseModel):
        t: DataTD

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'t': {'$ref': '#/definitions/DataTD'}},
        'required': ['t'],
        'definitions': {
            'DataTD': {
                'title': 'DataTD',
                'type': 'object',
                'properties': {
                    'a': {'title': 'A', 'type': 'integer'},
                    'b': {'title': 'B', 'type': 'string'},
                    'c': {'title': 'C', 'type': 'integer'},
                    'd': {'title': 'D', 'type': 'string'},
                },
                'required': ['b', 'c'],
            }
        },
    }


def test_typeddict_annotated_nonoptional():
    class DataTD(TypedDict):
        a: Optional[int]
        b: Annotated[Optional[int], Field(...)]
        c: Annotated[Optional[int], Field(..., description='Test')]
        d: Annotated[Optional[int], Field()]

    class Model(BaseModel):
        data_td: DataTD

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'data_td': {'$ref': '#/definitions/DataTD'}},
        'required': ['data_td'],
        'definitions': {
            'DataTD': {
                'type': 'object',
                'title': 'DataTD',
                'properties': {
                    'a': {'title': 'A', 'type': 'integer'},
                    'b': {'title': 'B', 'type': 'integer'},
                    'c': {'title': 'C', 'type': 'integer', 'description': 'Test'},
                    'd': {'title': 'D', 'type': 'integer'},
                },
                'required': ['a', 'b', 'c'],
            },
        },
    }

    for bad_obj in ({}, {'data_td': []}, {'data_td': {'a': 1, 'b': 2, 'd': 4}}):
        with pytest.raises(ValidationError):
            Model.parse_obj(bad_obj)

    valid_data = {'a': 1, 'b': 2, 'c': 3}
    parsed_model = Model.parse_obj({'data_td': valid_data})
    assert parsed_model and parsed_model == Model(data_td=valid_data)


@pytest.mark.skipif(not LegacyRequiredTypedDict, reason='python 3.11+ used')
def test_legacy_typeddict_required_not_required():
    class TDRequired(LegacyRequiredTypedDict):
        a: Required[int]

    class TDNotRequired(LegacyRequiredTypedDict):
        a: Required[int]

    for cls in (TDRequired, TDNotRequired):
        with pytest.raises(
            TypeError,
            match='^You should use `typing_extensions.TypedDict` instead of `typing.TypedDict` with Python < 3.11.',
        ):

            class Model(BaseModel):
                t: cls


@pytest.mark.skipif(not LegacyRequiredTypedDict, reason='python 3.11+ used')
def test_legacy_typeddict_no_required_not_required():
    class TD(LegacyRequiredTypedDict):
        a: int

    class Model(BaseModel):
        t: TD
