"""
Tests for TypedDict
"""
import sys
import typing
from typing import Optional

import pytest
import typing_extensions
from annotated_types import Lt
from typing_extensions import Annotated

from pydantic import BaseModel, Field, PositiveInt, ValidationError

from .conftest import Err


@pytest.fixture(
    name='TypedDictAll',
    params=[
        pytest.param(typing, id='typing.TypedDict'),
        pytest.param(typing_extensions, id='t_e.TypedDict'),
    ],
)
def fixture_typed_dict_all(request):
    try:
        return request.param.TypedDict
    except AttributeError:
        pytest.skip(f'TypedDict is not available from {request.param}')


@pytest.fixture(name='TypedDict')
def fixture_typed_dict(TypedDictAll):
    class TestTypedDict(TypedDictAll):
        foo: str

    if sys.version_info < (3, 11) and TypedDictAll.__module__ == 'typing':
        pytest.skip('typing.TypedDict does not track required keys correctly on Python < 3.11')

    if hasattr(TestTypedDict, '__required_keys__'):
        return TypedDictAll
    else:
        pytest.skip('TypedDict does not include __required_keys__')


@pytest.fixture(
    name='req_no_req',
    params=[
        pytest.param(typing, id='typing.Required'),
        pytest.param(typing_extensions, id='t_e.Required'),
    ],
)
def fixture_req_no_req(request):
    try:
        return request.param.Required, request.param.NotRequired
    except AttributeError:
        pytest.skip(f'Required and NotRequired are not available from {request.param}')


def test_typeddict_all(TypedDictAll):
    class MyDict(TypedDictAll):
        foo: str

    try:

        class M(BaseModel):
            d: MyDict

    except TypeError as e:
        assert str(e) == 'Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.11.'
    else:
        assert M(d=dict(foo='baz')).d == {'foo': 'baz'}


def test_typeddict_annotated_simple(TypedDict, req_no_req):
    Required, NotRequired = req_no_req

    class MyDict(TypedDict):
        foo: str
        bar: Annotated[int, Lt(10)]
        spam: NotRequired[float]

    class M(BaseModel):
        d: MyDict

    assert M(d=dict(foo='baz', bar='8')).d == {'foo': 'baz', 'bar': 8}
    assert M(d=dict(foo='baz', bar='8', spam='44.4')).d == {'foo': 'baz', 'bar': 8, 'spam': 44.4}
    with pytest.raises(ValidationError, match=r'd -> bar\s+Field required \[type=missing,'):
        M(d=dict(foo='baz'))

    with pytest.raises(ValidationError, match=r'd -> bar\s+Input should be less than 10 \[type=less_than,'):
        M(d=dict(foo='baz', bar='11'))


def test_typeddict_total_false(TypedDict, req_no_req):
    Required, NotRequired = req_no_req

    class MyDict(TypedDict, total=False):
        foo: Required[str]
        bar: int

    class M(BaseModel):
        d: MyDict

    assert M(d=dict(foo='baz', bar='8')).d == {'foo': 'baz', 'bar': 8}
    assert M(d=dict(foo='baz')).d == {'foo': 'baz'}
    with pytest.raises(ValidationError, match=r'd -> foo\s+Field required \[type=missing,'):
        M(d={})


def test_typeddict(TypedDict):
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
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'int_type', 'loc': ('td', 'a'), 'msg': 'Input should be a valid integer', 'input': [1]}
    ]


def test_typeddict_non_total(TypedDict):
    class FullMovie(TypedDict, total=True):
        name: str
        year: int

    class Model(BaseModel):
        movie: FullMovie

    with pytest.raises(ValidationError) as exc_info:
        Model(movie={'year': '2002'})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'missing', 'loc': ('movie', 'name'), 'msg': 'Field required', 'input': {'year': '2002'}}
    ]

    class PartialMovie(TypedDict, total=False):
        name: str
        year: int

    class Model(BaseModel):
        movie: PartialMovie

    m = Model(movie={'year': '2002'})
    assert m.movie == {'year': 2002}


def test_partial_new_typeddict(TypedDict):
    class OptionalUser(TypedDict, total=False):
        name: str

    class User(OptionalUser):
        id: int

    class Model(BaseModel):
        user: User

    assert Model(user={'id': 1, 'name': 'foobar'}).user == {'id': 1, 'name': 'foobar'}
    assert Model(user={'id': 1}).user == {'id': 1}


def test_typeddict_extra(TypedDict):
    class User(TypedDict):
        name: str
        age: int

    class Model(BaseModel, extra='forbid'):
        u: User

    with pytest.raises(ValidationError) as exc_info:
        Model(u={'name': 'pika', 'age': 7, 'rank': 1})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'extra_forbidden', 'loc': ('u', 'rank'), 'msg': 'Extra inputs are not permitted', 'input': 1}
    ]


def test_typeddict_schema(TypedDict):
    class Data(BaseModel):
        a: int

    # TODO: Need to make sure TypedDict's get their own schema
    class DataTD(TypedDict):
        a: int

    class Model(BaseModel):
        data: Data
        data_td: DataTD

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'data': {'$ref': '#/$defs/Data'}, 'data_td': {'$ref': '#/$defs/DataTD'}},
        'required': ['data', 'data_td'],
        '$defs': {
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


def test_typeddict_postponed_annotation(TypedDict):
    class DataTD(TypedDict):
        v: 'PositiveInt'

    class Model(BaseModel):
        t: DataTD

    with pytest.raises(ValidationError):
        Model.model_validate({'t': {'v': -1}})


def test_typeddict_required(TypedDict, req_no_req):
    Required, _ = req_no_req

    class DataTD(TypedDict, total=False):
        a: int
        b: Required[str]

    class Model(BaseModel):
        t: DataTD

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'t': {'$ref': '#/$defs/DataTD'}},
        'required': ['t'],
        '$defs': {
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


def test_typeddict_not_required_schema(TypedDict, req_no_req):
    Required, NotRequired = req_no_req

    class DataTD(TypedDict, total=True):
        a: NotRequired[int]
        b: str

    class Model(BaseModel):
        t: DataTD

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'t': {'$ref': '#/$defs/DataTD'}},
        'required': ['t'],
        '$defs': {
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


def test_typed_dict_inheritance_schema(TypedDict, req_no_req):
    Required, NotRequired = req_no_req

    class DataTDBase(TypedDict, total=True):
        a: NotRequired[int]
        b: str

    class DataTD(DataTDBase, total=False):
        c: Required[int]
        d: str

    class Model(BaseModel):
        t: DataTD

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'t': {'$ref': '#/$defs/DataTD'}},
        'required': ['t'],
        '$defs': {
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


def test_typeddict_annotated_nonoptional_schema(TypedDict):
    class DataTD(TypedDict):
        a: Optional[int]
        b: Annotated[Optional[int], Field(42)]
        c: Annotated[Optional[int], Field(description='Test')]

    class Model(BaseModel):
        data_td: DataTD

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'data_td': {'$ref': '#/$defs/DataTD'}},
        'required': ['data_td'],
        '$defs': {
            'DataTD': {
                'type': 'object',
                'title': 'DataTD',
                'properties': {
                    'a': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'title': 'A'},
                    'b': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': 42, 'title': 'B'},
                    'c': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'description': 'Test', 'title': 'C'},
                },
                'required': ['a', 'c'],
            },
        },
    }


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'a': '1', 'b': 2, 'c': 3}, {'a': 1, 'b': 2, 'c': 3}),
        ({'a': None, 'b': 2, 'c': 3}, {'a': None, 'b': 2, 'c': 3}),
        ({'a': None, 'c': 3}, {'a': None, 'b': 42, 'c': 3}),
        # ({}, None),
        # ({'data_td': []}, None),
        # ({'data_td': {'a': 1, 'b': 2, 'd': 4}}, None),
    ],
    ids=repr,
)
def test_typeddict_annotated(TypedDict, input_value, expected):
    class DataTD(TypedDict):
        a: Optional[int]
        b: Annotated[Optional[int], Field(42)]
        c: Annotated[Optional[int], Field(description='Test', lt=4)]

    class Model(BaseModel):
        d: DataTD

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message_escaped()):
            Model(d=input_value)
    else:
        assert Model(d=input_value).d == expected
