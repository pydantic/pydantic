import re
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Set, Union

import pytest

from pydantic import BaseConfig, BaseModel, NoneStrBytes, StrBytes, ValidationError, constr


def test_str_bytes():
    class Model(BaseModel):
        v: StrBytes = ...

    m = Model(v='s')
    assert m.v == 's'
    assert ("<Field v: "
            "type='typing.Union[str, bytes]', "
            "required=True, "
            "sub_fields=["
            "<Field v_str: type='str', required=True, validators=['not_none_validator', 'str_validator', "
            "'anystr_strip_whitespace', 'anystr_length_validator']>, "
            "<Field v_bytes: type='bytes', required=True, validators=['not_none_validator', 'bytes_validator', "
            "'anystr_strip_whitespace', 'anystr_length_validator']>]>") == repr(m.fields['v'])

    m = Model(v=b'b')
    assert m.v == 'b'

    with pytest.raises(ValidationError) as exc_info:
        Model(v=None)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v',),
            'msg': 'none is not an allow value',
            'type': 'type_error.none.not_allowed',
        },
        {
            'loc': ('v',),
            'msg': 'none is not an allow value',
            'type': 'type_error.none.not_allowed',
        },
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

    # NOTE not_none_validator removed
    assert ("{'type': 'typing.Union[str, bytes, NoneType]', "
            "'required': True, "
            "'sub_fields': [<Field v_str: type='str', "
            "required=True, "
            "validators=['str_validator', 'anystr_strip_whitespace', 'anystr_length_validator']>, "
            "<Field v_bytes: type='bytes', required=True, validators=['bytes_validator', "
            "'anystr_strip_whitespace', 'anystr_length_validator']>]}") == repr(m.fields['v'].info)


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
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v',),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
        {
            'loc': ('v',),
            'msg': 'none is not an allow value',
            'type': 'type_error.none.not_allowed',
        },
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
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v', 1),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
        {
            'loc': ('v', 2),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=1)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v',),
            'msg': '\'int\' object is not iterable',
            'type': 'type_error',
        },
    ]


def test_typed_set():
    class Model(BaseModel):
        v: Set[int] = ...

    assert Model(v={1, 2, '3'}).v == {1, 2, 3}
    assert Model(v=[1, 2, '3']).v == {1, 2, 3}

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 'x'])
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v', 1),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
    ]


def test_dict_dict():
    class Model(BaseModel):
        v: Dict[str, int] = ...

    assert Model(v={'foo': 1}).dict() == {'v': {'foo': 1}}


@pytest.mark.parametrize('value,result', [
    ({'a': 2, 'b': 4}, {'a': 2, 'b': 4}),
    ({1: '2', 'b': 4}, {'1': 2, 'b': 4}),
    ([('a', 2), ('b', 4)], {'a': 2, 'b': 4}),
])
def test_typed_dict(value, result):
    class Model(BaseModel):
        v: Dict[str, int] = ...

    assert Model(v=value).v == result


@pytest.mark.parametrize('value,errors', [
    (
        1,
        [
            {
                'loc': ('v',),
                'msg': 'value is not a valid dict, got int',
                'type': 'type_error',
            },
        ],
    ),
    (
        {'a': 'b'},
        [
            {
                'loc': ('v', 'a'),
                'msg': 'value is not a valid integer',
                'type': 'type_error.integer',
            },
        ],
    ),
    (
        [1, 2, 3],
        [
            {
                'loc': ('v',),
                'msg': 'value is not a valid dict, got list',
                'type': 'type_error',
            },
        ],
    ),
])
def test_typed_dict_error(value, errors):
    class Model(BaseModel):
        v: Dict[str, int] = ...

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.flatten_errors() == errors


def test_dict_key_error():
    class Model(BaseModel):
        v: Dict[int, int] = ...

    assert Model(v={1: 2, '3': '4'}).v == {1: 2, 3: 4}

    with pytest.raises(ValidationError) as exc_info:
        Model(v={'foo': 2, '3': '4'})
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v', '__key__'),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
    ]


# TODO re-add when implementing better model validators
# def test_all_model_validator():
#     class OverModel(BaseModel):
#         a: int = ...
#
#         def validate_a_pre(self, v):
#             return f'{v}1'
#
#         def validate_a(self, v):
#             assert isinstance(v, int)
#             return f'{v}_main'
#
#         def validate_a_post(self, v):
#             assert isinstance(v, str)
#             return f'{v}_post'
#
#     m = OverModel(a=1)
#     assert m.a == '11_main_post'


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
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v', 0),
            'msg': 'dictionary update sequence element #0 has length 1; 2 is required',
            'type': 'value_error',
        },
    ]


def test_recursive_list_error():
    class SubModel(BaseModel):
        name: str = ...
        count: int = None

    class Model(BaseModel):
        v: List[SubModel] = []

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[{}])
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v', 0, 'name'),
            'msg': 'field required',
            'type': 'value_error.missing',
        },
    ]


def test_list_unions():
    class Model(BaseModel):
        v: List[Union[int, str]] = ...

    assert Model(v=[123, '456', 'foobar']).v == [123, 456, 'foobar']

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, None])
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v', 2),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
        {
            'loc': ('v', 2),
            'msg': 'none is not an allow value',
            'type': 'type_error.none.not_allowed',
        },
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
    assert repr(Model.__fields__['a']) == ("<Field a (alias '_a'): type='str', default='foobar',"
                                           " required=False, validators=['not_none_validator', 'str_validator',"
                                           " 'anystr_strip_whitespace', 'anystr_length_validator']>")


def test_alias_error():
    class Model(BaseModel):
        a = 123

        class Config:
            fields = {'a': '_a'}

    assert Model(_a='123').a == 123

    with pytest.raises(ValidationError) as exc_info:
        Model(_a='foo')
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('_a',),
            'msg': 'value is not a valid integer',
            'type': 'type_error.integer',
        },
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
    with pytest.raises(TypeError) as exc_info:
        class Model(BaseModel):
            x: 43 = 123
    assert "error checking inheritance of 43 (type: int)" in str(exc_info)


@pytest.mark.parametrize('value,expected', [
    ('a string', 'a string'),
    (b'some bytes', 'some bytes'),
    (bytearray('foobar', encoding='utf8'), 'foobar'),
    (123, '123'),
    (123.45, '123.45'),
    (Decimal('12.45'), '12.45'),
    (True, 'True'),
    (False, 'False'),
    (StrEnum.a, 'a10'),
])
def test_valid_string_types(value, expected):
    class Model(BaseModel):
        v: str

    assert Model(v=value).v == expected


@pytest.mark.parametrize('value,errors', [
    (
        {'foo': 'bar'},
        [
            {
                'loc': ('v',),
                'msg': 'str or byte type expected not dict',
                'type': 'type_error',
            },
        ],
    ),
    (
        [1, 2, 3],
        [
            {
                'loc': ('v',),
                'msg': 'str or byte type expected not list',
                'type': 'type_error',
            },
        ],
    )
])
def test_invalid_string_types(value, errors):
    class Model(BaseModel):
        v: str

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.flatten_errors() == errors


def test_inheritance_config():
    class Parent(BaseModel):
        a: int

    class Child(Parent):
        b: str

        class Config:
            fields = {
                'a': 'aaa',
                'b': 'bbb',
            }

    m = Child(aaa=1, bbb='s')
    assert str(m) == "Child a=1 b='s'"


def test_partial_inheritance_config():
    class Parent(BaseModel):
        a: int

        class Config:
            fields = {
                'a': 'aaa',
            }

    class Child(Parent):
        b: str

        class Config:
            fields = {
                'b': 'bbb',
            }

    m = Child(aaa=1, bbb='s')
    assert str(m) == "Child a=1 b='s'"


def test_string_none():
    class Model(BaseModel):
        a: constr(min_length=20, max_length=1000) = ...

        class Config:
            ignore_extra = True

    with pytest.raises(ValidationError) as exc_info:
        Model(a=None)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('a',),
            'msg': 'none is not an allow value',
            'type': 'type_error.none.not_allowed',
        },
    ]


def test_alias_camel_case():
    class Model(BaseModel):
        one_thing: int
        another_thing: int

        class Config(BaseConfig):
            @classmethod
            def get_field_config(cls, name):
                field_config = super().get_field_config(name) or {}
                if 'alias' not in field_config:
                    field_config['alias'] = re.sub(r'(?:^|_)([a-z])', lambda m: m.group(1).upper(), name)
                return field_config

    v = Model(**{'OneThing': 123, 'AnotherThing': '321'})
    assert v.one_thing == 123
    assert v.another_thing == 321
    assert v == {'one_thing': 123, 'another_thing': 321}


def test_get_field_config_inherit():
    class ModelOne(BaseModel):
        class Config(BaseConfig):
            @classmethod
            def get_field_config(cls, name):
                field_config = super().get_field_config(name) or {}
                if 'alias' not in field_config:
                    field_config['alias'] = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)
                return field_config

    class ModelTwo(ModelOne):
        one_thing: int
        another_thing: int
        third_thing: int

        class Config:
            fields = {
                'third_thing': 'Banana'
            }

    v = ModelTwo(**{'oneThing': 123, 'anotherThing': '321', 'Banana': 1})
    assert v == {'one_thing': 123, 'another_thing': 321, 'third_thing': 1}
