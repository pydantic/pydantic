import importlib.util
import sys
from collections.abc import Hashable
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, FrozenSet, Generic, List, Optional, Sequence, Set, Tuple, Type, TypeVar, Union

import pytest

from pydantic import (
    BaseModel,
    BaseSettings,
    Extra,
    NoneStrBytes,
    StrBytes,
    ValidationError,
    compiled,
    constr,
    errors,
    validate_model,
    validator,
)
from pydantic.fields import Field

try:
    import cython
except ImportError:
    cython = None


def test_str_bytes():
    class Model(BaseModel):
        v: StrBytes = ...

    m = Model(v='s')
    assert m.v == 's'
    assert repr(m.__fields__['v']) == "ModelField(name='v', type=Union[str, bytes], required=True)"

    m = Model(v=b'b')
    assert m.v == 'b'

    with pytest.raises(ValidationError) as exc_info:
        Model(v=None)
    assert exc_info.value.errors() == [
        {'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'}
    ]


def test_str_bytes_none():
    class Model(BaseModel):
        v: NoneStrBytes = ...

    m = Model(v='s')
    assert m.v == 's'

    m = Model(v=b'b')
    assert m.v == 'b'

    m = Model(v=None)
    assert m.v is None


def test_union_int_str():
    class Model(BaseModel):
        v: Union[int, str] = ...

    m = Model(v=123)
    assert m.v == 123

    m = Model(v='123')
    assert m.v == 123

    m = Model(v=b'foobar')
    assert m.v == 'foobar'

    # here both validators work and it's impossible to work out which value "closer"
    m = Model(v=12.2)
    assert m.v == 12

    with pytest.raises(ValidationError) as exc_info:
        Model(v=None)
    assert exc_info.value.errors() == [
        {'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'}
    ]


def test_union_int_any():
    class Model(BaseModel):
        v: Union[int, Any]

    m = Model(v=123)
    assert m.v == 123

    m = Model(v='123')
    assert m.v == 123

    m = Model(v='foobar')
    assert m.v == 'foobar'

    m = Model(v=None)
    assert m.v is None


def test_union_priority():
    class ModelOne(BaseModel):
        v: Union[int, str] = ...

    class ModelTwo(BaseModel):
        v: Union[str, int] = ...

    assert ModelOne(v='123').v == 123
    assert ModelTwo(v='123').v == '123'


def test_typed_list():
    class Model(BaseModel):
        v: List[int] = ...

    m = Model(v=[1, 2, '3'])
    assert m.v == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 'x', 'y'])
    assert exc_info.value.errors() == [
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=1)
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_typed_set():
    class Model(BaseModel):
        v: Set[int] = ...

    assert Model(v={1, 2, '3'}).v == {1, 2, 3}
    assert Model(v=[1, 2, '3']).v == {1, 2, 3}

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 'x'])
    assert exc_info.value.errors() == [
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_dict_dict():
    class Model(BaseModel):
        v: Dict[str, int] = ...

    assert Model(v={'foo': 1}).dict() == {'v': {'foo': 1}}


def test_none_list():
    class Model(BaseModel):
        v = [None]

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'default': [None], 'type': 'array', 'items': {}}},
    }


@pytest.mark.parametrize(
    'value,result',
    [
        ({'a': 2, 'b': 4}, {'a': 2, 'b': 4}),
        ({1: '2', 'b': 4}, {'1': 2, 'b': 4}),
        ([('a', 2), ('b', 4)], {'a': 2, 'b': 4}),
    ],
)
def test_typed_dict(value, result):
    class Model(BaseModel):
        v: Dict[str, int] = ...

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'value,errors',
    [
        (1, [{'loc': ('v',), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}]),
        ({'a': 'b'}, [{'loc': ('v', 'a'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]),
        ([1, 2, 3], [{'loc': ('v',), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}]),
    ],
)
def test_typed_dict_error(value, errors):
    class Model(BaseModel):
        v: Dict[str, int] = ...

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


def test_dict_key_error():
    class Model(BaseModel):
        v: Dict[int, int] = ...

    assert Model(v={1: 2, '3': '4'}).v == {1: 2, 3: 4}

    with pytest.raises(ValidationError) as exc_info:
        Model(v={'foo': 2, '3': '4'})
    assert exc_info.value.errors() == [
        {'loc': ('v', '__key__'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_tuple():
    class Model(BaseModel):
        v: Tuple[int, float, bool]

    m = Model(v=[1.2, '2.2', 'true'])
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
        tuple_of_different_types=[4, 3, 2, 1],
        tuple_of_single_tuples=(('1',), (2,)),
    )
    assert m.dict() == {
        'empty_tuple': (),
        'simple_tuple': (1, 2, 3, 4),
        'tuple_of_different_types': (4, 3.0, '2', True),
        'tuple_of_single_tuples': ((1,), (2,)),
    }


@pytest.mark.parametrize(
    'dict_cls,frozenset_cls,list_cls,set_cls,tuple_cls,type_cls',
    [
        (Dict, FrozenSet, List, Set, Tuple, Type),
        (dict, frozenset, list, set, tuple, type),
    ],
)
@pytest.mark.skipif(
    sys.version_info < (3, 9) or compiled, reason='PEP585 generics only supported for python 3.9 and above'
)
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
    assert exc_info.value.errors() == [
        {
            'ctx': {'actual_length': 1, 'expected_length': 0},
            'loc': ('e3',),
            'msg': 'wrong tuple length 1, expected 0',
            'type': 'value_error.tuple.length',
        }
    ]

    Model(**(default_model_kwargs | {'f': Type2}))

    with pytest.raises(ValidationError) as exc_info:
        Model(**(default_model_kwargs | {'f1': Type2}))
    assert exc_info.value.errors() == [
        {
            'ctx': {'expected_class': 'Type1'},
            'loc': ('f1',),
            'msg': 'subclass of Type1 expected',
            'type': 'type_error.subclass',
        }
    ]


def test_tuple_length_error():
    class Model(BaseModel):
        v: Tuple[int, float, bool]
        w: Tuple[()]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2], w=[1])
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'wrong tuple length 2, expected 3',
            'type': 'value_error.tuple.length',
            'ctx': {'actual_length': 2, 'expected_length': 3},
        },
        {
            'loc': ('w',),
            'msg': 'wrong tuple length 1, expected 0',
            'type': 'value_error.tuple.length',
            'ctx': {'actual_length': 1, 'expected_length': 0},
        },
    ]


def test_tuple_invalid():
    class Model(BaseModel):
        v: Tuple[int, float, bool]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='xxx')
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid tuple', 'type': 'type_error.tuple'}]


def test_tuple_value_error():
    class Model(BaseModel):
        v: Tuple[int, float, Decimal]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=['x', 'y', 'x'])
    assert exc_info.value.errors() == [
        {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 1), 'msg': 'value is not a valid float', 'type': 'type_error.float'},
        {'loc': ('v', 2), 'msg': 'value is not a valid decimal', 'type': 'type_error.decimal'},
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
    assert m.dict() == {'v': [{'count': 4, 'name': 'testing'}]}

    with pytest.raises(ValidationError) as exc_info:
        Model(v=['x'])
    assert exc_info.value.errors() == [{'loc': ('v', 0), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}]


def test_recursive_list_error():
    class SubModel(BaseModel):
        name: str = ...
        count: int = None

    class Model(BaseModel):
        v: List[SubModel] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[{}])
    assert exc_info.value.errors() == [
        {'loc': ('v', 0, 'name'), 'msg': 'field required', 'type': 'value_error.missing'}
    ]


def test_list_unions():
    class Model(BaseModel):
        v: List[Union[int, str]] = ...

    assert Model(v=[123, '456', 'foobar']).v == [123, 456, 'foobar']

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, None])

    assert exc_info.value.errors() == [
        {'loc': ('v', 2), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'}
    ]


def test_recursive_lists():
    class Model(BaseModel):
        v: List[List[Union[int, float]]] = ...

    assert Model(v=[[1, 2], [3, '4', '4.1']]).v == [[1, 2], [3, 4, 4.1]]
    assert Model.__fields__['v'].sub_fields[0].name == '_v'
    assert len(Model.__fields__['v'].sub_fields) == 1
    assert Model.__fields__['v'].sub_fields[0].sub_fields[0].name == '__v'
    assert len(Model.__fields__['v'].sub_fields[0].sub_fields) == 1
    assert Model.__fields__['v'].sub_fields[0].sub_fields[0].sub_fields[1].name == '__v_float'
    assert len(Model.__fields__['v'].sub_fields[0].sub_fields[0].sub_fields) == 2


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

    assert Model(v={1: 'foobar'}).dict() == {'v': {1: 'foobar'}}
    assert Model(v={123: 456}).dict() == {'v': {123: 456}}
    assert Model(v={2: [1, 2, 3]}).dict() == {'v': {2: [1, 2, 3]}}


def test_success_values_include():
    class Model(BaseModel):
        a: int = 1
        b: int = 2
        c: int = 3

    m = Model()
    assert m.dict() == {'a': 1, 'b': 2, 'c': 3}
    assert m.dict(include={'a'}) == {'a': 1}
    assert m.dict(exclude={'a'}) == {'b': 2, 'c': 3}
    assert m.dict(include={'a', 'b'}, exclude={'a'}) == {'b': 2}


def test_include_exclude_unset():
    class Model(BaseModel):
        a: int
        b: int
        c: int = 3
        d: int = 4
        e: int = 5
        f: int = 6

    m = Model(a=1, b=2, e=5, f=7)
    assert m.dict() == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 7}
    assert m.__fields_set__ == {'a', 'b', 'e', 'f'}
    assert m.dict(exclude_unset=True) == {'a': 1, 'b': 2, 'e': 5, 'f': 7}

    assert m.dict(include={'a'}, exclude_unset=True) == {'a': 1}
    assert m.dict(include={'c'}, exclude_unset=True) == {}

    assert m.dict(exclude={'a'}, exclude_unset=True) == {'b': 2, 'e': 5, 'f': 7}
    assert m.dict(exclude={'c'}, exclude_unset=True) == {'a': 1, 'b': 2, 'e': 5, 'f': 7}

    assert m.dict(include={'a', 'b', 'c'}, exclude={'b'}, exclude_unset=True) == {'a': 1}
    assert m.dict(include={'a', 'b', 'c'}, exclude={'a', 'c'}, exclude_unset=True) == {'b': 2}


def test_include_exclude_defaults():
    class Model(BaseModel):
        a: int
        b: int
        c: int = 3
        d: int = 4
        e: int = 5
        f: int = 6

    m = Model(a=1, b=2, e=5, f=7)
    assert m.dict() == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 7}
    assert m.__fields_set__ == {'a', 'b', 'e', 'f'}
    assert m.dict(exclude_defaults=True) == {'a': 1, 'b': 2, 'f': 7}

    assert m.dict(include={'a'}, exclude_defaults=True) == {'a': 1}
    assert m.dict(include={'c'}, exclude_defaults=True) == {}

    assert m.dict(exclude={'a'}, exclude_defaults=True) == {'b': 2, 'f': 7}
    assert m.dict(exclude={'c'}, exclude_defaults=True) == {'a': 1, 'b': 2, 'f': 7}

    assert m.dict(include={'a', 'b', 'c'}, exclude={'b'}, exclude_defaults=True) == {'a': 1}
    assert m.dict(include={'a', 'b', 'c'}, exclude={'a', 'c'}, exclude_defaults=True) == {'b': 2}

    # abstract set
    assert m.dict(include={'a': 1}.keys()) == {'a': 1}
    assert m.dict(exclude={'a': 1}.keys()) == {'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 7}

    assert m.dict(include={'a': 1}.keys(), exclude_unset=True) == {'a': 1}
    assert m.dict(exclude={'a': 1}.keys(), exclude_unset=True) == {'b': 2, 'e': 5, 'f': 7}


def test_skip_defaults_deprecated():
    class Model(BaseModel):
        x: int
        b: int = 2

    m = Model(x=1)
    match = r'Model.dict\(\): "skip_defaults" is deprecated and replaced by "exclude_unset"'
    with pytest.warns(DeprecationWarning, match=match):
        assert m.dict(skip_defaults=True) == m.dict(exclude_unset=True)
    with pytest.warns(DeprecationWarning, match=match):
        assert m.dict(skip_defaults=False) == m.dict(exclude_unset=False)

    match = r'Model.json\(\): "skip_defaults" is deprecated and replaced by "exclude_unset"'
    with pytest.warns(DeprecationWarning, match=match):
        assert m.json(skip_defaults=True) == m.json(exclude_unset=True)
    with pytest.warns(DeprecationWarning, match=match):
        assert m.json(skip_defaults=False) == m.json(exclude_unset=False)


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

    assert m.dict(exclude={'f': {'c': ..., 'd': {-1: {'a'}}}}) == {
        'e': 'e',
        'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]},
    }
    assert m.dict(exclude={'e': ..., 'f': {'d'}}) == {'f': {'c': 'foo'}}


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
    assert m.dict(exclude=excludes, by_alias=True) == {
        'e_alias': 'e',
        'f_alias': {'d_alias': [{'a': 'a', 'b_alias': 'b'}, {'b_alias': 'e'}]},
    }

    excludes = {'aliased_e': ..., 'aliased_f': {'aliased_d'}}
    assert m.dict(exclude=excludes, by_alias=True) == {'f_alias': {'c_alias': 'foo'}}


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

    assert m.dict(include={'f'}) == {'f': {'c': 'foo', 'd': [{'a': 'a', 'b': 'b'}, {'a': 'c', 'b': 'e'}]}}
    assert m.dict(include={'e'}) == {'e': 'e'}
    assert m.dict(include={'f': {'d': {0: ..., -1: {'b'}}}}) == {'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}}


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

    assert m.dict(exclude={'f': {'c': ..., 'd': {-1: {'a'}}}}, include={'f'}) == {
        'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}
    }
    assert m.dict(exclude={'e': ..., 'f': {'d'}}, include={'e', 'f'}) == {'f': {'c': 'foo'}}

    assert m.dict(exclude={'f': {'d': {-1: {'a'}}}}, include={'f': {'d'}}) == {
        'f': {'d': [{'a': 'a', 'b': 'b'}, {'b': 'e'}]}
    }


@pytest.mark.parametrize(
    'exclude,expected',
    [
        # Normal nested __all__
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'j': 1}, {'j': 2}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
        ),
        # Merge sub dicts
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': ...}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1}, {'i': 2}]}, {'k': 2}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: {'subsubs': ...}}},
            {'subs': [{'k': 1}, {'k': 2, 'subsubs': [{'i': 3}]}]},
        ),
        # Merge sub sets
        (
            {'subs': {'__all__': {'subsubs': {0}}, 0: {'subsubs': {1}}}},
            {'subs': [{'k': 1, 'subsubs': []}, {'k': 2, 'subsubs': []}]},
        ),
        # Merge sub dict-set
        (
            {'subs': {'__all__': {'subsubs': {0: {'i'}}}, 0: {'subsubs': {1}}}},
            {'subs': [{'k': 1, 'subsubs': [{'j': 1}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
        ),
        # Different keys
        ({'subs': {'__all__': {'subsubs'}, 0: {'k'}}}, {'subs': [{}, {'k': 2}]}),
        ({'subs': {'__all__': {'subsubs': ...}, 0: {'k'}}}, {'subs': [{}, {'k': 2}]}),
        ({'subs': {'__all__': {'subsubs'}, 0: {'k': ...}}}, {'subs': [{}, {'k': 2}]}),
        # Nested different keys
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i': ...}, 0: {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j': ...}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
        ),
        # Ignore __all__ for index with defined exclude
        (
            {'subs': {'__all__': {'subsubs'}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1}, {'i': 2}]}, {'k': 2}]},
        ),
        ({'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: ...}}, {'subs': [{'k': 2, 'subsubs': [{'i': 3}]}]}),
        ({'subs': {'__all__': ..., 0: {'subsubs'}}}, {'subs': [{'k': 1}]}),
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

    assert m.dict(exclude=exclude) == expected


@pytest.mark.parametrize(
    'include,expected',
    [
        # Normal nested __all__
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}}},
            {'subs': [{'subsubs': [{'i': 1}, {'i': 2}]}, {'subsubs': [{'i': 3}]}]},
        ),
        # Merge sub dicts
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': ...}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'subsubs': [{'j': 1}, {'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: {'subsubs': ...}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'j': 3}]}]},
        ),
        # Merge sub sets
        (
            {'subs': {'__all__': {'subsubs': {0}}, 0: {'subsubs': {1}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        # Merge sub dict-set
        (
            {'subs': {'__all__': {'subsubs': {0: {'i'}}}, 0: {'subsubs': {1}}}},
            {'subs': [{'subsubs': [{'i': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3}]}]},
        ),
        # Different keys
        (
            {'subs': {'__all__': {'subsubs'}, 0: {'k'}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': ...}, 0: {'k'}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs'}, 0: {'k': ...}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        # Nested different keys
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j'}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i': ...}, 0: {'j'}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j': ...}}}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        # Ignore __all__ for index with defined include
        (
            {'subs': {'__all__': {'subsubs'}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'subsubs': [{'j': 1}, {'j': 2}]}, {'subsubs': [{'i': 3, 'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: ...}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'subsubs': [{'j': 3}]}]},
        ),
        (
            {'subs': {'__all__': ..., 0: {'subsubs'}}},
            {'subs': [{'subsubs': [{'i': 1, 'j': 1}, {'i': 2, 'j': 2}]}, {'k': 2, 'subsubs': [{'i': 3, 'j': 3}]}]},
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

    assert m.dict(include=include) == expected


def test_field_set_ignore_extra():
    class Model(BaseModel):
        a: int
        b: int
        c: int = 3

        class Config:
            extra = Extra.ignore

    m = Model(a=1, b=2)
    assert m.dict() == {'a': 1, 'b': 2, 'c': 3}
    assert m.__fields_set__ == {'a', 'b'}
    assert m.dict(exclude_unset=True) == {'a': 1, 'b': 2}

    m2 = Model(a=1, b=2, d=4)
    assert m2.dict() == {'a': 1, 'b': 2, 'c': 3}
    assert m2.__fields_set__ == {'a', 'b'}
    assert m2.dict(exclude_unset=True) == {'a': 1, 'b': 2}


def test_field_set_allow_extra():
    class Model(BaseModel):
        a: int
        b: int
        c: int = 3

        class Config:
            extra = Extra.allow

    m = Model(a=1, b=2)
    assert m.dict() == {'a': 1, 'b': 2, 'c': 3}
    assert m.__fields_set__ == {'a', 'b'}
    assert m.dict(exclude_unset=True) == {'a': 1, 'b': 2}

    m2 = Model(a=1, b=2, d=4)
    assert m2.dict() == {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    assert m2.__fields_set__ == {'a', 'b', 'd'}
    assert m2.dict(exclude_unset=True) == {'a': 1, 'b': 2, 'd': 4}


def test_field_set_field_name():
    class Model(BaseModel):
        a: int
        field_set: int
        b: int = 3

    assert Model(a=1, field_set=2).dict() == {'a': 1, 'field_set': 2, 'b': 3}
    assert Model(a=1, field_set=2).dict(exclude_unset=True) == {'a': 1, 'field_set': 2}
    assert Model.construct(a=1, field_set=3).dict() == {'a': 1, 'field_set': 3, 'b': 3}


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

    class Bar(Foo):
        x: float = 12.3
        a = 123.0

    assert Bar().dict() == {'x': 12.3, 'a': 123.0}


def test_inheritance_subclass_default():
    class MyStr(str):
        pass

    # Confirm hint supports a subclass default
    class Simple(BaseModel):
        x: str = MyStr('test')

    # Confirm hint on a base can be overridden with a subclass default on a subclass
    class Base(BaseModel):
        x: str
        y: str

    class Sub(Base):
        x = MyStr('test')
        y: MyStr = MyStr('test')  # force subtype

    assert Sub.__fields__['x'].type_ == str
    assert Sub.__fields__['y'].type_ == MyStr


def test_invalid_type():
    with pytest.raises(RuntimeError) as exc_info:

        class Model(BaseModel):
            x: 43 = 123

    assert 'error checking inheritance of 43 (type: int)' in exc_info.value.args[0]


class CustomStr(str):
    def foobar(self):
        return 7


@pytest.mark.parametrize(
    'value,expected',
    [
        ('a string', 'a string'),
        (b'some bytes', 'some bytes'),
        (bytearray('foobar', encoding='utf8'), 'foobar'),
        (123, '123'),
        (123.45, '123.45'),
        (Decimal('12.45'), '12.45'),
        (True, 'True'),
        (False, 'False'),
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
        ({'foo': 'bar'}, [{'loc': ('v',), 'msg': 'str type expected', 'type': 'type_error.str'}]),
        ([1, 2, 3], [{'loc': ('v',), 'msg': 'str type expected', 'type': 'type_error.str'}]),
    ],
)
def test_invalid_string_types(value, errors):
    class Model(BaseModel):
        v: str

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


def test_inheritance_config():
    class Parent(BaseModel):
        a: int

    class Child(Parent):
        b: str

        class Config:
            fields = {'a': 'aaa', 'b': 'bbb'}

    m = Child(aaa=1, bbb='s')
    assert repr(m) == "Child(a=1, b='s')"


def test_partial_inheritance_config():
    class Parent(BaseModel):
        a: int

        class Config:
            fields = {'a': 'aaa'}

    class Child(Parent):
        b: str

        class Config:
            fields = {'b': 'bbb'}

    m = Child(aaa=1, bbb='s')
    assert repr(m) == "Child(a=1, b='s')"


def test_annotation_inheritance():
    class A(BaseModel):
        integer: int = 1

    class B(A):
        integer = 2

    if sys.version_info < (3, 10):
        assert B.__annotations__['integer'] == int
    else:
        assert B.__annotations__ == {}
    assert B.__fields__['integer'].type_ == int

    class C(A):
        integer: str = 'G'

    assert C.__annotations__['integer'] == str
    assert C.__fields__['integer'].type_ == str

    with pytest.raises(TypeError) as exc_info:

        class D(A):
            integer = 'G'

    assert str(exc_info.value) == (
        'The type of D.integer differs from the new default value; '
        'if you wish to change the type of this field, please use a type annotation'
    )


def test_string_none():
    class Model(BaseModel):
        a: constr(min_length=20, max_length=1000) = ...

        class Config:
            extra = Extra.ignore

    with pytest.raises(ValidationError) as exc_info:
        Model(a=None)
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'}
    ]


def test_return_errors_ok():
    class Model(BaseModel):
        foo: int
        bar: List[int]

    assert validate_model(Model, {'foo': '123', 'bar': (1, 2, 3)}) == (
        {'foo': 123, 'bar': [1, 2, 3]},
        {'foo', 'bar'},
        None,
    )
    d, f, e = validate_model(Model, {'foo': '123', 'bar': (1, 2, 3)}, False)
    assert d == {'foo': 123, 'bar': [1, 2, 3]}
    assert f == {'foo', 'bar'}
    assert e is None


def test_return_errors_error():
    class Model(BaseModel):
        foo: int
        bar: List[int]

    d, f, e = validate_model(Model, {'foo': '123', 'bar': (1, 2, 'x')}, False)
    assert d == {'foo': 123}
    assert f == {'foo', 'bar'}
    assert e.errors() == [{'loc': ('bar', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]

    d, f, e = validate_model(Model, {'bar': (1, 2, 3)}, False)
    assert d == {'bar': [1, 2, 3]}
    assert f == {'bar'}
    assert e.errors() == [{'loc': ('foo',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_optional_required():
    class Model(BaseModel):
        bar: Optional[int]

    assert Model(bar=123).dict() == {'bar': 123}
    assert Model().dict() == {'bar': None}
    assert Model(bar=None).dict() == {'bar': None}


def test_invalid_validator():
    class InvalidValidator:
        @classmethod
        def __get_validators__(cls):
            yield cls.has_wrong_arguments

        @classmethod
        def has_wrong_arguments(cls, value, bar):
            pass

    with pytest.raises(errors.ConfigError) as exc_info:

        class InvalidValidatorModel(BaseModel):
            x: InvalidValidator = ...

    assert exc_info.value.args[0].startswith('Invalid signature for validator')


def test_unable_to_infer():
    with pytest.raises(errors.ConfigError) as exc_info:

        class InvalidDefinitionModel(BaseModel):
            x = None

    assert exc_info.value.args[0] == 'unable to infer type for attribute "x"'


def test_multiple_errors():
    class Model(BaseModel):
        a: Union[None, int, float, Decimal]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foobar')

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('a',), 'msg': 'value is not a valid float', 'type': 'type_error.float'},
        {'loc': ('a',), 'msg': 'value is not a valid decimal', 'type': 'type_error.decimal'},
    ]
    assert Model().a is None
    assert Model(a=None).a is None


def test_validate_all():
    class Model(BaseModel):
        a: int
        b: int

        class Config:
            validate_all = True

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('b',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_force_extra():
    class Model(BaseModel):
        foo: int

        class Config:
            extra = 'ignore'

    assert Model.__config__.extra is Extra.ignore


def test_illegal_extra_value():
    with pytest.raises(ValueError, match='is not a valid value for "extra"'):

        class Model(BaseModel):
            foo: int

            class Config:
                extra = 'foo'


def test_multiple_inheritance_config():
    class Parent(BaseModel):
        class Config:
            allow_mutation = False
            extra = Extra.forbid

    class Mixin(BaseModel):
        class Config:
            use_enum_values = True

    class Child(Mixin, Parent):
        class Config:
            allow_population_by_field_name = True

    assert BaseModel.__config__.allow_mutation is True
    assert BaseModel.__config__.allow_population_by_field_name is False
    assert BaseModel.__config__.extra is Extra.ignore
    assert BaseModel.__config__.use_enum_values is False

    assert Parent.__config__.allow_mutation is False
    assert Parent.__config__.allow_population_by_field_name is False
    assert Parent.__config__.extra is Extra.forbid
    assert Parent.__config__.use_enum_values is False

    assert Mixin.__config__.allow_mutation is True
    assert Mixin.__config__.allow_population_by_field_name is False
    assert Mixin.__config__.extra is Extra.ignore
    assert Mixin.__config__.use_enum_values is True

    assert Child.__config__.allow_mutation is False
    assert Child.__config__.allow_population_by_field_name is True
    assert Child.__config__.extra is Extra.forbid
    assert Child.__config__.use_enum_values is True


def test_submodel_different_type():
    class Foo(BaseModel):
        a: int

    class Bar(BaseModel):
        b: int

    class Spam(BaseModel):
        c: Foo

    assert Spam(c={'a': '123'}).dict() == {'c': {'a': 123}}
    with pytest.raises(ValidationError):
        Spam(c={'b': '123'})

    assert Spam(c=Foo(a='123')).dict() == {'c': {'a': 123}}
    with pytest.raises(ValidationError):
        Spam(c=Bar(b='123'))


def test_self():
    class Model(BaseModel):
        self: str

    m = Model.parse_obj(dict(self='some value'))
    assert m.dict() == {'self': 'some value'}
    assert m.self == 'some value'
    assert m.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {'self': {'title': 'Self', 'type': 'string'}},
        'required': ['self'],
    }


@pytest.mark.parametrize('model', [BaseModel, BaseSettings])
def test_self_recursive(model):
    class SubModel(model):
        self: int

    class Model(model):
        sm: SubModel

    m = Model.parse_obj({'sm': {'self': '123'}})
    assert m.dict() == {'sm': {'self': 123}}


@pytest.mark.parametrize('model', [BaseModel, BaseSettings])
def test_nested_init(model):
    class NestedModel(model):
        self: str
        modified_number: int = 1

        def __init__(someinit, **kwargs):
            super().__init__(**kwargs)
            someinit.modified_number += 1

    class TopModel(model):
        self: str
        nest: NestedModel

    m = TopModel.parse_obj(dict(self='Top Model', nest=dict(self='Nested Model', modified_number=0)))
    assert m.self == 'Top Model'
    assert m.nest.self == 'Nested Model'
    assert m.nest.modified_number == 1


def test_init_inspection():
    class Foobar(BaseModel):
        x: int

        def __init__(self, **data) -> None:
            with pytest.raises(AttributeError):
                assert self.x
            super().__init__(**data)

    Foobar(x=1)


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

    assert Model.__fields__.keys() == {'b', 'c', 'e', 'f', 'g', 'h', 'i'}


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
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'subclass of Parent expected',
            'type': 'type_error.subclass',
            'ctx': {'expected_class': 'Parent'},
        }
    ]


def test_optional_subfields():
    class Model(BaseModel):
        a: Optional[int]

    assert Model.__fields__['a'].sub_fields is None
    assert Model.__fields__['a'].allow_none is True

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foobar')

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert Model().a is None
    assert Model(a=None).a is None
    assert Model(a=12).a == 12


def test_not_optional_subfields():
    class Model(BaseModel):
        a: Optional[int]

        @validator('a')
        def check_a(cls, v):
            return v

    assert Model.__fields__['a'].sub_fields is None
    # assert Model.__fields__['a'].required is True
    assert Model.__fields__['a'].allow_none is True

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foobar')

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]
    assert Model().a is None
    assert Model(a=None).a is None
    assert Model(a=12).a == 12


def test_optional_field_constraints():
    class MyModel(BaseModel):
        my_int: Optional[int] = Field(..., ge=3)

    with pytest.raises(ValidationError) as exc_info:
        MyModel(my_int=2)
    assert exc_info.value.errors() == [
        {
            'loc': ('my_int',),
            'msg': 'ensure this value is greater than or equal to 3',
            'type': 'value_error.number.not_ge',
            'ctx': {'limit_value': 3},
        }
    ]


def test_field_str_shape():
    class Model(BaseModel):
        a: List[int]

    assert repr(Model.__fields__['a']) == "ModelField(name='a', type=List[int], required=True)"
    assert str(Model.__fields__['a']) == "name='a' type=List[int] required=True"


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
        (Optional[int], 'Optional[int]'),
        (Union[None, int, str], 'Union[NoneType, int, str]'),
        (Union[int, str, bytes], 'Union[int, str, bytes]'),
        (List[int], 'List[int]'),
        (Tuple[int, str, bytes], 'Tuple[int, str, bytes]'),
        (Union[List[int], Set[bytes]], 'Union[List[int], Set[bytes]]'),
        (List[Tuple[int, int]], 'List[Tuple[int, int]]'),
        (Dict[int, str], 'Mapping[int, str]'),
        (FrozenSet[int], 'FrozenSet[int]'),
        (Tuple[int, ...], 'Tuple[int, ...]'),
        (Optional[List[int]], 'Optional[List[int]]'),
        (dict, 'dict'),
        (DisplayGen[bool, str], 'DisplayGen[bool, str]'),
    ],
)
def test_field_type_display(type_, expected):
    class Model(BaseModel):
        a: type_

    assert Model.__fields__['a']._type_display() == expected


def test_any_none():
    class MyModel(BaseModel):
        foo: Any

    m = MyModel(foo=None)
    assert dict(m) == {'foo': None}


def test_type_var_any():
    Foobar = TypeVar('Foobar')

    class MyModel(BaseModel):
        foo: Foobar

    assert MyModel.schema() == {'title': 'MyModel', 'type': 'object', 'properties': {'foo': {'title': 'Foo'}}}
    assert MyModel(foo=None).foo is None
    assert MyModel(foo='x').foo == 'x'
    assert MyModel(foo=123).foo == 123


def test_type_var_constraint():
    Foobar = TypeVar('Foobar', int, str)

    class MyModel(BaseModel):
        foo: Foobar

    assert MyModel.schema() == {
        'title': 'MyModel',
        'type': 'object',
        'properties': {'foo': {'title': 'Foo', 'anyOf': [{'type': 'integer'}, {'type': 'string'}]}},
        'required': ['foo'],
    }
    with pytest.raises(ValidationError, match='none is not an allowed value'):
        MyModel(foo=None)
    with pytest.raises(ValidationError, match='value is not a valid integer'):
        MyModel(foo=[1, 2, 3])
    assert MyModel(foo='x').foo == 'x'
    assert MyModel(foo=123).foo == 123


def test_type_var_bound():
    Foobar = TypeVar('Foobar', bound=int)

    class MyModel(BaseModel):
        foo: Foobar

    assert MyModel.schema() == {
        'title': 'MyModel',
        'type': 'object',
        'properties': {'foo': {'title': 'Foo', 'type': 'integer'}},
        'required': ['foo'],
    }
    with pytest.raises(ValidationError, match='none is not an allowed value'):
        MyModel(foo=None)
    with pytest.raises(ValidationError, match='value is not a valid integer'):
        MyModel(foo='x')
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

        @validator('foo')
        def check_something(cls, value):
            return value

    class Bar(Foo):
        pass

    assert repr(Foo.__fields__['foo']) == "ModelField(name='foo', type=List[List[int]], required=True)"
    assert repr(Bar.__fields__['foo']) == "ModelField(name='foo', type=List[List[int]], required=True)"
    assert Foo(foo=[[0, 1]]).foo == [[0, 1]]
    assert Bar(foo=[[0, 1]]).foo == [[0, 1]]


def test_exclude_none():
    class MyModel(BaseModel):
        a: Optional[int] = None
        b: int = 2

    m = MyModel(a=5)
    assert m.dict(exclude_none=True) == {'a': 5, 'b': 2}

    m = MyModel(b=3)
    assert m.dict(exclude_none=True) == {'b': 3}
    assert m.json(exclude_none=True) == '{"b": 3}'


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
    assert m.dict() == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}, 'f': None}
    assert m.dict(exclude_none=True) == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}}
    assert dict(m) == {'c': 5, 'd': 2, 'e': {'a': 0, 'b': 1}, 'f': None}

    m = ModelB(c=5, e={'b': 20}, f='test')
    assert m.dict() == {'c': 5, 'd': 2, 'e': {'a': None, 'b': 20}, 'f': 'test'}
    assert m.dict(exclude_none=True) == {'c': 5, 'd': 2, 'e': {'b': 20}, 'f': 'test'}
    assert dict(m) == {'c': 5, 'd': 2, 'e': {'a': None, 'b': 20}, 'f': 'test'}


def test_exclude_none_with_extra():
    class MyModel(BaseModel):
        a: str = 'default'
        b: Optional[str] = None

        class Config:
            extra = 'allow'

    m = MyModel(a='a', c='c')

    assert m.dict(exclude_none=True) == {'a': 'a', 'c': 'c'}
    assert m.dict() == {'a': 'a', 'b': None, 'c': 'c'}

    m = MyModel(a='a', b='b', c=None)

    assert m.dict(exclude_none=True) == {'a': 'a', 'b': 'b'}
    assert m.dict() == {'a': 'a', 'b': 'b', 'c': None}


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

        @validator('something')
        def check_something(cls, v):
            val_calls.append(v)
            return v

    assert Model().dict() == {'something': None}
    assert Model(something=None).dict() == {'something': None}
    assert Model(something='hello').dict() == {'something': 'hello'}
    assert val_calls == [None, 'hello']


def test_required_optional():
    class Model(BaseModel):
        nullable1: Optional[int] = ...
        nullable2: Optional[int] = Field(...)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors() == [
        {'loc': ('nullable1',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('nullable2',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable1=1)
    assert exc_info.value.errors() == [{'loc': ('nullable2',), 'msg': 'field required', 'type': 'value_error.missing'}]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable2=2)
    assert exc_info.value.errors() == [{'loc': ('nullable1',), 'msg': 'field required', 'type': 'value_error.missing'}]
    assert Model(nullable1=None, nullable2=None).dict() == {'nullable1': None, 'nullable2': None}
    assert Model(nullable1=1, nullable2=2).dict() == {'nullable1': 1, 'nullable2': 2}
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable1='some text')
    assert exc_info.value.errors() == [
        {'loc': ('nullable1',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('nullable2',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_required_any():
    class Model(BaseModel):
        optional1: Any
        optional2: Any = None
        nullable1: Any = ...
        nullable2: Any = Field(...)

    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors() == [
        {'loc': ('nullable1',), 'msg': 'field required', 'type': 'value_error.missing'},
        {'loc': ('nullable2',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable1='a')
    assert exc_info.value.errors() == [{'loc': ('nullable2',), 'msg': 'field required', 'type': 'value_error.missing'}]
    with pytest.raises(ValidationError) as exc_info:
        Model(nullable2=False)
    assert exc_info.value.errors() == [{'loc': ('nullable1',), 'msg': 'field required', 'type': 'value_error.missing'}]
    assert Model(nullable1=None, nullable2=None).dict() == {
        'optional1': None,
        'optional2': None,
        'nullable1': None,
        'nullable2': None,
    }
    assert Model(nullable1=1, nullable2='two').dict() == {
        'optional1': None,
        'optional2': None,
        'nullable1': 1,
        'nullable2': 'two',
    }
    assert Model(optional1='op1', optional2=False, nullable1=1, nullable2='two').dict() == {
        'optional1': 'op1',
        'optional2': False,
        'nullable1': 1,
        'nullable2': 'two',
    }


def test_custom_generic_validators():
    T1 = TypeVar('T1')
    T2 = TypeVar('T2')

    class MyGen(Generic[T1, T2]):
        def __init__(self, t1: T1, t2: T2):
            self.t1 = t1
            self.t2 = t2

        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v, field):
            if not isinstance(v, cls):
                raise TypeError('Invalid value')
            if not field.sub_fields:
                return v
            t1_f = field.sub_fields[0]
            t2_f = field.sub_fields[1]
            errors = []
            _, error = t1_f.validate(v.t1, {}, loc='t1')
            if error:
                errors.append(error)
            _, error = t2_f.validate(v.t2, {}, loc='t2')
            if error:
                errors.append(error)
            if errors:
                raise ValidationError(errors, cls)
            return v

    class Model(BaseModel):
        a: str
        gen: MyGen[str, bool]
        gen2: MyGen

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', gen='invalid', gen2='invalid')
    assert exc_info.value.errors() == [
        {'loc': ('gen',), 'msg': 'Invalid value', 'type': 'type_error'},
        {'loc': ('gen2',), 'msg': 'Invalid value', 'type': 'type_error'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', gen=MyGen(t1='bar', t2='baz'), gen2=MyGen(t1='bar', t2='baz'))
    assert exc_info.value.errors() == [
        {'loc': ('gen', 't2'), 'msg': 'value could not be parsed to a boolean', 'type': 'type_error.bool'}
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

        class Config:
            arbitrary_types_allowed = True

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', gen='invalid')
    assert exc_info.value.errors() == [
        {
            'loc': ('gen',),
            'msg': 'instance of MyGen expected',
            'type': 'type_error.arbitrary_type',
            'ctx': {'expected_arbitrary_type': 'MyGen'},
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

    match = r'Fields of type(.*)are not supported.'
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
    assert exc_info.value.errors() == [
        {'loc': ('v',), 'msg': 'value is not a valid hashable', 'type': 'type_error.hashable'}
    ]
    with pytest.raises(ValidationError) as exc_info:
        Model()
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'field required', 'type': 'value_error.missing'}]


@pytest.mark.parametrize('default', [1, None])
def test_hashable_optional(default):
    class Model(BaseModel):
        v: Hashable = default

    Model(v=None)
    Model()


def test_default_factory_called_once():
    """It should never call `default_factory` more than once even when `validate_all` is set"""

    v = 0

    def factory() -> int:
        nonlocal v
        v += 1
        return v

    class MyModel(BaseModel):
        id: int = Field(default_factory=factory)

        class Config:
            validate_all = True

    m1 = MyModel()
    assert m1.id == 1

    class MyBadModel(BaseModel):
        id: List[str] = Field(default_factory=factory)

        class Config:
            validate_all = True

    with pytest.raises(ValidationError) as exc_info:
        MyBadModel()
    assert v == 2  # `factory` has been called to run validation
    assert exc_info.value.errors() == [
        {'loc': ('id',), 'msg': 'value is not a valid list', 'type': 'type_error.list'},
    ]


def test_default_factory_validator_child():
    class Parent(BaseModel):
        foo: List[str] = Field(default_factory=list)

        @validator('foo', pre=True, each_item=True)
        def mutate_foo(cls, v):
            return f'{v}-1'

    assert Parent(foo=['a', 'b']).foo == ['a-1', 'b-1']

    class Child(Parent):
        pass

    assert Child(foo=['a', 'b']).foo == ['a-1', 'b-1']


@pytest.mark.skipif(cython is None, reason='cython not installed')
def test_cython_function_untouched():
    Model = cython.inline(
        # language=Python
        """
from pydantic import BaseModel

class Model(BaseModel):
    a = 0.0
    b = 10

    def get_double_a(self) -> float:
        return self.a + self.b

return Model
"""
    )
    model = Model(a=10.2)
    assert model.a == 10.2
    assert model.b == 10
    assert model.get_double_a() == 20.2


def test_resolve_annotations_module_missing(tmp_path):
    # see https://github.com/pydantic/pydantic/issues/2363
    file_path = tmp_path / 'module_to_load.py'
    # language=Python
    file_path.write_text(
        """
from pydantic import BaseModel
class User(BaseModel):
    id: int
    name = 'Jane Doe'
"""
    )

    spec = importlib.util.spec_from_file_location('my_test_module', file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.User(id=12).dict() == {'id': 12, 'name': 'Jane Doe'}


def test_iter_coverage():
    class MyModel(BaseModel):
        x: int = 1
        y: str = 'a'

    assert list(MyModel()._iter(by_alias=True)) == [('x', 1), ('y', 'a')]


def test_config_field_info():
    class Foo(BaseModel):
        a: str = Field(...)

        class Config:
            fields = {'a': {'description': 'descr'}}

    assert Foo.schema(by_alias=True)['properties'] == {'a': {'title': 'A', 'description': 'descr', 'type': 'string'}}


def test_config_field_info_alias():
    class Foo(BaseModel):
        a: str = Field(...)

        class Config:
            fields = {'a': {'alias': 'b'}}

    assert Foo.schema(by_alias=True)['properties'] == {'b': {'title': 'B', 'type': 'string'}}


def test_config_field_info_merge():
    class Foo(BaseModel):
        a: str = Field(..., foo='Foo')

        class Config:
            fields = {'a': {'bar': 'Bar'}}

    assert Foo.schema(by_alias=True)['properties'] == {
        'a': {'bar': 'Bar', 'foo': 'Foo', 'title': 'A', 'type': 'string'}
    }


def test_config_field_info_allow_mutation():
    class Foo(BaseModel):
        a: str = Field(...)

        class Config:
            validate_assignment = True

    assert Foo.__fields__['a'].field_info.allow_mutation is True

    f = Foo(a='x')
    f.a = 'y'
    assert f.dict() == {'a': 'y'}

    class Bar(BaseModel):
        a: str = Field(...)

        class Config:
            fields = {'a': {'allow_mutation': False}}
            validate_assignment = True

    assert Bar.__fields__['a'].field_info.allow_mutation is False

    b = Bar(a='x')
    with pytest.raises(TypeError):
        b.a = 'y'
    assert b.dict() == {'a': 'x'}


def test_arbitrary_types_allowed_custom_eq():
    class Foo:
        def __eq__(self, other):
            if other.__class__ is not Foo:
                raise TypeError(f'Cannot interpret {other.__class__.__name__!r} as a valid type')
            return True

    class Model(BaseModel):
        x: Foo = Foo()

        class Config:
            arbitrary_types_allowed = True

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
    assert m.my_int.__class__ == IntSubclass


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
    assert Model(x=b'1' * 4_300).x == int('1' * 4_300)
    assert Model(x=bytearray(b'1' * 4_300)).x == int('1' * 4_300)

    too_long = '1' * 4_301
    with pytest.raises(ValidationError) as exc_info:
        Model(x=too_long)

    assert exc_info.value.errors() == [
        {
            'loc': ('x',),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
    ]

    too_long_b = too_long.encode('utf-8')
    with pytest.raises(ValidationError):
        Model(x=too_long_b)
    with pytest.raises(ValidationError):
        Model(x=bytearray(too_long_b))

    # this used to hang indefinitely
    with pytest.raises(ValidationError):
        Model(x='1' * (10**7))
