"""
Tests for TypedDict
"""
import re
import sys
import typing
from typing import Generic, List, Optional, TypeVar

import pytest
import typing_extensions
from annotated_types import Lt
from typing_extensions import Annotated, TypedDict

from pydantic import BaseModel, Field, PositiveInt, PydanticUserError, ValidationError
from pydantic.type_adapter import TypeAdapter

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

    except PydanticUserError as e:
        assert e.message == 'Please use `typing_extensions.TypedDict` instead of `typing.TypedDict` on Python < 3.11.'
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
    with pytest.raises(ValidationError, match=r'd\.bar\s+Field required \[type=missing,'):
        M(d=dict(foo='baz'))

    with pytest.raises(ValidationError, match=r'd\.bar\s+Input should be less than 10 \[type=less_than,'):
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
    with pytest.raises(ValidationError, match=r'd\.foo\s+Field required \[type=missing,'):
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
    assert exc_info.value.errors(include_url=False) == [
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
    assert exc_info.value.errors(include_url=False) == [
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


def test_typeddict_extra_default(TypedDict):
    class User(TypedDict):
        name: str
        age: int

    val = TypeAdapter(User)

    with pytest.raises(ValidationError) as exc_info:
        val.validate_python({'name': 'pika', 'age': 7, 'rank': 1})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('rank',), 'msg': 'Extra inputs are not permitted', 'input': 1}
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


def test_typeddict_from_attributes():
    class UserCls:
        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

    class User(TypedDict):
        name: str
        age: int

    class FromAttributesCls:
        def __init__(self, u: User):
            self.u = u

    class Model(BaseModel):
        u: Annotated[User, Field(strict=False)]

    class FromAttributesModel(BaseModel, from_attributes=True):
        u: Annotated[User, Field(strict=False)]

    # You can validate the TypedDict from attributes from a type that has a field with an appropriate attribute
    assert FromAttributesModel.model_validate(FromAttributesCls(u={'name': 'foo', 'age': 15}))

    # The normal case: you can't populate a TypedDict from attributes with the relevant config setting disabled
    with pytest.raises(ValidationError, match='Input should be a valid dictionary'):
        Model(u=UserCls('foo', 15))

    # Going further: even with from_attributes allowed, it won't attempt to populate a TypedDict from attributes
    with pytest.raises(ValidationError, match='Input should be a valid dictionary'):
        FromAttributesModel(u=UserCls('foo', 15))


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


def test_recursive_typeddict(create_module):
    @create_module
    def module():
        from typing import Optional

        from typing_extensions import TypedDict

        from pydantic import BaseModel

        class RecursiveTypedDict(TypedDict):
            # TODO: See if we can get this working if defined in a function (right now, needs to be module-level)
            foo: Optional['RecursiveTypedDict']

        class RecursiveTypedDictModel(BaseModel):
            rec: RecursiveTypedDict

    assert module.RecursiveTypedDictModel(rec={'foo': {'foo': None}}).rec == {'foo': {'foo': None}}
    with pytest.raises(ValidationError) as exc_info:
        module.RecursiveTypedDictModel(rec={'foo': {'foo': {'foo': 1}}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 1,
            'loc': ('rec', 'foo', 'foo', 'foo'),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
        }
    ]


T = TypeVar('T')


def test_generic_typeddict_in_concrete_model():
    T = TypeVar('T')

    class GenericTypedDict(typing_extensions.TypedDict, Generic[T]):
        x: T

    class Model(BaseModel):
        y: GenericTypedDict[int]

    Model(y={'x': 1})
    with pytest.raises(ValidationError) as exc_info:
        Model(y={'x': 'a'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('y', 'x'),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]


def test_generic_typeddict_in_generic_model():
    T = TypeVar('T')

    class GenericTypedDict(typing_extensions.TypedDict, Generic[T]):
        x: T

    class Model(BaseModel, Generic[T]):
        y: GenericTypedDict[T]

    Model[int](y={'x': 1})
    with pytest.raises(ValidationError) as exc_info:
        Model[int](y={'x': 'a'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('y', 'x'),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]


def test_recursive_generic_typeddict_in_module(create_module):
    @create_module
    def module():
        from typing import Generic, List, Optional, TypeVar

        from typing_extensions import TypedDict

        from pydantic import BaseModel

        T = TypeVar('T')

        class RecursiveGenTypedDictModel(BaseModel, Generic[T]):
            rec: 'RecursiveGenTypedDict[T]'
            model_config = dict(undefined_types_warning=False)

        class RecursiveGenTypedDict(TypedDict, Generic[T]):
            foo: Optional['RecursiveGenTypedDict[T]']
            ls: List[T]

    int_data: module.RecursiveGenTypedDict[int] = {'foo': {'foo': None, 'ls': [1]}, 'ls': [1]}
    assert module.RecursiveGenTypedDictModel[int](rec=int_data).rec == int_data

    str_data: module.RecursiveGenTypedDict[str] = {'foo': {'foo': None, 'ls': ['a']}, 'ls': ['a']}
    with pytest.raises(ValidationError) as exc_info:
        module.RecursiveGenTypedDictModel[int](rec=str_data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('rec', 'foo', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': 'a',
            'loc': ('rec', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]


def test_recursive_generic_typeddict_in_function_1():
    T = TypeVar('T')

    # First ordering: typed dict first
    class RecursiveGenTypedDict(TypedDict, Generic[T]):
        foo: Optional['RecursiveGenTypedDict[T]']
        ls: List[T]

    class RecursiveGenTypedDictModel(BaseModel, Generic[T]):
        rec: 'RecursiveGenTypedDict[T]'
        model_config = dict(undefined_types_warning=False)

    # Note: no model_rebuild() necessary here
    # RecursiveGenTypedDictModel.model_rebuild()

    int_data: RecursiveGenTypedDict[int] = {'foo': {'foo': None, 'ls': [1]}, 'ls': [1]}
    assert RecursiveGenTypedDictModel[int](rec=int_data).rec == int_data

    str_data: RecursiveGenTypedDict[str] = {'foo': {'foo': None, 'ls': ['a']}, 'ls': ['a']}
    with pytest.raises(ValidationError) as exc_info:
        RecursiveGenTypedDictModel[int](rec=str_data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('rec', 'foo', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': 'a',
            'loc': ('rec', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]


def test_recursive_generic_typeddict_in_function_2():
    T = TypeVar('T')

    # Second ordering: model first
    class RecursiveGenTypedDictModel(BaseModel, Generic[T]):
        rec: 'RecursiveGenTypedDict[T]'
        model_config = dict(undefined_types_warning=False)

    class RecursiveGenTypedDict(TypedDict, Generic[T]):
        foo: Optional['RecursiveGenTypedDict[T]']
        ls: List[T]

    int_data: RecursiveGenTypedDict[int] = {'foo': {'foo': None, 'ls': [1]}, 'ls': [1]}
    assert RecursiveGenTypedDictModel[int](rec=int_data).rec == int_data

    str_data: RecursiveGenTypedDict[str] = {'foo': {'foo': None, 'ls': ['a']}, 'ls': ['a']}
    with pytest.raises(ValidationError) as exc_info:
        RecursiveGenTypedDictModel[int](rec=str_data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('rec', 'foo', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': 'a',
            'loc': ('rec', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]


def test_recursive_generic_typeddict_in_function_rebuild_error():
    T = TypeVar('T')

    class RecursiveGenTypedDictModel(BaseModel, Generic[T]):
        rec: 'RecursiveGenTypedDict[T]'
        model_config = dict(undefined_types_warning=False)

    IntModel = RecursiveGenTypedDictModel[int]

    class RecursiveGenTypedDict(TypedDict, Generic[T]):
        foo: Optional['RecursiveGenTypedDict[T]']
        ls: List[T]

    int_data: RecursiveGenTypedDict[int] = {'foo': {'foo': None, 'ls': [1]}, 'ls': [1]}
    with pytest.raises(
        PydanticUserError,
        match=re.escape(
            '`RecursiveGenTypedDictModel[int]` is not fully defined; you should define `RecursiveGenTypedDict`,'
            ' then call `RecursiveGenTypedDictModel[int].model_rebuild()` before the first'
            ' `RecursiveGenTypedDictModel[int]` instance is created.'
        ),
    ):
        IntModel(rec=int_data).rec


def test_recursive_generic_typeddict_in_function_rebuild_pass():
    T = TypeVar('T')

    class RecursiveGenTypedDictModel(BaseModel, Generic[T]):
        rec: 'RecursiveGenTypedDict[T]'
        model_config = dict(undefined_types_warning=False)

    IntModel = RecursiveGenTypedDictModel[int]

    class RecursiveGenTypedDict(TypedDict, Generic[T]):
        foo: Optional['RecursiveGenTypedDict[T]']
        ls: List[T]

    int_data: RecursiveGenTypedDict[int] = {'foo': {'foo': None, 'ls': [1]}, 'ls': [1]}
    IntModel.model_rebuild()
    assert IntModel(rec=int_data).rec == int_data

    str_data: RecursiveGenTypedDict[str] = {'foo': {'foo': None, 'ls': ['a']}, 'ls': ['a']}
    with pytest.raises(ValidationError) as exc_info:
        IntModel(rec=str_data)
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('rec', 'foo', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {
            'input': 'a',
            'loc': ('rec', 'ls', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]
