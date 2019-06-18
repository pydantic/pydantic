import re
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pytest

from pydantic import (
    BaseConfig,
    BaseModel,
    Extra,
    NoneStrBytes,
    StrBytes,
    ValidationError,
    constr,
    errors,
    validate_model,
)


def test_str_bytes():
    class Model(BaseModel):
        v: StrBytes = ...

    m = Model(v='s')
    assert m.v == 's'
    assert '<Field(v type=typing.Union[str, bytes] required)>' == repr(m.fields['v'])
    assert 'not_none_validator' in [v.__qualname__ for v in m.fields['v'].sub_fields[0].validators]

    m = Model(v=b'b')
    assert m.v == 'b'

    with pytest.raises(ValidationError) as exc_info:
        Model(v=None)
    assert exc_info.value.errors() == [
        {'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
        {'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
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
        {'loc': ('v',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v',), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
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

    m = Model(simple_tuple=[1, 2, 3, 4], tuple_of_different_types=[1, 2, 3, 4])
    assert m.dict() == {'simple_tuple': (1, 2, 3, 4), 'tuple_of_different_types': (1, 2.0, '3', True)}


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
    assert "<Model v=[<SubModel name='testing' count=4>]>" == repr(m)
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
        {'loc': ('v', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 2), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
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
    assert repr(Model.__fields__['a']) == "<Field(a type=str default='foobar' alias=_a)>"


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


def test_include_exclude_default():
    class Model(BaseModel):
        a: int
        b: int
        c: int = 3
        d: int = 4

    m = Model(a=1, b=2)
    assert m.dict() == {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    assert m.__fields_set__ == {'a', 'b'}
    assert m.dict(skip_defaults=True) == {'a': 1, 'b': 2}

    assert m.dict(include={'a'}, skip_defaults=True) == {'a': 1}
    assert m.dict(include={'c'}, skip_defaults=True) == {}

    assert m.dict(exclude={'a'}, skip_defaults=True) == {'b': 2}
    assert m.dict(exclude={'c'}, skip_defaults=True) == {'a': 1, 'b': 2}

    assert m.dict(include={'a', 'b', 'c'}, exclude={'b'}, skip_defaults=True) == {'a': 1}
    assert m.dict(include={'a', 'b', 'c'}, exclude={'a', 'c'}, skip_defaults=True) == {'b': 2}


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
    assert m.dict(skip_defaults=True) == {'a': 1, 'b': 2}

    m2 = Model(a=1, b=2, d=4)
    assert m2.dict() == {'a': 1, 'b': 2, 'c': 3}
    assert m2.__fields_set__ == {'a', 'b'}
    assert m2.dict(skip_defaults=True) == {'a': 1, 'b': 2}


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
    assert m.dict(skip_defaults=True) == {'a': 1, 'b': 2}

    m2 = Model(a=1, b=2, d=4)
    assert m2.dict() == {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    assert m2.__fields_set__ == {'a', 'b', 'd'}
    assert m2.dict(skip_defaults=True) == {'a': 1, 'b': 2, 'd': 4}


def test_field_set_field_name():
    class Model(BaseModel):
        a: int
        field_set: int
        b: int = 3

    assert Model(a=1, field_set=2).dict() == {'a': 1, 'field_set': 2, 'b': 3}
    assert Model(a=1, field_set=2).dict(skip_defaults=True) == {'a': 1, 'field_set': 2}
    assert Model.construct(dict(a=1, field_set=3), {'a', 'field_set'}).dict() == {'a': 1, 'field_set': 3}


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
        a = 123

    assert Bar().dict() == {'x': 12.3, 'a': 123}


def test_invalid_type():
    with pytest.raises(RuntimeError) as exc_info:

        class Model(BaseModel):
            x: 43 = 123

    assert "error checking inheritance of 43 (type: int)" in str(exc_info)


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
    assert str(m) == "Child a=1 b='s'"


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
    assert str(m) == "Child a=1 b='s'"


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
            def get_field_schema(cls, name):
                field_config = super().get_field_schema(name) or {}
                if 'alias' not in field_config:
                    field_config['alias'] = re.sub(r'(?:^|_)([a-z])', lambda m: m.group(1).upper(), name)
                return field_config

    v = Model(**{'OneThing': 123, 'AnotherThing': '321'})
    assert v.one_thing == 123
    assert v.another_thing == 321
    assert v == {'one_thing': 123, 'another_thing': 321}


def test_get_field_schema_inherit():
    class ModelOne(BaseModel):
        class Config(BaseConfig):
            @classmethod
            def get_field_schema(cls, name):
                field_config = super().get_field_schema(name) or {}
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


def test_get_validator():
    class CustomClass:
        @classmethod
        def get_validators(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            return v * 2

    with pytest.warns(DeprecationWarning):

        class Model(BaseModel):
            x: CustomClass

    assert Model(x=42).x == 84


def test_multiple_errors():
    class Model(BaseModel):
        a: Union[None, int, float, Decimal]

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foobar')

    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not none', 'type': 'type_error.none.allowed'},
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
            allow_population_by_alias = True
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


def test_ignore_extra_true():
    with pytest.warns(DeprecationWarning, match='Model: "ignore_extra" is deprecated and replaced by "extra"'):

        class Model(BaseModel):
            foo: int

            class Config:
                ignore_extra = True

    assert Model.__config__.extra is Extra.ignore


def test_ignore_extra_false():
    with pytest.warns(DeprecationWarning, match='Model: "ignore_extra" is deprecated and replaced by "extra"'):

        class Model(BaseModel):
            foo: int

            class Config:
                ignore_extra = False

    assert Model.__config__.extra is Extra.forbid


def test_allow_extra():
    with pytest.warns(DeprecationWarning, match='Model: "allow_extra" is deprecated and replaced by "extra"'):

        class Model(BaseModel):
            foo: int

            class Config:
                allow_extra = True

    assert Model.__config__.extra is Extra.allow


def test_ignore_extra_allow_extra():
    with pytest.warns(DeprecationWarning, match='Model: "ignore_extra" and "allow_extra" are deprecated and'):

        class Model(BaseModel):
            foo: int

            class Config:
                ignore_extra = False
                allow_extra = False

    assert Model.__config__.extra is Extra.forbid


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
            allow_population_by_alias = True

    assert BaseModel.__config__.allow_mutation is True
    assert BaseModel.__config__.allow_population_by_alias is False
    assert BaseModel.__config__.extra is Extra.ignore
    assert BaseModel.__config__.use_enum_values is False

    assert Parent.__config__.allow_mutation is False
    assert Parent.__config__.allow_population_by_alias is False
    assert Parent.__config__.extra is Extra.forbid
    assert Parent.__config__.use_enum_values is False

    assert Mixin.__config__.allow_mutation is True
    assert Mixin.__config__.allow_population_by_alias is False
    assert Mixin.__config__.extra is Extra.ignore
    assert Mixin.__config__.use_enum_values is True

    assert Child.__config__.allow_mutation is False
    assert Child.__config__.allow_population_by_alias is True
    assert Child.__config__.extra is Extra.forbid
    assert Child.__config__.use_enum_values is True


def test_multiple_inheritance_config_legacy_extra():
    with pytest.warns(DeprecationWarning, match='Parent: "ignore_extra" and "allow_extra" are deprecated and'):

        class Parent(BaseModel):
            class Config:
                allow_extra = False
                ignore_extra = False

        class Mixin(BaseModel):
            pass

        class Child(Mixin, Parent):
            pass

    assert BaseModel.__config__.extra is Extra.ignore
    assert Parent.__config__.extra is Extra.forbid
    assert Mixin.__config__.extra is Extra.ignore
    assert Child.__config__.extra is Extra.forbid


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
