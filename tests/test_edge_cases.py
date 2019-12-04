import re
import sys
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union

import pytest

from pydantic import (
    BaseConfig,
    BaseModel,
    BaseSettings,
    Extra,
    NoneStrBytes,
    StrBytes,
    ValidationError,
    constr,
    errors,
    validate_model,
    validator,
)
from pydantic.fields import Field, Schema


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
        simple_tuple: tuple = None
        tuple_of_different_types: Tuple[int, float, str, bool] = None

    m = Model(simple_tuple=[1, 2, 3, 4], tuple_of_different_types=[4, 3, 2, 1])
    assert m.dict() == {'simple_tuple': (1, 2, 3, 4), 'tuple_of_different_types': (4, 3.0, '2', True)}


def test_tuple_length_error():
    class Model(BaseModel):
        v: Tuple[int, float, bool]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2])
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'wrong tuple length 2, expected 3',
            'type': 'value_error.tuple.length',
            'ctx': {'actual_length': 2, 'expected_length': 3},
        }
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


def test_infer_alias():
    class Model(BaseModel):
        a = 'foobar'

        class Config:
            fields = {'a': '_a'}

    assert Model(_a='different').a == 'different'
    assert repr(Model.__fields__['a']) == (
        "ModelField(name='a', type=str, required=False, default='foobar', alias='_a')"
    )


def test_alias_error():
    class Model(BaseModel):
        a = 123

        class Config:
            fields = {'a': '_a'}

    assert Model(_a='123').a == 123

    with pytest.raises(ValidationError) as exc_info:
        Model(_a='foo')
    assert exc_info.value.errors() == [
        {'loc': ('_a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_annotation_config():
    class Model(BaseModel):
        b: float
        a: int = 10
        _c: str

        class Config:
            fields = {'b': 'foobar'}

    assert list(Model.__fields__.keys()) == ['b', 'a']
    assert [f.alias for f in Model.__fields__.values()] == ['foobar', 'a']
    assert Model(foobar='123').b == 123.0


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


def test_advanced_value_inclide():
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

    assert B.__annotations__['integer'] == int
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


def test_alias_camel_case():
    class Model(BaseModel):
        one_thing: int
        another_thing: int

        class Config(BaseConfig):
            @classmethod
            def get_field_info(cls, name):
                field_config = super().get_field_info(name) or {}
                if 'alias' not in field_config:
                    field_config['alias'] = re.sub(r'(?:^|_)([a-z])', lambda m: m.group(1).upper(), name)
                return field_config

    v = Model(**{'OneThing': 123, 'AnotherThing': '321'})
    assert v.one_thing == 123
    assert v.another_thing == 321
    assert v == {'one_thing': 123, 'another_thing': 321}


def test_get_field_info_inherit():
    class ModelOne(BaseModel):
        class Config(BaseConfig):
            @classmethod
            def get_field_info(cls, name):
                field_config = super().get_field_info(name) or {}
                if 'alias' not in field_config:
                    field_config['alias'] = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)
                return field_config

    class ModelTwo(ModelOne):
        one_thing: int
        another_thing: int
        third_thing: int

        class Config:
            fields = {'third_thing': 'Banana'}

    v = ModelTwo(**{'oneThing': 123, 'anotherThing': '321', 'Banana': 1})
    assert v == {'one_thing': 123, 'another_thing': 321, 'third_thing': 1}


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


def test_pop_by_alias():
    class Model(BaseModel):
        last_updated_by: Optional[str] = None

        class Config:
            extra = Extra.forbid
            allow_population_by_field_name = True
            fields = {'last_updated_by': 'lastUpdatedBy'}

    assert Model(lastUpdatedBy='foo').dict() == {'last_updated_by': 'foo'}
    assert Model(last_updated_by='foo').dict() == {'last_updated_by': 'foo'}
    with pytest.raises(ValidationError) as exc_info:
        Model(lastUpdatedBy='foo', last_updated_by='bar')
    assert exc_info.value.errors() == [
        {'loc': ('last_updated_by',), 'msg': 'extra fields not permitted', 'type': 'value_error.extra'}
    ]


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


def test_values_attr_deprecation():
    class Model(BaseModel):
        foo: int
        bar: str

    m = Model(foo=4, bar='baz')
    with pytest.warns(DeprecationWarning, match='`__values__` attribute is deprecated, use `__dict__` instead'):
        assert m.__values__ == m.__dict__


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

    assert Model.__fields__.keys() == {'b', 'c', 'e', 'f'}


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


def test_scheme_deprecated():

    with pytest.warns(DeprecationWarning, match='`Schema` is deprecated, use `Field` instead'):

        class Model(BaseModel):
            foo: int = Schema(4)


def test_population_by_alias():
    with pytest.warns(DeprecationWarning, match='"allow_population_by_alias" is deprecated and replaced by'):

        class Model(BaseModel):
            a: str

            class Config:
                allow_population_by_alias = True
                fields = {'a': {'alias': '_a'}}

    assert Model.__config__.allow_population_by_field_name is True
    assert Model(a='different').a == 'different'
    assert Model(a='different').dict() == {'a': 'different'}
    assert Model(a='different').dict(by_alias=True) == {'_a': 'different'}


def test_fields_deprecated():
    class Model(BaseModel):
        v: str = 'x'

    with pytest.warns(DeprecationWarning, match='`fields` attribute is deprecated, use `__fields__` instead'):
        assert Model().fields.keys() == {'v'}

    assert Model().__fields__.keys() == {'v'}
    assert Model.__fields__.keys() == {'v'}


def test_alias_child_precedence():
    class Parent(BaseModel):
        x: int

        class Config:
            fields = {'x': 'x1'}

    class Child(Parent):
        y: int

        class Config:
            fields = {'y': 'y2', 'x': 'x2'}

    assert Child.__fields__['y'].alias == 'y2'
    assert Child.__fields__['x'].alias == 'x2'


def test_alias_generator_parent():
    class Parent(BaseModel):
        x: int

        class Config:
            allow_population_by_field_name = True

            @classmethod
            def alias_generator(cls, f_name):
                return f_name + '1'

    class Child(Parent):
        y: int

        class Config:
            @classmethod
            def alias_generator(cls, f_name):
                return f_name + '2'

    assert Child.__fields__['y'].alias == 'y2'
    assert Child.__fields__['x'].alias == 'x2'


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


@pytest.mark.skipif(sys.version_info < (3, 7), reason='output slightly different for 3.6')
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
        (Tuple[int, ...], 'Tuple[int, ...]'),
        (Optional[List[int]], 'Optional[List[int]]'),
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

    # output is slightly different for 3.6
    if sys.version_info >= (3, 7):
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
