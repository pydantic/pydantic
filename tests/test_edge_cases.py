import importlib.util
import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Hashable
from decimal import Decimal
from enum import Enum, auto
from typing import (
    Any,
    Dict,
    ForwardRef,
    FrozenSet,
    Generic,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pytest
from dirty_equals import HasRepr, IsStr
from pydantic_core import ErrorDetails, InitErrorDetails, PydanticSerializationError, core_schema
from typing_extensions import Annotated, TypedDict, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    PydanticDeprecatedSince20,
    PydanticInvalidForJsonSchema,
    PydanticSchemaGenerationError,
    TypeAdapter,
    ValidationError,
    constr,
    errors,
    field_validator,
    model_validator,
    root_validator,
    validator,
)
from pydantic.fields import Field, computed_field
from pydantic.functional_serializers import (
    field_serializer,
    model_serializer,
)


def test_str_bytes():
    class Model(BaseModel):
        v: Union[str, bytes]

    m = Model(v='s')
    assert m.v == 's'
    assert repr(m.model_fields['v']) == 'FieldInfo(annotation=Union[str, bytes], required=True)'

    m = Model(v=b'b')
    assert m.v == b'b'

    with pytest.raises(ValidationError) as exc_info:
        Model(v=None)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': ('v', 'str'), 'msg': 'Input should be a valid string', 'input': None},
        {'type': 'bytes_type', 'loc': ('v', 'bytes'), 'msg': 'Input should be a valid bytes', 'input': None},
    ]


def test_str_bytes_none():
    class Model(BaseModel):
        v: Union[None, str, bytes] = ...

    m = Model(v='s')
    assert m.v == 's'

    m = Model(v=b'b')
    assert m.v == b'b'

    m = Model(v=None)
    assert m.v is None


def test_union_int_str():
    class Model(BaseModel):
        v: Union[int, str] = ...

    m = Model(v=123)
    assert m.v == 123

    m = Model(v='123')
    assert m.v == '123'

    m = Model(v=b'foobar')
    assert m.v == 'foobar'

    m = Model(v=12.0)
    assert m.v == 12

    with pytest.raises(ValidationError) as exc_info:
        Model(v=None)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('v', 'int'), 'msg': 'Input should be a valid integer', 'input': None},
        {
            'type': 'string_type',
            'loc': ('v', 'str'),
            'msg': 'Input should be a valid string',
            'input': None,
        },
    ]


def test_union_int_any():
    class Model(BaseModel):
        v: Union[int, Any]

    m = Model(v=123)
    assert m.v == 123

    m = Model(v='123')
    assert m.v == '123'

    m = Model(v='foobar')
    assert m.v == 'foobar'

    m = Model(v=None)
    assert m.v is None


def test_typed_list():
    class Model(BaseModel):
        v: List[int] = ...

    m = Model(v=[1, 2, '3'])
    assert m.v == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 'x', 'y'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('v', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': ('v', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': ('v',), 'msg': 'Input should be a valid list', 'input': 1}
    ]


def test_typed_set():
    class Model(BaseModel):
        v: Set[int] = ...

    assert Model(v={1, 2, '3'}).v == {1, 2, 3}
    assert Model(v=[1, 2, '3']).v == {1, 2, 3}

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 'x'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('v', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        }
    ]


def test_dict_dict():
    class Model(BaseModel):
        v: Dict[str, int] = ...

    assert Model(v={'foo': 1}).model_dump() == {'v': {'foo': 1}}


def test_none_list():
    class Model(BaseModel):
        v: List[None] = [None]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'default': [None], 'type': 'array', 'items': {'type': 'null'}}},
    }


@pytest.mark.parametrize(
    'value,result',
    [
        ({'a': 2, 'b': 4}, {'a': 2, 'b': 4}),
        ({b'a': '2', 'b': 4}, {'a': 2, 'b': 4}),
        # ([('a', 2), ('b', 4)], {'a': 2, 'b': 4}),
    ],
)
def test_typed_dict(value, result):
    class Model(BaseModel):
        v: Dict[str, int] = ...

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'value,errors',
    [
        (1, [{'type': 'dict_type', 'loc': ('v',), 'msg': 'Input should be a valid dictionary', 'input': 1}]),
        (
            {'a': 'b'},
            [
                {
                    'type': 'int_parsing',
                    'loc': ('v', 'a'),
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'b',
                }
            ],
        ),
        (
            [1, 2, 3],
            [{'type': 'dict_type', 'loc': ('v',), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}],
        ),
    ],
)
def test_typed_dict_error(value, errors):
    class Model(BaseModel):
        v: Dict[str, int] = ...

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors(include_url=False) == errors


def test_dict_key_error():
    class Model(BaseModel):
        v: Dict[int, int] = ...

    assert Model(v={1: 2, '3': '4'}).v == {1: 2, 3: 4}

    with pytest.raises(ValidationError) as exc_info:
        Model(v={'foo': 2, '3': '4'})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('v', 'foo', '[key]'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'foo',
        }
    ]


def test_tuple():
    class Model(BaseModel):
        v: Tuple[int, float, bool]

    m = Model(v=['1.0', '2.2', 'true'])
    assert m.v == (1, 2.2, True)


def test_tuple_more():
    class Model(BaseModel):
        empty_tuple: Tuple[()]
        simple_tuple: tuple = None
        tuple_of_different_types: Tuple[int, float, str, bool] = None
        tuple_of_single_tuples: Tuple[Tuple[int], ...] = ()

    m = Model(
        empty_tuple=[],
        simple_tuple=[1, 2, 3, 4],
        tuple_of_different_types=[4, 3.1, 'str', 1],
        tuple_of_single_tuples=(('1',), (2,)),
    )
    assert m.model_dump() == {
        'empty_tuple': (),
        'simple_tuple': (1, 2, 3, 4),
        'tuple_of_different_types': (4, 3.1, 'str', True),
        'tuple_of_single_tuples': ((1,), (2,)),
    }


@pytest.mark.parametrize(
    'dict_cls,frozenset_cls,list_cls,set_cls,tuple_cls,type_cls',
    [
        (Dict, FrozenSet, List, Set, Tuple, Type),
        (dict, frozenset, list, set, tuple, type),
    ],
)
@pytest.mark.skipif(sys.version_info < (3, 9), reason='PEP585 generics only supported for python 3.9 and above')
def test_pep585_generic_types(dict_cls, frozenset_cls, list_cls, set_cls, tuple_cls, type_cls):
    class Type1:
        pass

    class Type2:
        pass

    class Model(BaseModel, arbitrary_types_allowed=True):
        a: dict_cls
        a1: dict_cls[str, int]
        b: frozenset_cls
        b1: frozenset_cls[int]
        c: list_cls
        c1: list_cls[int]
        d: set_cls
        d1: set_cls[int]
        e: tuple_cls
        e1: tuple_cls[int]
        e2: tuple_cls[int, ...]
        e3: tuple_cls[()]
        f: type_cls
        f1: type_cls[Type1]

    default_model_kwargs = dict(
        a={},
        a1={'a': '1'},
        b=[],
        b1=('1',),
        c=[],
        c1=('1',),
        d=[],
        d1=['1'],
        e=[],
        e1=['1'],
        e2=['1', '2'],
        e3=[],
        f=Type1,
        f1=Type1,
    )

    m = Model(**default_model_kwargs)
    assert m.a == {}
    assert m.a1 == {'a': 1}
    assert m.b == frozenset()
    assert m.b1 == frozenset({1})
    assert m.c == []
    assert m.c1 == [1]
    assert m.d == set()
    assert m.d1 == {1}
    assert m.e == ()
    assert m.e1 == (1,)
    assert m.e2 == (1, 2)
    assert m.e3 == ()
    assert m.f == Type1
    assert m.f1 == Type1

    with pytest.raises(ValidationError) as exc_info:
        Model(**(default_model_kwargs | {'e3': (1,)}))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('e3',),
            'msg': 'Tuple should have at most 0 items after validation, not 1',
            'input': (1,),
            'ctx': {'field_type': 'Tuple', 'max_length': 0, 'actual_length': 1},
        }
    ]

    Model(**(default_model_kwargs | {'f': Type2}))

    with pytest.raises(ValidationError) as exc_info:
        Model(**(default_model_kwargs | {'f1': Type2}))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_subclass_of',
            'loc': ('f1',),
            'msg': 'Input should be a subclass of test_pep585_generic_types.<locals>.Type1',
            'input': HasRepr(IsStr(regex=r".+\.Type2'>")),
            'ctx': {'class': 'test_pep585_generic_types.<locals>.Type1'},
        }
    ]


def test_tuple_length_error():
    class Model(BaseModel):
        v: Tuple[int, float, bool]
        w: Tuple[()]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2], w=[1])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('v', 2), 'msg': 'Field required', 'input': [1, 2]},
        {
            'type': 'too_long',
            'loc': ('w',),
            'msg': 'Tuple should have at most 0 items after validation, not 1',
            'input': [1],
            'ctx': {'field_type': 'Tuple', 'max_length': 0, 'actual_length': 1},
        },
    ]


def test_tuple_invalid():
    class Model(BaseModel):
        v: Tuple[int, float, bool]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='xxx')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': ('v',), 'msg': 'Input should be a valid tuple', 'input': 'xxx'}
    ]


def test_tuple_value_error():
    class Model(BaseModel):
        v: Tuple[int, float, Decimal]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=['x', 'y', 'x'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('v', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {
            'type': 'float_parsing',
            'loc': ('v', 1),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'y',
        },
        {
            'type': 'is_instance_of',
            'loc': ('v', 2, 'is-instance[Decimal]'),
            'msg': 'Input should be an instance of Decimal',
            'input': 'x',
            'ctx': {'class': 'Decimal'},
        },
        {
            'type': 'decimal_parsing',
            'loc': (
                'v',
                2,
                'function-after[to_decimal(), union[float,int,constrained-str,function-plain[<lambda>()]]]',
            ),
            'msg': 'Input should be a valid decimal',
            'input': 'x',
        },
    ]


def test_recursive_list():
    class SubModel(BaseModel):
        name: str = ...
        count: int = None

    class Model(BaseModel):
        v: List[SubModel] = []

    m = Model(v=[])
    assert m.v == []

    m = Model(v=[{'name': 'testing', 'count': 4}])
    assert repr(m) == "Model(v=[SubModel(name='testing', count=4)])"
    assert m.v[0].name == 'testing'
    assert m.v[0].count == 4
    assert m.model_dump() == {'v': [{'count': 4, 'name': 'testing'}]}

    with pytest.raises(ValidationError) as exc_info:
        Model(v=['x'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('v', 0),
            'msg': 'Input should be a valid dictionary or instance of SubModel',
            'input': 'x',
            'ctx': {'class_name': 'SubModel'},
        }
    ]


def test_recursive_list_error():
    class SubModel(BaseModel):
        name: str = ...
        count: int = None

    class Model(BaseModel):
        v: List[SubModel] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[{}])
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('v', 0, 'name'), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_list_unions():
    class Model(BaseModel):
        v: List[Union[int, str]] = ...

    assert Model(v=[123, '456', 'foobar']).v == [123, '456', 'foobar']

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, None])

    assert exc_info.value.errors(include_url=False) == [
        {'input': None, 'loc': ('v', 2, 'int'), 'msg': 'Input should be a valid integer', 'type': 'int_type'},
        {'input': None, 'loc': ('v', 2, 'str'), 'msg': 'Input should be a valid string', 'type': 'string_type'},
    ]


def test_recursive_lists():
    class Model(BaseModel):
        v: List[List[Union[int, float]]] = ...

    assert Model(v=[[1, 2], [3, '4', '4.1']]).v == [[1, 2], [3, 4, 4.1]]
    assert Model.model_fields['v'].annotation == List[List[Union[int, float]]]
    assert Model.model_fields['v'].is_required()


class StrEnum(str, Enum):
    a = 'a10'
    b = 'b10'


def test_str_enum():
    class Model(BaseModel):
        v: StrEnum = ...

    assert Model(v='a10').v is StrEnum.a

    with pytest.raises(ValidationError):
        Model(v='different')


def test_any_dict():
    class Model(BaseModel):
        v: Dict[int, Any] = ...

    assert Model(v={1: 'foobar'}).model_dump() == {'v': {1: 'foobar'}}
    assert Model(v={123: 456}).model_dump() == {'v': {123: 456}}
    assert Model(v={2: [1, 2, 3]}).model_dump() == {'v': {2: [1, 2, 3]}}


def test_success_values_include():
    class Model(BaseModel):
        a: int = 1
        b: int = 2
        c: int = 3

    m = Model()
    assert m.model_dump() == {'a': 1, 'b': 2, 'c': 3}
    assert m.model_dump(include={'a'}) == {'a': 1}
    assert m.model_dump(exclude={'a'}) == {'b': 2, 'c': 3}
    assert m.model_dump(include={'a', 'b'}, exclude={'a'}) == {'b': 2}


def test_include_exclude_unset():
    class Model(BaseModel):
        a: int
        b: int
        c: int = 3
        d: int = 4
        e: int = 5
        f: int = 6

    m = Model(a=1, b=2, e=5, f=7)
    assert m.model_dump() == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 7}
    assert m.model_fields_set == {'a', 'b', 'e', 'f'}
    assert m.model_dump(exclude_unset=True) == {'a': 1, 'b': 2, 'e': 5, 'f': 7}

    assert m.model_dump(include={'a'}, exclude_unset=True) == {'a': 1}
    assert m.model_dump(include={'c'}, exclude_unset=True) == {}

    assert m.model_dump(exclude={'a'}, exclude_unset=True) == {'b': 2, 'e': 5, 'f': 7}
    assert m.model_dump(exclude={'c'}, exclude_unset=True) == {'a': 1, 'b': 2, 'e': 5, 'f': 7}

    assert m.model_dump(include={'a', 'b', 'c'}, exclude={'b'}, exclude_unset=True) == {'a': 1}
    assert m.model_dump(include={'a', 'b', 'c'}, exclude={'a', 'c'}, exclude_unset=True) == {'b': 2}


def test_include_exclude_defaults():
    class Model(BaseModel):
        a: int
        b: int
        c: int = 3
        d: int = 4
        e: int = 5
        f: int = 6

    m = Model(a=1, b=2, e=5, f=7)
    assert m.model_dump() == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 7}
    assert m.model_fields_set == {'a', 'b', 'e', 'f'}
    assert m.model_dump(exclude_defaults=True) == {'a': 1, 'b': 2, 'f': 7}

    assert m.model_dump(include={'a'}, exclude_defaults=True) == {'a': 1}
    assert m.model_dump(include={'c'}, exclude_defaults=True) == {}

    assert m.model_dump(exclude={'a'}, exclude_defaults=True) == {'b': 2, 'f': 7}
    assert m.model_dump(exclude={'c'}, exclude_defaults=True) == {'a': 1, 'b': 2, 'f': 7}

    assert m.model_dump(include={'a', 'b', 'c'}, exclude={'b'}, exclude_defaults=True) == {'a': 1}
    assert m.model_dump(include={'a', 'b', 'c'}, exclude={'a', 'c'}, exclude_defaults=True) == {'b': 2}

    assert m.model_dump(include={'a': 1}.keys()) == {'a': 1}
    assert m.model_dump(exclude={'a': 1}.keys()) == {'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 7}

    assert m.model_dump(include={'a': 1}.keys(), exclude_unset=True) == {'a': 1}
    assert m.model_dump(exclude={'a': 1}.keys(), exclude_unset=True) == {'b': 2, 'e': 5, 'f': 7}

    assert m.model_dump(include=['a']) == {'a': 1}
    assert m.model_dump(exclude=['a']) == {'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 7}

    assert m.model_dump(include=['a'], exclude_unset=True) == {'a': 1}
    assert m.model_dump(exclude=['a'], exclude_unset=True) == {'b': 2, 'e': 5, 'f': 7}


def test_advanced_exclude():
    class SubSubModel(BaseModel):
        a: str
        b: str

    class SubModel(BaseModel):
        c: str
        d: List[SubSubModel]

    class Model(BaseModel):
        e: str
        f: SubModel

    m = Model(e='e', f=SubModel(c='foo', d=[SubSubModel(a='a', b='b'), SubSubModel(a='c', b='e')]))

    assert m.model_dump(exclude={'f': {'c': ..., 'd': {-1: {'a'}}}}) == {
        'e': 'e',
        'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]},
    }
    assert m.model_dump(exclude={'e': ..., 'f': {'d'}}) == {'f': {'c': 'foo'}}


def test_advanced_exclude_by_alias():
    class SubSubModel(BaseModel):
        a: str
        aliased_b: str = Field(..., alias='b_alias')

    class SubModel(BaseModel):
        aliased_c: str = Field(..., alias='c_alias')
        aliased_d: List[SubSubModel] = Field(..., alias='d_alias')

    class Model(BaseModel):
        aliased_e: str = Field(..., alias='e_alias')
        aliased_f: SubModel = Field(..., alias='f_alias')

    m = Model(
        e_alias='e',
        f_alias=SubModel(c_alias='foo', d_alias=[SubSubModel(a='a', b_alias='b'), SubSubModel(a='c', b_alias='e')]),
    )

    excludes = {'aliased_f': {'aliased_c': ..., 'aliased_d': {-1: {'a'}}}}
    assert m.model_dump(exclude=excludes, by_alias=True) == {
        'e_alias': 'e',
        'f_alias': {'d_alias': [{'a': 'a', 'b_alias': 'b'}, {'b_alias': 'e'}]},
    }

    excludes = {'aliased_e': ..., 'aliased_f': {'aliased_d'}}
    assert m.model_dump(exclude=excludes, by_alias=True) == {'f_alias': {'c_alias': 'foo'}}


def test_advanced_value_include():
    class SubSubModel(BaseModel):
        a: str
        b: str

    class SubModel(BaseModel):
        c: str
        d: List[SubSubModel]

    class Model(BaseModel):
        e: str
        f: SubModel

    m = Model(e='e', f=SubModel(c='foo', d=[SubSubModel(a='a', b='b'), SubSubModel(a='c', b='e')]))

    assert m.model_dump(include={'f'}) == {'f': {'c': 'foo', 'd': [{'a': 'a', 'b': 'b'}, {'a': 'c', 'b': 'e'}]}}
    assert m.model_dump(include={'e'}) == {'e': 'e'}
    assert m.model_dump(include={'f': {'d': {0: ..., -1: {'b'}}}}) == {'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}}


def test_advanced_value_exclude_include():
    class SubSubModel(BaseModel):
        a: str
        b: str

    class SubModel(BaseModel):
        c: str
        d: List[SubSubModel]

    class Model(BaseModel):
        e: str
        f: SubModel

    m = Model(e='e', f=SubModel(c='foo', d=[SubSubModel(a='a', b='b'), SubSubModel(a='c', b='e')]))

    assert m.model_dump(exclude={'f': {'c': ..., 'd': {-1: {'a'}}}}, include={'f'}) == {
        'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}
    }
    assert m.model_dump(exclude={'e': ..., 'f': {'d'}}, include={'e', 'f'}) == {'f': {'c': 'foo'}}

    assert m.model_dump(exclude={'f': {'d': {-1: {'a'}}}}, include={'f': {'d'}}) == {
        'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}
    }


@pytest.mark.parametrize(
    'exclude,expected',
    [
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'j': 1}, {'j': 2}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
            id='Normal nested __all__',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
            id='Merge sub dicts 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': ...}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1}, {'i': 2}]}, {'k': 2}]},
            # {'subs': [{'k': 1                                 }, {'k': 2}]}
            id='Merge sub sets 2',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: {'subsubs': ...}}},
            {'subs': [{'k': 1}, {'k': 2, 'subsubs': [{'i': 3}]}]},
            id='Merge sub sets 3',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {0}}, 0: {'subsubs': {1}}}},
            {'subs': [{'k': 1, 'subsubs': []}, {'k': 2, 'subsubs': []}]},
            id='Merge sub sets 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {0: {'i'}}}, 0: {'subsubs': {1}}}},
            {'subs': [{'k': 1, 'subsubs': [{'j': 1}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
            id='Merge sub dict-set',
        ),
        pytest.param({'subs': {'__all__': {'subsubs'}, 0: {'k'}}}, {'subs': [{}, {'k': 2}]}, id='Different keys 1'),
        pytest.param(
            {'subs': {'__all__': {'subsubs': ...}, 0: {'k'}}}, {'subs': [{}, {'k': 2}]}, id='Different keys 2'
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs'}, 0: {'k': ...}}}, {'subs': [{}, {'k': 2}]}, id='Different keys 3'
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
            id='Nested different keys 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i': ...}, 0: {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
            id='Nested different keys 2',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j': ...}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
            id='Nested different keys 3',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs'}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1}, {'i': 2}]}, {'k': 2}]},
            id='Ignore __all__ for index with defined exclude 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: ...}},
            {'subs': [{'k': 2, 'subsubs': [{'i': 3}]}]},
            id='Ignore __all__ for index with defined exclude 2',
        ),
        pytest.param(
            {'subs': {'__all__': ..., 0: {'subsubs'}}},
            {'subs': [{'k': 1}]},
            id='Ignore __all__ for index with defined exclude 3',
        ),
    ],
)
def test_advanced_exclude_nested_lists(exclude, expected):
    class SubSubModel(BaseModel):
        i: int
        j: int

    class SubModel(BaseModel):
        k: int
        subsubs: List[SubSubModel]

    class Model(BaseModel):
        subs: List[SubModel]

    m = Model(subs=[dict(k=1, subsubs=[dict(i=1, j=1), dict(i=2, j=2)]), dict(k=2, subsubs=[dict(i=3, j=3)])])

    assert m.model_dump(exclude=exclude) == expected


@pytest.mark.parametrize(
    'include,expected',
    [
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}}},
            {'subs': [{'subsubs': [{'i': 1}, {'i': 2}]}, {'subsubs': [{'i': 3}]}]},
            id='Normal nested __all__',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3}]}]},
            id='Merge sub dicts 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': ...}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'subsubs': [{'j': 1}, {'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Merge sub dicts 2',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: {'subsubs': ...}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'j': 3}]}]},
            id='Merge sub dicts 3',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {0}}, 0: {'subsubs': {1}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Merge sub sets',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {0: {'i'}}}, 0: {'subsubs': {1}}}},
            {'subs': [{'subsubs': [{'i': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3}]}]},
            id='Merge sub dict-set',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs'}, 0: {'k'}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Nested different keys 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': ...}, 0: {'k'}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Nested different keys 2',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs'}, 0: {'k': ...}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Nested different keys 3',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j'}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Nested different keys 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i': ...}, 0: {'j'}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Nested different keys 2',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j': ...}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Nested different keys 3',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs'}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'subsubs': [{'j': 1}, {'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Ignore __all__ for index with defined include 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: ...}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'j': 3}]}]},
            id='Ignore __all__ for index with defined include 2',
        ),
        pytest.param(
            {'subs': {'__all__': ..., 0: {'subsubs'}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'k': 2, 'subsubs': [{'i': 3, 'j': 3}]}]},
            id='Ignore __all__ for index with defined include 3',
        ),
    ],
)
def test_advanced_include_nested_lists(include, expected):
    class SubSubModel(BaseModel):
        i: int
        j: int

    class SubModel(BaseModel):
        k: int
        subsubs: List[SubSubModel]

    class Model(BaseModel):
        subs: List[SubModel]

    m = Model(subs=[dict(k=1, subsubs=[dict(i=1, j=1), dict(i=2, j=2)]), dict(k=2, subsubs=[dict(i=3, j=3)])])

    assert m.model_dump(include=include) == expected


def test_field_set_ignore_extra():
    class Model(BaseModel):
        model_config = ConfigDict(extra='ignore')
        a: int
        b: int
        c: int = 3

    m = Model(a=1, b=2)
    assert m.model_dump() == {'a': 1, 'b': 2, 'c': 3}
    assert m.model_fields_set == {'a', 'b'}
    assert m.model_dump(exclude_unset=True) == {'a': 1, 'b': 2}

    m2 = Model(a=1, b=2, d=4)
    assert m2.model_dump() == {'a': 1, 'b': 2, 'c': 3}
    assert m2.model_fields_set == {'a', 'b'}
    assert m2.model_dump(exclude_unset=True) == {'a': 1, 'b': 2}


def test_field_set_allow_extra():
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')
        a: int
        b: int
        c: int = 3

    m = Model(a=1, b=2)
    assert m.model_dump() == {'a': 1, 'b': 2, 'c': 3}
    assert m.model_fields_set == {'a', 'b'}
    assert m.model_dump(exclude_unset=True) == {'a': 1, 'b': 2}

    m2 = Model(a=1, b=2, d=4)
    assert m2.model_dump() == {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    assert m2.model_fields_set == {'a', 'b', 'd'}
    assert m2.model_dump(exclude_unset=True) == {'a': 1, 'b': 2, 'd': 4}


def test_field_set_field_name():
    class Model(BaseModel):
        a: int
        field_set: int
        b: int = 3

    assert Model(a=1, field_set=2).model_dump() == {'a': 1, 'field_set': 2, 'b': 3}
    assert Model(a=1, field_set=2).model_dump(exclude_unset=True) == {'a': 1, 'field_set': 2}
    assert Model.model_construct(a=1, field_set=3).model_dump() == {'a': 1, 'field_set': 3, 'b': 3}


def test_values_order():
    class Model(BaseModel):
        a: int = 1
        b: int = 2
        c: int = 3

    m = Model(c=30, b=20, a=10)
    assert list(m) == [('a', 10), ('b', 20), ('c', 30)]


def test_inheritance():
    class Foo(BaseModel):
        a: float = ...

    with pytest.raises(
        TypeError,
        match=(
            "Field 'a' defined on a base class was overridden by a non-annotated attribute. "
            'All field definitions, including overrides, require a type annotation.'
        ),
    ):

        class Bar(Foo):
            x: float = 12.3
            a = 123.0

    class Bar2(Foo):
        x: float = 12.3
        a: float = 123.0

    assert Bar2().model_dump() == {'x': 12.3, 'a': 123.0}

    class Bar3(Foo):
        x: float = 12.3
        a: float = Field(default=123.0)

    assert Bar3().model_dump() == {'x': 12.3, 'a': 123.0}


def test_inheritance_subclass_default():
    class MyStr(str):
        pass

    # Confirm hint supports a subclass default
    class Simple(BaseModel):
        x: str = MyStr('test')

        model_config = dict(arbitrary_types_allowed=True)

    # Confirm hint on a base can be overridden with a subclass default on a subclass
    class Base(BaseModel):
        x: str
        y: str

    class Sub(Base):
        x: str = MyStr('test')
        y: MyStr = MyStr('test')  # force subtype

        model_config = dict(arbitrary_types_allowed=True)

    assert Sub.model_fields['x'].annotation == str
    assert Sub.model_fields['y'].annotation == MyStr


def test_invalid_type():
    with pytest.raises(PydanticSchemaGenerationError) as exc_info:

        class Model(BaseModel):
            x: 43 = 123

    assert 'Unable to generate pydantic-core schema for 43' in exc_info.value.args[0]


class CustomStr(str):
    def foobar(self):
        return 7


@pytest.mark.parametrize(
    'value,expected',
    [
        ('a string', 'a string'),
        (b'some bytes', 'some bytes'),
        (bytearray('foobar', encoding='utf8'), 'foobar'),
        (StrEnum.a, 'a10'),
        (CustomStr('whatever'), 'whatever'),
    ],
)
def test_valid_string_types(value, expected):
    class Model(BaseModel):
        v: str

    assert Model(v=value).v == expected


@pytest.mark.parametrize(
    'value,errors',
    [
        (
            {'foo': 'bar'},
            [{'input': {'foo': 'bar'}, 'loc': ('v',), 'msg': 'Input should be a valid string', 'type': 'string_type'}],
        ),
        (
            [1, 2, 3],
            [{'input': [1, 2, 3], 'loc': ('v',), 'msg': 'Input should be a valid string', 'type': 'string_type'}],
        ),
    ],
)
def test_invalid_string_types(value, errors):
    class Model(BaseModel):
        v: str

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors(include_url=False) == errors


def test_inheritance_config():
    class Parent(BaseModel):
        a: str

    class Child(Parent):
        model_config = ConfigDict(str_to_lower=True)
        b: str

    m1 = Parent(a='A')
    m2 = Child(a='A', b='B')
    assert repr(m1) == "Parent(a='A')"
    assert repr(m2) == "Child(a='a', b='b')"


def test_partial_inheritance_config():
    class Parent(BaseModel):
        a: int = Field(ge=0)

    class Child(Parent):
        b: int = Field(ge=0)

    Child(a=0, b=0)
    with pytest.raises(ValidationError) as exc_info:
        Child(a=-1, b=0)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'ge': 0},
            'input': -1,
            'loc': ('a',),
            'msg': 'Input should be greater than or equal to 0',
            'type': 'greater_than_equal',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Child(a=0, b=-1)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'ge': 0},
            'input': -1,
            'loc': ('b',),
            'msg': 'Input should be greater than or equal to 0',
            'type': 'greater_than_equal',
        }
    ]


def test_annotation_inheritance():
    class A(BaseModel):
        integer: int = 1

    class B(A):
        integer: int = 2

    assert B.model_fields['integer'].annotation == int

    class C(A):
        integer: str = 'G'

    assert C.__annotations__['integer'] == str
    assert C.model_fields['integer'].annotation == str

    with pytest.raises(
        TypeError,
        match=(
            "Field 'integer' defined on a base class was overridden by a non-annotated attribute. "
            "All field definitions, including overrides, require a type annotation."
        ),
    ):

        class D(A):
            integer = 'G'


def test_string_none():
    class Model(BaseModel):
        model_config = ConfigDict(extra='ignore')
        a: constr(min_length=20, max_length=1000) = ...

    with pytest.raises(ValidationError) as exc_info:
        Model(a=None)
    assert exc_info.value.errors(include_url=False) == [
        {'input': None, 'loc': ('a',), 'msg': 'Input should be a valid string', 'type': 'string_type'}
    ]


# def test_return_errors_ok():
#     class Model(BaseModel):
#         foo: int
#         bar: List[int]
#
#     assert validate_model(Model, {'foo': '123', 'bar': (1, 2, 3)}) == (
#         {'foo': 123, 'bar': [1, 2, 3]},
#         {'foo', 'bar'},
#         None,
#     )
#     d, f, e = validate_model(Model, {'foo': '123', 'bar': (1, 2, 3)}, False)
#     assert d == {'foo': 123, 'bar': [1, 2, 3]}
#     assert f == {'foo', 'bar'}
#     assert e is None


# def test_return_errors_error():
#     class Model(BaseModel):
#         foo: int
#         bar: List[int]
#
#     d, f, e = validate_model(Model, {'foo': '123', 'bar': (1, 2, 'x')}, False)
#     assert d == {'foo': 123}
#     assert f == {'foo', 'bar'}
#     assert e.errors() == [{'loc': ('bar', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]
#
#     d, f, e = validate_model(Model, {'bar': (1, 2, 3)}, False)
#     assert d == {'bar': [1, 2, 3]}
#     assert f == {'bar'}
#     assert e.errors() == [{'loc': ('foo',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_optional_required():
    class Model(BaseModel):
        bar: Optional[int]

    assert Model(bar=123).model_dump() == {'bar': 123}
    assert Model(bar=None).model_dump() == {'bar': None}

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('bar',), 'msg': 'Field required', 'type': 'missing'}
    ]


def test_unable_to_infer():
    with pytest.raises(
        errors.PydanticUserError,
        match=re.escape(
            "A non-annotated attribute was detected: `x = None`. All model fields require a type annotation; "
            "if `x` is not meant to be a field, you may be able to resolve this error by annotating it as a "
            "`ClassVar` or updating `model_config['ignored_types']`"
        ),
    ):

        class InvalidDefinitionModel(BaseModel):
            x = None


def test_multiple_errors():
    class Model(BaseModel):
        a: Union[None, int, float, Decimal]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foobar')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a', 'int'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'foobar',
        },
        {
            'type': 'float_parsing',
            'loc': ('a', 'float'),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'foobar',
        },
        {
            'type': 'is_instance_of',
            'loc': (
                'a',
                'function-after[check_digits_validator(), json-or-python[json=function-after[to_decimal(), union[float,int,constrained-str,function-plain[<lambda>()]]],python=lax-or-strict[lax=union[is-instance[Decimal],function-after[to_decimal(), union[float,int,constrained-str,function-plain[<lambda>()]]]],strict=is-instance[Decimal]]]]',  # noqa: E501
                'is-instance[Decimal]',
            ),
            'msg': 'Input should be an instance of Decimal',
            'input': 'foobar',
            'ctx': {'class': 'Decimal'},
        },
        {
            'type': 'decimal_parsing',
            'loc': (
                'a',
                'function-after[check_digits_validator(), json-or-python[json=function-after[to_decimal(), union[float,int,constrained-str,function-plain[<lambda>()]]],python=lax-or-strict[lax=union[is-instance[Decimal],function-after[to_decimal(), union[float,int,constrained-str,function-plain[<lambda>()]]]],strict=is-instance[Decimal]]]]',  # noqa: E501
                'function-after[to_decimal(), union[float,int,constrained-str,function-plain[<lambda>()]]]',
            ),
            'msg': 'Input should be a valid decimal',
            'input': 'foobar',
        },
    ]

    assert Model(a=1.5).a == 1.5
    assert Model(a=None).a is None


def test_validate_default():
    class Model(BaseModel):
        model_config = ConfigDict(validate_default=True)
        a: int
        b: int

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {}, 'loc': ('b',), 'msg': 'Field required', 'type': 'missing'},
    ]


def test_force_extra():
    class Model(BaseModel):
        model_config = ConfigDict(extra='ignore')
        foo: int

    assert Model.model_config['extra'] == 'ignore'


def test_submodel_different_type():
    class Foo(BaseModel):
        a: int

    class Bar(BaseModel):
        b: int

    class Spam(BaseModel):
        c: Foo

    assert Spam(c={'a': '123'}).model_dump() == {'c': {'a': 123}}
    with pytest.raises(ValidationError):
        Spam(c={'b': '123'})

    assert Spam(c=Foo(a='123')).model_dump() == {'c': {'a': 123}}
    with pytest.raises(ValidationError):
        Spam(c=Bar(b='123'))


def test_self():
    class Model(BaseModel):
        self: str

    m = Model.model_validate(dict(self='some value'))
    assert m.model_dump() == {'self': 'some value'}
    assert m.self == 'some value'
    assert m.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'self': {'title': 'Self', 'type': 'string'}},
        'required': ['self'],
    }


def test_self_recursive():
    class SubModel(BaseModel):
        self: int

    class Model(BaseModel):
        sm: SubModel

    m = Model.model_validate({'sm': {'self': '123'}})
    assert m.model_dump() == {'sm': {'self': 123}}


def test_custom_init():
    class Model(BaseModel):
        x: int

        def __init__(self, x: int, y: int):
            if isinstance(y, str):
                y = len(y)
            super().__init__(x=x + int(y))

    assert Model(x=1, y=1).x == 2
    assert Model.model_validate({'x': 1, 'y': 1}).x == 2
    assert Model.model_validate_json('{"x": 1, "y": 2}').x == 3

    # For documentation purposes: type hints on __init__ are not currently used for validation:
    assert Model.model_validate({'x': 1, 'y': 'abc'}).x == 4


def test_nested_custom_init():
    class NestedModel(BaseModel):
        self: str
        modified_number: int = 1

        def __init__(someinit, **kwargs):
            super().__init__(**kwargs)
            someinit.modified_number += 1

    class TopModel(BaseModel):
        self: str
        nest: NestedModel

    m = TopModel.model_validate(dict(self='Top Model', nest=dict(self='Nested Model', modified_number=0)))
    assert m.self == 'Top Model'
    assert m.nest.self == 'Nested Model'
    assert m.nest.modified_number == 1


def test_init_inspection():
    calls = []

    class Foobar(BaseModel):
        x: int

        def __init__(self, **data) -> None:
            with pytest.raises(AttributeError):
                calls.append(data)
                assert self.x
            super().__init__(**data)

    Foobar(x=1)
    Foobar.model_validate({'x': 2})
    Foobar.model_validate_json('{"x": 3}')
    assert calls == [{'x': 1}, {'x': 2}, {'x': 3}]


def test_type_on_annotation():
    class FooBar:
        pass

    class Model(BaseModel):
        a: int = int
        b: Type[int]
        c: Type[int] = int
        d: FooBar = FooBar
        e: Type[FooBar]
        f: Type[FooBar] = FooBar
        g: Sequence[Type[FooBar]] = [FooBar]
        h: Union[Type[FooBar], Sequence[Type[FooBar]]] = FooBar
        i: Union[Type[FooBar], Sequence[Type[FooBar]]] = [FooBar]

        model_config = dict(arbitrary_types_allowed=True)

    assert Model.model_fields.keys() == set('abcdefghi')


def test_assign_type():
    class Parent:
        def echo(self):
            return 'parent'

    class Child(Parent):
        def echo(self):
            return 'child'

    class Different:
        def echo(self):
            return 'different'

    class Model(BaseModel):
        v: Type[Parent] = Parent

    assert Model(v=Parent).v().echo() == 'parent'
    assert Model().v().echo() == 'parent'
    assert Model(v=Child).v().echo() == 'child'
    with pytest.raises(ValidationError) as exc_info:
        Model(v=Different)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_assign_type.<locals>.Parent'},
            'input': HasRepr("<class 'tests.test_edge_cases.test_assign_type.<locals>.Different'>"),
            'loc': ('v',),
            'msg': 'Input should be a subclass of test_assign_type.<locals>.Parent',
            'type': 'is_subclass_of',
        }
    ]


def test_optional_subfields():
    class Model(BaseModel):
        a: Optional[int]

    assert Model.model_fields['a'].annotation == Optional[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foobar')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'foobar',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'}
    ]

    assert Model(a=None).a is None
    assert Model(a=12).a == 12


def test_validated_optional_subfields():
    class Model(BaseModel):
        a: Optional[int]

        @field_validator('a')
        @classmethod
        def check_a(cls, v):
            return v

    assert Model.model_fields['a'].annotation == Optional[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foobar')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'foobar',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('a',), 'msg': 'Field required', 'type': 'missing'}
    ]

    assert Model(a=None).a is None
    assert Model(a=12).a == 12


def test_optional_field_constraints():
    class MyModel(BaseModel):
        my_int: Optional[int] = Field(..., ge=3)

    with pytest.raises(ValidationError) as exc_info:
        MyModel(my_int=2)
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'ge': 3},
            'input': 2,
            'loc': ('my_int',),
            'msg': 'Input should be greater than or equal to 3',
            'type': 'greater_than_equal',
        }
    ]


def test_field_str_shape():
    class Model(BaseModel):
        a: List[int]

    assert repr(Model.model_fields['a']) == 'FieldInfo(annotation=List[int], required=True)'
    assert str(Model.model_fields['a']) == 'annotation=List[int] required=True'


T1 = TypeVar('T1')
T2 = TypeVar('T2')


class DisplayGen(Generic[T1, T2]):
    def __init__(self, t1: T1, t2: T2):
        self.t1 = t1
        self.t2 = t2

    @classmethod
    def __get_validators__(cls):
        def validator(v):
            return v

        yield validator


@pytest.mark.parametrize(
    'type_,expected',
    [
        (int, 'int'),
        (Optional[int], 'Union[int, NoneType]'),
        (Union[None, int, str], 'Union[NoneType, int, str]'),
        (Union[int, str, bytes], 'Union[int, str, bytes]'),
        (List[int], 'List[int]'),
        (Tuple[int, str, bytes], 'Tuple[int, str, bytes]'),
        (Union[List[int], Set[bytes]], 'Union[List[int], Set[bytes]]'),
        (List[Tuple[int, int]], 'List[Tuple[int, int]]'),
        (Dict[int, str], 'Dict[int, str]'),
        (FrozenSet[int], 'FrozenSet[int]'),
        (Tuple[int, ...], 'Tuple[int, ...]'),
        (Optional[List[int]], 'Union[List[int], NoneType]'),
        (dict, 'dict'),
        pytest.param(
            DisplayGen[bool, str],
            'DisplayGen[bool, str]',
            marks=pytest.mark.skipif(sys.version_info[:2] <= (3, 9), reason='difference in __name__ between versions'),
        ),
        pytest.param(
            DisplayGen[bool, str],
            'tests.test_edge_cases.DisplayGen[bool, str]',
            marks=pytest.mark.skipif(sys.version_info[:2] > (3, 9), reason='difference in __name__ between versions'),
        ),
    ],
)
def test_field_type_display(type_, expected):
    class Model(BaseModel):
        a: type_

        model_config = dict(arbitrary_types_allowed=True)

    assert re.search(fr'\(annotation={re.escape(expected)},', str(Model.model_fields))


def test_any_none():
    class MyModel(BaseModel):
        foo: Any

    m = MyModel(foo=None)
    assert dict(m) == {'foo': None}


def test_type_var_any():
    Foobar = TypeVar('Foobar')

    class MyModel(BaseModel):
        foo: Foobar

    assert MyModel.model_json_schema() == {
        'properties': {'foo': {'title': 'Foo'}},
        'required': ['foo'],
        'title': 'MyModel',
        'type': 'object',
    }
    assert MyModel(foo=None).foo is None
    assert MyModel(foo='x').foo == 'x'
    assert MyModel(foo=123).foo == 123


def test_type_var_constraint():
    Foobar = TypeVar('Foobar', int, str)

    class MyModel(BaseModel):
        foo: Foobar

    assert MyModel.model_json_schema() == {
        'title': 'MyModel',
        'type': 'object',
        'properties': {'foo': {'title': 'Foo', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]}},
        'required': ['foo'],
    }
    with pytest.raises(ValidationError) as exc_info:
        MyModel(foo=None)
    assert exc_info.value.errors(include_url=False) == [
        {'input': None, 'loc': ('foo', 'int'), 'msg': 'Input should be a valid integer', 'type': 'int_type'},
        {'input': None, 'loc': ('foo', 'str'), 'msg': 'Input should be a valid string', 'type': 'string_type'},
    ]

    with pytest.raises(ValidationError):
        MyModel(foo=[1, 2, 3])
    assert exc_info.value.errors(include_url=False) == [
        {'input': None, 'loc': ('foo', 'int'), 'msg': 'Input should be a valid integer', 'type': 'int_type'},
        {'input': None, 'loc': ('foo', 'str'), 'msg': 'Input should be a valid string', 'type': 'string_type'},
    ]

    assert MyModel(foo='x').foo == 'x'
    assert MyModel(foo=123).foo == 123


def test_type_var_bound():
    Foobar = TypeVar('Foobar', bound=int)

    class MyModel(BaseModel):
        foo: Foobar

    assert MyModel.model_json_schema() == {
        'title': 'MyModel',
        'type': 'object',
        'properties': {'foo': {'title': 'Foo', 'type': 'integer'}},
        'required': ['foo'],
    }
    with pytest.raises(ValidationError) as exc_info:
        MyModel(foo=None)
    assert exc_info.value.errors(include_url=False) == [
        {'input': None, 'loc': ('foo',), 'msg': 'Input should be a valid integer', 'type': 'int_type'}
    ]

    with pytest.raises(ValidationError):
        MyModel(foo='x')
    assert exc_info.value.errors(include_url=False) == [
        {'input': None, 'loc': ('foo',), 'msg': 'Input should be a valid integer', 'type': 'int_type'}
    ]
    assert MyModel(foo=123).foo == 123


def test_dict_bare():
    class MyModel(BaseModel):
        foo: Dict

    m = MyModel(foo={'x': 'a', 'y': None})
    assert m.foo == {'x': 'a', 'y': None}


def test_list_bare():
    class MyModel(BaseModel):
        foo: List

    m = MyModel(foo=[1, 2, None])
    assert m.foo == [1, 2, None]


def test_dict_any():
    class MyModel(BaseModel):
        foo: Dict[str, Any]

    m = MyModel(foo={'x': 'a', 'y': None})
    assert m.foo == {'x': 'a', 'y': None}


def test_modify_fields():
    class Foo(BaseModel):
        foo: List[List[int]]

        @field_validator('foo')
        @classmethod
        def check_something(cls, value):
            return value

    class Bar(Foo):
        pass

    assert repr(Foo.model_fields['foo']) == 'FieldInfo(annotation=List[List[int]], required=True)'
    assert repr(Bar.model_fields['foo']) == 'FieldInfo(annotation=List[List[int]], required=True)'
    assert Foo(foo=[[0, 1]]).foo == [[0, 1]]
    assert Bar(foo=[[0, 1]]).foo == [[0, 1]]


def test_exclude_none():
    class MyModel(BaseModel):
        a: Optional[int] = None
        b: int = 2

    m = MyModel(a=5)
    assert m.model_dump(exclude_none=True) == {'a': 5, 'b': 2}

    m = MyModel(b=3)
    assert m.model_dump(exclude_none=True) == {'b': 3}
    assert m.model_dump_json(exclude_none=True) == '{"b":3}'


def test_exclude_none_recursive():
    class ModelA(BaseModel):
        a: Optional[int] = None
        b: int = 1

    class ModelB(BaseModel):
        c: int
        d: int = 2
        e: ModelA
        f: Optional[str] = None

    m = ModelB(c=5, e={'a': 0})
    assert m.model_dump() == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}, 'f': None}
    assert m.model_dump(exclude_none=True) == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}
    assert dict(m) == {'c': 5, 'd': 2, 'e': ModelA(a=0), 'f': None}

    m = ModelB(c=5, e={'b': 20}, f='test')
    assert m.model_dump() == {'c': 5, 'd': 2, 'e': {'a': None, 'b': 20}, 'f': 'test'}
    assert m.model_dump(exclude_none=True) == {'c': 5, 'd': 2, 'e': {'b': 20}, 'f': 'test'}
    assert dict(m) == {'c': 5, 'd': 2, 'e': ModelA(b=20), 'f': 'test'}


def test_exclude_none_with_extra():
    class MyModel(BaseModel):
        model_config = ConfigDict(extra='allow')
        a: str = 'default'
        b: Optional[str] = None

    m = MyModel(a='a', c='c')

    assert m.model_dump(exclude_none=True) == {'a': 'a', 'c': 'c'}
    assert m.model_dump() == {'a': 'a', 'b': None, 'c': 'c'}

    m = MyModel(a='a', b='b', c=None)

    assert m.model_dump(exclude_none=True) == {'a': 'a', 'b': 'b'}
    assert m.model_dump() == {'a': 'a', 'b': 'b', 'c': None}


def test_str_method_inheritance():
    import pydantic

    class Foo(pydantic.BaseModel):
        x: int = 3
        y: int = 4

        def __str__(self):
            return str(self.y + self.x)

    class Bar(Foo):
        z: bool = False

    assert str(Foo()) == '7'
    assert str(Bar()) == '7'


def test_repr_method_inheritance():
    import pydantic

    class Foo(pydantic.BaseModel):
        x: int = 3
        y: int = 4

        def __repr__(self):
            return repr(self.y + self.x)

    class Bar(Foo):
        z: bool = False

    assert repr(Foo()) == '7'
    assert repr(Bar()) == '7'


def test_optional_validator():
    val_calls = []

    class Model(BaseModel):
        something: Optional[str]

        @field_validator('something')
        @classmethod
        def check_something(cls, v):
            val_calls.append(v)
            return v

    with pytest.raises(ValidationError) as exc_info:
        assert Model().model_dump() == {'something': None}
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('something',), 'msg': 'Field required', 'type': 'missing'}
    ]

    assert Model(something=None).model_dump() == {'something': None}
    assert Model(something='hello').model_dump() == {'something': 'hello'}
    assert val_calls == [None, 'hello']


def test_required_optional():
    class Model(BaseModel):
        nullable1: Optional[int] = ...
        nullable2: Optional[int] = Field(...)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('nullable1',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {}, 'loc': ('nullable2',), 'msg': 'Field required', 'type': 'missing'},
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable1=1)
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'nullable1': 1}, 'loc': ('nullable2',), 'msg': 'Field required', 'type': 'missing'}
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable2=2)
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'nullable2': 2}, 'loc': ('nullable1',), 'msg': 'Field required', 'type': 'missing'}
    ]
    assert Model(nullable1=None, nullable2=None).model_dump() == {'nullable1': None, 'nullable2': None}
    assert Model(nullable1=1, nullable2=2).model_dump() == {'nullable1': 1, 'nullable2': 2}
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable1='some text')
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'some text',
            'loc': ('nullable1',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
        {'input': {'nullable1': 'some text'}, 'loc': ('nullable2',), 'msg': 'Field required', 'type': 'missing'},
    ]


def test_required_any():
    class Model(BaseModel):
        optional1: Any
        optional2: Any = None
        optional3: Optional[Any] = None
        nullable1: Any = ...
        nullable2: Any = Field(...)
        nullable3: Optional[Any]

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('optional1',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {}, 'loc': ('nullable1',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {}, 'loc': ('nullable2',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {}, 'loc': ('nullable3',), 'msg': 'Field required', 'type': 'missing'},
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable1='a')
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'nullable1': 'a'}, 'loc': ('optional1',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'nullable1': 'a'}, 'loc': ('nullable2',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'nullable1': 'a'}, 'loc': ('nullable3',), 'msg': 'Field required', 'type': 'missing'},
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable2=False)
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'nullable2': False}, 'loc': ('optional1',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'nullable2': False}, 'loc': ('nullable1',), 'msg': 'Field required', 'type': 'missing'},
        {'input': {'nullable2': False}, 'loc': ('nullable3',), 'msg': 'Field required', 'type': 'missing'},
    ]
    with pytest.raises(ValidationError) as exc_info:
        assert Model(nullable1=None, nullable2=None).model_dump() == {
            'optional1': None,
            'optional2': None,
            'nullable1': None,
            'nullable2': None,
        }
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': {'nullable1': None, 'nullable2': None},
            'loc': ('optional1',),
            'msg': 'Field required',
            'type': 'missing',
        },
        {
            'input': {'nullable1': None, 'nullable2': None},
            'loc': ('nullable3',),
            'msg': 'Field required',
            'type': 'missing',
        },
    ]
    assert Model(optional1=None, nullable1=1, nullable2='two', nullable3=None).model_dump() == {
        'optional1': None,
        'optional2': None,
        'optional3': None,
        'nullable1': 1,
        'nullable2': 'two',
        'nullable3': None,
    }
    assert Model(optional1='op1', optional2=False, nullable1=1, nullable2='two', nullable3='three').model_dump() == {
        'optional1': 'op1',
        'optional2': False,
        'optional3': None,
        'nullable1': 1,
        'nullable2': 'two',
        'nullable3': 'three',
    }


def test_custom_generic_validators():
    T1 = TypeVar('T1')
    T2 = TypeVar('T2')

    class MyGen(Generic[T1, T2]):
        def __init__(self, t1: T1, t2: T2):
            self.t1 = t1
            self.t2 = t2

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source: Any,
        ):
            schema = core_schema.is_instance_schema(cls)

            args = get_args(source)
            if not args:
                return schema

            t1_f = TypeAdapter(args[0]).validate_python
            t2_f = TypeAdapter(args[1]).validate_python

            def convert_to_init_error(e: ErrorDetails, loc: str) -> InitErrorDetails:
                init_e = {'type': e['type'], 'loc': e['loc'] + (loc,), 'input': e['input']}
                if 'ctx' in e:
                    init_e['ctx'] = e['ctx']
                return init_e

            def validate(v, _info):
                if not args:
                    return v
                try:
                    v.t1 = t1_f(v.t1)
                except ValidationError as exc:
                    raise ValidationError.from_exception_data(
                        exc.title, [convert_to_init_error(e, 't1') for e in exc.errors()]
                    ) from exc
                try:
                    v.t2 = t2_f(v.t2)
                except ValidationError as exc:
                    raise ValidationError.from_exception_data(
                        exc.title, [convert_to_init_error(e, 't2') for e in exc.errors()]
                    ) from exc
                return v

            return core_schema.general_after_validator_function(validate, schema)

    class Model(BaseModel):
        a: str
        gen: MyGen[str, bool]
        gen2: MyGen

        model_config = dict(arbitrary_types_allowed=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', gen='invalid', gen2='invalid')
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_custom_generic_validators.<locals>.MyGen'},
            'input': 'invalid',
            'loc': ('gen',),
            'msg': 'Input should be an instance of test_custom_generic_validators.<locals>.MyGen',
            'type': 'is_instance_of',
        },
        {
            'ctx': {'class': 'test_custom_generic_validators.<locals>.MyGen'},
            'input': 'invalid',
            'loc': ('gen2',),
            'msg': 'Input should be an instance of test_custom_generic_validators.<locals>.MyGen',
            'type': 'is_instance_of',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', gen=MyGen(t1='bar', t2='baz'), gen2=MyGen(t1='bar', t2='baz'))
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'baz',
            'loc': ('gen', 't2'),
            'msg': 'Input should be a valid boolean, unable to interpret input',
            'type': 'bool_parsing',
        }
    ]

    m = Model(a='foo', gen=MyGen(t1='bar', t2=True), gen2=MyGen(t1=1, t2=2))
    assert m.a == 'foo'
    assert m.gen.t1 == 'bar'
    assert m.gen.t2 is True
    assert m.gen2.t1 == 1
    assert m.gen2.t2 == 2


def test_custom_generic_arbitrary_allowed():
    T1 = TypeVar('T1')
    T2 = TypeVar('T2')

    class MyGen(Generic[T1, T2]):
        def __init__(self, t1: T1, t2: T2):
            self.t1 = t1
            self.t2 = t2

    class Model(BaseModel):
        a: str
        gen: MyGen[str, bool]

        model_config = dict(arbitrary_types_allowed=True)

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', gen='invalid')
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'class': 'test_custom_generic_arbitrary_allowed.<locals>.MyGen'},
            'input': 'invalid',
            'loc': ('gen',),
            'msg': 'Input should be an instance of ' 'test_custom_generic_arbitrary_allowed.<locals>.MyGen',
            'type': 'is_instance_of',
        }
    ]

    # No validation, no exception
    m = Model(a='foo', gen=MyGen(t1='bar', t2='baz'))
    assert m.a == 'foo'
    assert m.gen.t1 == 'bar'
    assert m.gen.t2 == 'baz'

    m = Model(a='foo', gen=MyGen(t1='bar', t2=True))
    assert m.a == 'foo'
    assert m.gen.t1 == 'bar'
    assert m.gen.t2 is True


def test_custom_generic_disallowed():
    T1 = TypeVar('T1')
    T2 = TypeVar('T2')

    class MyGen(Generic[T1, T2]):
        def __init__(self, t1: T1, t2: T2):
            self.t1 = t1
            self.t2 = t2

    match = (
        r'Unable to generate pydantic-core schema for (.*)MyGen\[str, bool\](.*). '
        r'Set `arbitrary_types_allowed=True` in the model_config to ignore this error'
    )
    with pytest.raises(TypeError, match=match):

        class Model(BaseModel):
            a: str
            gen: MyGen[str, bool]


def test_hashable_required():
    class Model(BaseModel):
        v: Hashable

    Model(v=None)
    with pytest.raises(ValidationError) as exc_info:
        Model(v=[])
    assert exc_info.value.errors(include_url=False) == [
        {'input': [], 'loc': ('v',), 'msg': 'Input should be hashable', 'type': 'is_hashable'}
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('v',), 'msg': 'Field required', 'type': 'missing'}
    ]


@pytest.mark.parametrize('default', [1, None])
def test_hashable_optional(default):
    class Model(BaseModel):
        v: Hashable = default

    Model(v=None)
    Model()


def test_hashable_serialization():
    class Model(BaseModel):
        v: Hashable

    class HashableButNotSerializable:
        def __hash__(self):
            return 0

    assert Model(v=(1,)).model_dump_json() == '{"v":[1]}'
    m = Model(v=HashableButNotSerializable())
    with pytest.raises(
        PydanticSerializationError, match='Unable to serialize unknown type:.*HashableButNotSerializable'
    ):
        m.model_dump_json()


def test_hashable_json_schema():
    class Model(BaseModel):
        v: Hashable

    with pytest.raises(
        PydanticInvalidForJsonSchema,
        match=re.escape(
            "Cannot generate a JsonSchema for core_schema.IsInstanceSchema (<class 'collections.abc.Hashable'>)"
        ),
    ):
        Model.model_json_schema()


def test_default_factory_called_once():
    """It should never call `default_factory` more than once even when `validate_all` is set"""

    v = 0

    def factory() -> int:
        nonlocal v
        v += 1
        return v

    class MyModel(BaseModel):
        model_config = ConfigDict(validate_default=True)
        id: int = Field(default_factory=factory)

    m1 = MyModel()
    assert m1.id == 1

    class MyBadModel(BaseModel):
        model_config = ConfigDict(validate_default=True)
        id: List[str] = Field(default_factory=factory)

    with pytest.raises(ValidationError) as exc_info:
        MyBadModel()
    assert v == 2  # `factory` has been called to run validation
    assert exc_info.value.errors(include_url=False) == [
        {'input': 2, 'loc': ('id',), 'msg': 'Input should be a valid list', 'type': 'list_type'}
    ]


def test_default_factory_validator_child():
    class Parent(BaseModel):
        foo: List[str] = Field(default_factory=list)

        @field_validator('foo', mode='before')
        @classmethod
        def mutate_foo(cls, v):
            return [f'{x}-1' for x in v]

    assert Parent(foo=['a', 'b']).foo == ['a-1', 'b-1']

    class Child(Parent):
        pass

    assert Child(foo=['a', 'b']).foo == ['a-1', 'b-1']


def test_resolve_annotations_module_missing(tmp_path):
    # see https://github.com/pydantic/pydantic/issues/2363
    file_path = tmp_path / 'module_to_load.py'
    # language=Python
    file_path.write_text(
        """
from pydantic import BaseModel
class User(BaseModel):
    id: int
    name: str = 'Jane Doe'
"""
    )

    spec = importlib.util.spec_from_file_location('my_test_module', file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.User(id=12).model_dump() == {'id': 12, 'name': 'Jane Doe'}


def test_iter_coverage():
    class MyModel(BaseModel):
        x: int = 1
        y: str = 'a'

    with pytest.warns(
        PydanticDeprecatedSince20, match='The private method `_iter` will be removed and should no longer be used.'
    ):
        assert list(MyModel()._iter(by_alias=True)) == [('x', 1), ('y', 'a')]


def test_frozen_config_and_field():
    class Foo(BaseModel):
        model_config = ConfigDict(frozen=False, validate_assignment=True)
        a: str = Field(...)

    assert Foo.model_fields['a'].metadata == []

    f = Foo(a='x')
    f.a = 'y'
    assert f.model_dump() == {'a': 'y'}

    class Bar(BaseModel):
        model_config = ConfigDict(validate_assignment=True)
        a: str = Field(..., frozen=True)
        c: Annotated[str, Field(frozen=True)]

    assert Bar.model_fields['a'].frozen

    b = Bar(a='x', c='z')
    with pytest.raises(ValidationError) as exc_info:
        b.a = 'y'
    assert exc_info.value.errors(include_url=False) == [
        {'input': 'y', 'loc': ('a',), 'msg': 'Field is frozen', 'type': 'frozen_field'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        b.c = 'y'
    assert exc_info.value.errors(include_url=False) == [
        {'input': 'y', 'loc': ('c',), 'msg': 'Field is frozen', 'type': 'frozen_field'}
    ]

    assert b.model_dump() == {'a': 'x', 'c': 'z'}


def test_arbitrary_types_allowed_custom_eq():
    class Foo:
        def __eq__(self, other):
            if other.__class__ is not Foo:
                raise TypeError(f'Cannot interpret {other.__class__.__name__!r} as a valid type')
            return True

    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        x: Foo = Foo()

    assert Model().x == Foo()


def test_bytes_subclass():
    class MyModel(BaseModel):
        my_bytes: bytes

    class BytesSubclass(bytes):
        def __new__(cls, data: bytes):
            self = bytes.__new__(cls, data)
            return self

    m = MyModel(my_bytes=BytesSubclass(b'foobar'))
    assert m.my_bytes.__class__ == BytesSubclass


def test_int_subclass():
    class MyModel(BaseModel):
        my_int: int

    class IntSubclass(int):
        def __new__(cls, data: int):
            self = int.__new__(cls, data)
            return self

    m = MyModel(my_int=IntSubclass(123))
    # This is expected behavior in `V2` because in pydantic-core we cast the value to a rust i64,
    # so the sub-type information is lost."
    # (more detail about how to handle this in: https://github.com/pydantic/pydantic/pull/5151#discussion_r1130691036)
    assert m.my_int.__class__ != IntSubclass
    assert isinstance(m.my_int, int)


def test_model_issubclass():
    assert not issubclass(int, BaseModel)

    class MyModel(BaseModel):
        x: int

    assert issubclass(MyModel, BaseModel)

    class Custom:
        __fields__ = True

    assert not issubclass(Custom, BaseModel)


def test_long_int():
    """
    see https://github.com/pydantic/pydantic/issues/1477 and in turn, https://github.com/python/cpython/issues/95778
    """

    class Model(BaseModel):
        x: int

    assert Model(x='1' * 4_300).x == int('1' * 4_300)

    too_long = '1' * 4_301
    with pytest.raises(ValidationError) as exc_info:
        Model(x=too_long)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing_size',
            'loc': ('x',),
            'msg': 'Unable to parse input string as an integer, exceeded maximum size',
            'input': too_long,
        }
    ]

    # this used to hang indefinitely
    with pytest.raises(ValidationError):
        Model(x='1' * (10**7))


def test_parent_field_with_default():
    class Parent(BaseModel):
        a: int = 1
        b: int = Field(2)

    class Child(Parent):
        c: int = 3

    c = Child()
    assert c.a == 1
    assert c.b == 2
    assert c.c == 3


@pytest.mark.parametrize(
    'bases',
    [
        (BaseModel, ABC),
        (ABC, BaseModel),
        (BaseModel,),
    ],
)
def test_abstractmethod_missing_for_all_decorators(bases):
    class AbstractSquare(*bases):
        side: float

        @field_validator('side')
        @classmethod
        @abstractmethod
        def my_field_validator(cls, v):
            raise NotImplementedError

        @model_validator(mode='wrap')
        @classmethod
        @abstractmethod
        def my_model_validator(cls, values, handler, info):
            raise NotImplementedError

        with pytest.warns(PydanticDeprecatedSince20):

            @root_validator(skip_on_failure=True)
            @classmethod
            @abstractmethod
            def my_root_validator(cls, values):
                raise NotImplementedError

        with pytest.warns(PydanticDeprecatedSince20):

            @validator('side')
            @classmethod
            @abstractmethod
            def my_validator(cls, value, **kwargs):
                raise NotImplementedError

        @model_serializer(mode='wrap')
        @abstractmethod
        def my_model_serializer(self, handler, info):
            raise NotImplementedError

        @field_serializer('side')
        @abstractmethod
        def my_serializer(self, v, _info):
            raise NotImplementedError

        @computed_field
        @property
        @abstractmethod
        def my_computed_field(self) -> Any:
            raise NotImplementedError

    class Square(AbstractSquare):
        pass

    with pytest.raises(
        TypeError,
        match=(
            "Can't instantiate abstract class Square with abstract methods"
            " my_computed_field,"
            " my_field_validator,"
            " my_model_serializer,"
            " my_model_validator,"
            " my_root_validator,"
            " my_serializer,"
            " my_validator"
        ),
    ):
        Square(side=1.0)


@pytest.mark.skipif(sys.version_info < (3, 9), reason='cannot use list.__class_getitem__ before 3.9')
def test_generic_wrapped_forwardref():
    class Operation(BaseModel):
        callbacks: list['PathItem']

    class PathItem(BaseModel):
        pass

    Operation.model_rebuild()

    Operation.model_validate({'callbacks': [PathItem()]})
    with pytest.raises(ValidationError) as exc_info:
        Operation.model_validate({'callbacks': [1]})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('callbacks', 0),
            'msg': 'Input should be a valid dictionary or instance of PathItem',
            'input': 1,
            'ctx': {'class_name': 'PathItem'},
        }
    ]


def test_plain_basemodel_field():
    class Model(BaseModel):
        x: BaseModel

    class Model2(BaseModel):
        pass

    assert Model(x=Model2()).x == Model2()
    with pytest.raises(ValidationError) as exc_info:
        Model(x=1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('x',),
            'msg': 'Input should be a valid dictionary or instance of BaseModel',
            'input': 1,
            'ctx': {'class_name': 'BaseModel'},
        }
    ]


def test_invalid_forward_ref_model():
    """
    This test is to document the fact that forward refs to a type with the same name as that of a field
    can cause problems, and to demonstrate a way to work around this.
    """
    # The problem:
    if sys.version_info >= (3, 11):
        error = RecursionError
        kwargs = {}
    else:
        error = TypeError
        kwargs = {
            'match': r'Forward references must evaluate to types\.'
            r' Got FieldInfo\(annotation=NoneType, required=False\)\.'
        }
    with pytest.raises(error, **kwargs):

        class M(BaseModel):
            B: ForwardRef('B') = Field(default=None)

    # The solution:
    class A(BaseModel):
        B: ForwardRef('__types["B"]') = Field()  # F821

    assert A.model_fields['B'].annotation == ForwardRef('__types["B"]')  # F821
    A.model_rebuild(raise_errors=False)
    assert A.model_fields['B'].annotation == ForwardRef('__types["B"]')  # F821

    class B(BaseModel):
        pass

    class C(BaseModel):
        pass

    assert not A.__pydantic_complete__
    types = {'B': B}
    A.model_rebuild(_types_namespace={'__types': types})
    assert A.__pydantic_complete__

    assert A(B=B()).B == B()
    with pytest.raises(ValidationError) as exc_info:
        A(B=C())
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': ('B',),
            'msg': 'Input should be a valid dictionary or instance of B',
            'input': C(),
            'ctx': {'class_name': 'B'},
        }
    ]


@pytest.mark.skipif(sys.version_info < (3, 9), reason='cannot parametrize types before 3.9')
@pytest.mark.parametrize(
    ('sequence_type', 'input_data', 'expected_error_type', 'expected_error_msg', 'expected_error_ctx'),
    [
        pytest.param(List[str], '1bc', 'list_type', 'Input should be a valid list', None, id='list[str]'),
        pytest.param(
            Sequence[str],
            '1bc',
            'sequence_str',
            "'str' instances are not allowed as a Sequence value",
            {'type_name': 'str'},
            id='Sequence[str]',
        ),
        pytest.param(
            Sequence[bytes],
            b'1bc',
            'sequence_str',
            "'bytes' instances are not allowed as a Sequence value",
            {'type_name': 'bytes'},
            id='Sequence[bytes]',
        ),
    ],
)
def test_sequences_str(sequence_type, input_data, expected_error_type, expected_error_msg, expected_error_ctx):
    input_sequence = [input_data[:1], input_data[1:]]
    expected_error = {
        'type': expected_error_type,
        'input': input_data,
        'loc': ('str_sequence',),
        'msg': expected_error_msg,
    }
    if expected_error_ctx is not None:
        expected_error.update(ctx=expected_error_ctx)

    class Model(BaseModel):
        str_sequence: sequence_type

    assert Model(str_sequence=input_sequence).str_sequence == input_sequence

    with pytest.raises(ValidationError) as e:
        Model(str_sequence=input_data)

    assert e.value.errors(include_url=False) == [expected_error]


def test_multiple_enums():
    """See https://github.com/pydantic/pydantic/issues/6270"""

    class MyEnum(Enum):
        a = auto()

    class MyModel(TypedDict):
        a: Optional[MyEnum]
        b: Optional[MyEnum]

    TypeAdapter(MyModel)
