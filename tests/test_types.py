import itertools
import os
import re
import sys
import uuid
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path
from typing import (
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    MutableSet,
    NewType,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
)
from uuid import UUID

import pytest

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    BaseModel,
    ByteSize,
    ConfigError,
    DirectoryPath,
    EmailStr,
    Field,
    FilePath,
    Json,
    NameEmail,
    NegativeFloat,
    NegativeInt,
    PositiveFloat,
    PositiveInt,
    PyObject,
    SecretBytes,
    SecretStr,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    ValidationError,
    conbytes,
    condecimal,
    confloat,
    conint,
    conlist,
    conset,
    constr,
    create_model,
    errors,
    validator,
)

try:
    import email_validator
except ImportError:
    email_validator = None

try:
    import typing_extensions
except ImportError:
    typing_extensions = None


class ConBytesModel(BaseModel):
    v: conbytes(max_length=10) = b'foobar'


def foo():
    return 42


def test_constrained_bytes_good():
    m = ConBytesModel(v=b'short')
    assert m.v == b'short'


def test_constrained_bytes_default():
    m = ConBytesModel()
    assert m.v == b'foobar'


def test_constrained_bytes_too_long():
    with pytest.raises(ValidationError) as exc_info:
        ConBytesModel(v=b'this is too long')
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at most 10 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 10},
        }
    ]


def test_constrained_list_good():
    class ConListModelMax(BaseModel):
        v: conlist(int) = []

    m = ConListModelMax(v=[1, 2, 3])
    assert m.v == [1, 2, 3]


def test_constrained_list_default():
    class ConListModelMax(BaseModel):
        v: conlist(int) = []

    m = ConListModelMax()
    assert m.v == []


def test_constrained_list_too_long():
    class ConListModelMax(BaseModel):
        v: conlist(int, max_items=10) = []

    with pytest.raises(ValidationError) as exc_info:
        ConListModelMax(v=list(str(i) for i in range(11)))
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at most 10 items',
            'type': 'value_error.list.max_items',
            'ctx': {'limit_value': 10},
        }
    ]


def test_constrained_list_too_short():
    class ConListModelMin(BaseModel):
        v: conlist(int, min_items=1)

    with pytest.raises(ValidationError) as exc_info:
        ConListModelMin(v=[])
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at least 1 items',
            'type': 'value_error.list.min_items',
            'ctx': {'limit_value': 1},
        }
    ]


def test_constrained_list_constraints():
    class ConListModelBoth(BaseModel):
        v: conlist(int, min_items=7, max_items=11)

    m = ConListModelBoth(v=list(range(7)))
    assert m.v == list(range(7))

    m = ConListModelBoth(v=list(range(11)))
    assert m.v == list(range(11))

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=list(range(6)))
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at least 7 items',
            'type': 'value_error.list.min_items',
            'ctx': {'limit_value': 7},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=list(range(12)))
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at most 11 items',
            'type': 'value_error.list.max_items',
            'ctx': {'limit_value': 11},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConListModelBoth(v=1)
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_constrained_list_item_type_fails():
    class ConListModel(BaseModel):
        v: conlist(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConListModel(v=['a', 'b', 'c'])
    assert exc_info.value.errors() == [
        {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_conlist():
    class Model(BaseModel):
        foo: List[int] = Field(..., min_items=2, max_items=4)
        bar: conlist(str, min_items=1, max_items=4) = None

    assert Model(foo=[1, 2], bar=['spoon']).dict() == {'foo': [1, 2], 'bar': ['spoon']}

    with pytest.raises(ValidationError, match='ensure this value has at least 2 items'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='ensure this value has at most 4 items'):
        Model(foo=list(range(5)))

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'foo': {'title': 'Foo', 'type': 'array', 'items': {'type': 'integer'}, 'minItems': 2, 'maxItems': 4},
            'bar': {'title': 'Bar', 'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 4},
        },
        'required': ['foo'],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    assert exc_info.value.errors() == [
        {'loc': ('foo', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('foo', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_conlist_wrong_type_default():
    """It should not validate default value by default"""

    class Model(BaseModel):
        v: conlist(int) = 'a'

    m = Model()
    assert m.v == 'a'


def test_constrained_set_good():
    class Model(BaseModel):
        v: conset(int) = []

    m = Model(v=[1, 2, 3])
    assert m.v == {1, 2, 3}


def test_constrained_set_default():
    class Model(BaseModel):
        v: conset(int) = set()

    m = Model()
    assert m.v == set()


def test_constrained_set_default_invalid():
    class Model(BaseModel):
        v: conset(int) = 'not valid, not validated'

    m = Model()
    assert m.v == 'not valid, not validated'


def test_constrained_set_too_long():
    class ConSetModelMax(BaseModel):
        v: conset(int, max_items=10) = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelMax(v=set(str(i) for i in range(11)))
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at most 10 items',
            'type': 'value_error.set.max_items',
            'ctx': {'limit_value': 10},
        }
    ]


def test_constrained_set_too_short():
    class ConSetModelMin(BaseModel):
        v: conset(int, min_items=1)

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelMin(v=[])
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at least 1 items',
            'type': 'value_error.set.min_items',
            'ctx': {'limit_value': 1},
        }
    ]


def test_constrained_set_constraints():
    class ConSetModelBoth(BaseModel):
        v: conset(int, min_items=7, max_items=11)

    m = ConSetModelBoth(v=set(range(7)))
    assert m.v == set(range(7))

    m = ConSetModelBoth(v=set(range(11)))
    assert m.v == set(range(11))

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=set(range(6)))
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at least 7 items',
            'type': 'value_error.set.min_items',
            'ctx': {'limit_value': 7},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=set(range(12)))
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at most 11 items',
            'type': 'value_error.set.max_items',
            'ctx': {'limit_value': 11},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ConSetModelBoth(v=1)
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid set', 'type': 'type_error.set'}]


def test_constrained_set_item_type_fails():
    class ConSetModel(BaseModel):
        v: conset(int) = []

    with pytest.raises(ValidationError) as exc_info:
        ConSetModel(v=['a', 'b', 'c'])
    assert exc_info.value.errors() == [
        {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('v', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_conset():
    class Model(BaseModel):
        foo: Set[int] = Field(..., min_items=2, max_items=4)
        bar: conset(str, min_items=1, max_items=4) = None

    assert Model(foo=[1, 2], bar=['spoon']).dict() == {'foo': {1, 2}, 'bar': {'spoon'}}

    assert Model(foo=[1, 1, 1, 2, 2], bar=['spoon']).dict() == {'foo': {1, 2}, 'bar': {'spoon'}}

    with pytest.raises(ValidationError, match='ensure this value has at least 2 items'):
        Model(foo=[1])

    with pytest.raises(ValidationError, match='ensure this value has at most 4 items'):
        Model(foo=list(range(5)))

    assert Model.schema() == {
        'title': 'Model',
        'type': 'object',
        'properties': {
            'foo': {
                'title': 'Foo',
                'type': 'array',
                'items': {'type': 'integer'},
                'uniqueItems': True,
                'minItems': 2,
                'maxItems': 4,
            },
            'bar': {
                'title': 'Bar',
                'type': 'array',
                'items': {'type': 'string'},
                'uniqueItems': True,
                'minItems': 1,
                'maxItems': 4,
            },
        },
        'required': ['foo'],
    }

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=[1, 'x', 'y'])
    errors = exc_info.value.errors()
    assert len(errors) == 2
    assert all(error['msg'] == 'value is not a valid integer' for error in errors)

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=1)
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'value is not a valid set', 'type': 'type_error.set'}]


def test_conset_not_required():
    class Model(BaseModel):
        foo: Set[int] = None

    assert Model(foo=None).foo is None
    assert Model().foo is None


class ConStringModel(BaseModel):
    v: constr(max_length=10) = 'foobar'


def test_constrained_str_good():
    m = ConStringModel(v='short')
    assert m.v == 'short'


def test_constrained_str_default():
    m = ConStringModel()
    assert m.v == 'foobar'


def test_constrained_str_too_long():
    with pytest.raises(ValidationError) as exc_info:
        ConStringModel(v='this is too long')
    assert exc_info.value.errors() == [
        {
            'loc': ('v',),
            'msg': 'ensure this value has at most 10 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 10},
        }
    ]


def test_module_import():
    class PyObjectModel(BaseModel):
        module: PyObject = 'os.path'

    m = PyObjectModel()
    assert m.module == os.path

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(module='foobar')
    assert exc_info.value.errors() == [
        {
            'loc': ('module',),
            'msg': 'ensure this value contains valid import path or valid callable: '
            '"foobar" doesn\'t look like a module path',
            'type': 'type_error.pyobject',
            'ctx': {'error_message': '"foobar" doesn\'t look like a module path'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(module='os.missing')
    assert exc_info.value.errors() == [
        {
            'loc': ('module',),
            'msg': 'ensure this value contains valid import path or valid callable: '
            'Module "os" does not define a "missing" attribute',
            'type': 'type_error.pyobject',
            'ctx': {'error_message': 'Module "os" does not define a "missing" attribute'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(module=[1, 2, 3])
    assert exc_info.value.errors() == [
        {
            'loc': ('module',),
            'msg': 'ensure this value contains valid import path or valid callable: '
            'value is neither a valid import path not a valid callable',
            'type': 'type_error.pyobject',
            'ctx': {'error_message': 'value is neither a valid import path not a valid callable'},
        }
    ]


def test_pyobject_none():
    class PyObjectModel(BaseModel):
        module: PyObject = None

    m = PyObjectModel()
    assert m.module is None


def test_pyobject_callable():
    class PyObjectModel(BaseModel):
        foo: PyObject = foo

    m = PyObjectModel()
    assert m.foo is foo
    assert m.foo() == 42


class CheckModel(BaseModel):
    bool_check = True
    str_check = 's'
    bytes_check = b's'
    int_check = 1
    float_check = 1.0
    uuid_check: UUID = UUID('7bd00d58-6485-4ca6-b889-3da6d8df3ee4')
    decimal_check: Decimal = Decimal('42.24')

    class Config:
        anystr_strip_whitespace = True
        max_anystr_length = 10


class BoolCastable:
    def __bool__(self) -> bool:
        return True


@pytest.mark.parametrize(
    'field,value,result',
    [
        ('bool_check', True, True),
        ('bool_check', 1, True),
        ('bool_check', 'y', True),
        ('bool_check', 'Y', True),
        ('bool_check', 'yes', True),
        ('bool_check', 'Yes', True),
        ('bool_check', 'YES', True),
        ('bool_check', 'true', True),
        ('bool_check', 'True', True),
        ('bool_check', 'TRUE', True),
        ('bool_check', 'on', True),
        ('bool_check', 'On', True),
        ('bool_check', 'ON', True),
        ('bool_check', '1', True),
        ('bool_check', 't', True),
        ('bool_check', 'T', True),
        ('bool_check', b'TRUE', True),
        ('bool_check', False, False),
        ('bool_check', 0, False),
        ('bool_check', 'n', False),
        ('bool_check', 'N', False),
        ('bool_check', 'no', False),
        ('bool_check', 'No', False),
        ('bool_check', 'NO', False),
        ('bool_check', 'false', False),
        ('bool_check', 'False', False),
        ('bool_check', 'FALSE', False),
        ('bool_check', 'off', False),
        ('bool_check', 'Off', False),
        ('bool_check', 'OFF', False),
        ('bool_check', '0', False),
        ('bool_check', 'f', False),
        ('bool_check', 'F', False),
        ('bool_check', b'FALSE', False),
        ('bool_check', None, ValidationError),
        ('bool_check', '', ValidationError),
        ('bool_check', [], ValidationError),
        ('bool_check', {}, ValidationError),
        ('bool_check', [1, 2, 3, 4], ValidationError),
        ('bool_check', {1: 2, 3: 4}, ValidationError),
        ('bool_check', b'2', ValidationError),
        ('bool_check', '2', ValidationError),
        ('bool_check', 2, ValidationError),
        ('bool_check', b'\x81', ValidationError),
        ('bool_check', BoolCastable(), ValidationError),
        ('str_check', 's', 's'),
        ('str_check', '  s  ', 's'),
        ('str_check', b's', 's'),
        ('str_check', b'  s  ', 's'),
        ('str_check', 1, '1'),
        ('str_check', 'x' * 11, ValidationError),
        ('str_check', b'x' * 11, ValidationError),
        ('bytes_check', 's', b's'),
        ('bytes_check', '  s  ', b's'),
        ('bytes_check', b's', b's'),
        ('bytes_check', b'  s  ', b's'),
        ('bytes_check', 1, b'1'),
        ('bytes_check', bytearray('xx', encoding='utf8'), b'xx'),
        ('bytes_check', True, b'True'),
        ('bytes_check', False, b'False'),
        ('bytes_check', {}, ValidationError),
        ('bytes_check', 'x' * 11, ValidationError),
        ('bytes_check', b'x' * 11, ValidationError),
        ('int_check', 1, 1),
        ('int_check', 1.9, 1),
        ('int_check', '1', 1),
        ('int_check', '1.9', ValidationError),
        ('int_check', b'1', 1),
        ('int_check', 12, 12),
        ('int_check', '12', 12),
        ('int_check', b'12', 12),
        ('float_check', 1, 1.0),
        ('float_check', 1.0, 1.0),
        ('float_check', '1.0', 1.0),
        ('float_check', '1', 1.0),
        ('float_check', b'1.0', 1.0),
        ('float_check', b'1', 1.0),
        ('uuid_check', 'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        ('uuid_check', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        ('uuid_check', b'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        ('uuid_check', b'\x12\x34\x56\x78' * 4, UUID('12345678-1234-5678-1234-567812345678')),
        ('uuid_check', 'ebcdab58-6eb8-46fb-a190-', ValidationError),
        ('uuid_check', 123, ValidationError),
        ('decimal_check', 42.24, Decimal('42.24')),
        ('decimal_check', '42.24', Decimal('42.24')),
        ('decimal_check', b'42.24', Decimal('42.24')),
        ('decimal_check', '  42.24  ', Decimal('42.24')),
        ('decimal_check', Decimal('42.24'), Decimal('42.24')),
        ('decimal_check', 'not a valid decimal', ValidationError),
        ('decimal_check', 'NaN', ValidationError),
    ],
)
def test_default_validators(field, value, result):
    kwargs = {field: value}
    if result == ValidationError:
        with pytest.raises(ValidationError):
            CheckModel(**kwargs)
    else:
        assert CheckModel(**kwargs).dict()[field] == result


class StrModel(BaseModel):
    str_check: str

    class Config:
        min_anystr_length = 5
        max_anystr_length = 10


def test_string_too_long():
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x' * 150)
    assert exc_info.value.errors() == [
        {
            'loc': ('str_check',),
            'msg': 'ensure this value has at most 10 characters',
            'type': 'value_error.any_str.max_length',
            'ctx': {'limit_value': 10},
        }
    ]


def test_string_too_short():
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x')
    assert exc_info.value.errors() == [
        {
            'loc': ('str_check',),
            'msg': 'ensure this value has at least 5 characters',
            'type': 'value_error.any_str.min_length',
            'ctx': {'limit_value': 5},
        }
    ]


class DatetimeModel(BaseModel):
    dt: datetime = ...
    date_: date = ...
    time_: time = ...
    duration: timedelta = ...


def test_datetime_successful():
    m = DatetimeModel(dt='2017-10-5T19:47:07', date_=1_494_012_000, time_='10:20:30.400', duration='15:30.0001')
    assert m.dt == datetime(2017, 10, 5, 19, 47, 7)
    assert m.date_ == date(2017, 5, 5)
    assert m.time_ == time(10, 20, 30, 400_000)
    assert m.duration == timedelta(minutes=15, seconds=30, microseconds=100)


def test_datetime_errors():
    with pytest.raises(ValueError) as exc_info:
        DatetimeModel(dt='2017-13-5T19:47:07', date_='XX1494012000', time_='25:20:30.400', duration='15:30.0001 broken')
    assert exc_info.value.errors() == [
        {'loc': ('dt',), 'msg': 'invalid datetime format', 'type': 'value_error.datetime'},
        {'loc': ('date_',), 'msg': 'invalid date format', 'type': 'value_error.date'},
        {'loc': ('time_',), 'msg': 'invalid time format', 'type': 'value_error.time'},
        {'loc': ('duration',), 'msg': 'invalid duration format', 'type': 'value_error.duration'},
    ]


class FruitEnum(str, Enum):
    pear = 'pear'
    banana = 'banana'


class ToolEnum(IntEnum):
    spanner = 1
    wrench = 2


class CookingModel(BaseModel):
    fruit: FruitEnum = FruitEnum.pear
    tool: ToolEnum = ToolEnum.spanner


def test_enum_successful():
    m = CookingModel(tool=2)
    assert m.fruit == FruitEnum.pear
    assert m.tool == ToolEnum.wrench
    assert repr(m.tool) == '<ToolEnum.wrench: 2>'


def test_enum_fails():
    with pytest.raises(ValueError) as exc_info:
        CookingModel(tool=3)
    assert exc_info.value.errors() == [
        {
            'loc': ('tool',),
            'msg': 'value is not a valid enumeration member; permitted: 1, 2',
            'type': 'type_error.enum',
            'ctx': {'enum_values': [ToolEnum.spanner, ToolEnum.wrench]},
        }
    ]
    assert len(exc_info.value.json()) == 217


def test_int_enum_successful_for_str_int():
    m = CookingModel(tool='2')
    assert m.tool == ToolEnum.wrench
    assert repr(m.tool) == '<ToolEnum.wrench: 2>'


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_success():
    class MoreStringsModel(BaseModel):
        str_strip_enabled: constr(strip_whitespace=True)
        str_strip_disabled: constr(strip_whitespace=False)
        str_regex: constr(regex=r'^xxx\d{3}$') = ...  # noqa: F722
        str_min_length: constr(min_length=5) = ...
        str_curtailed: constr(curtail_length=5) = ...
        str_email: EmailStr = ...
        name_email: NameEmail = ...

    m = MoreStringsModel(
        str_strip_enabled='   xxx123   ',
        str_strip_disabled='   xxx123   ',
        str_regex='xxx123',
        str_min_length='12345',
        str_curtailed='123456',
        str_email='foobar@example.com  ',
        name_email='foo bar  <foobaR@example.com>',
    )
    assert m.str_strip_enabled == 'xxx123'
    assert m.str_strip_disabled == '   xxx123   '
    assert m.str_regex == 'xxx123'
    assert m.str_curtailed == '12345'
    assert m.str_email == 'foobar@example.com'
    assert repr(m.name_email) == "NameEmail(name='foo bar', email='foobaR@example.com')"
    assert str(m.name_email) == 'foo bar <foobaR@example.com>'
    assert m.name_email.name == 'foo bar'
    assert m.name_email.email == 'foobaR@example.com'


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_fails():
    class MoreStringsModel(BaseModel):
        str_regex: constr(regex=r'^xxx\d{3}$') = ...  # noqa: F722
        str_min_length: constr(min_length=5) = ...
        str_curtailed: constr(curtail_length=5) = ...
        str_email: EmailStr = ...
        name_email: NameEmail = ...

    with pytest.raises(ValidationError) as exc_info:
        MoreStringsModel(
            str_regex='xxx123xxx',
            str_min_length='1234',
            str_curtailed='123',  # doesn't fail
            str_email='foobar<@example.com',
            name_email='foobar @example.com',
        )
    assert exc_info.value.errors() == [
        {
            'loc': ('str_regex',),
            'msg': 'string does not match regex "^xxx\\d{3}$"',
            'type': 'value_error.str.regex',
            'ctx': {'pattern': '^xxx\\d{3}$'},
        },
        {
            'loc': ('str_min_length',),
            'msg': 'ensure this value has at least 5 characters',
            'type': 'value_error.any_str.min_length',
            'ctx': {'limit_value': 5},
        },
        {'loc': ('str_email',), 'msg': 'value is not a valid email address', 'type': 'value_error.email'},
        {'loc': ('name_email',), 'msg': 'value is not a valid email address', 'type': 'value_error.email'},
    ]


@pytest.mark.skipif(email_validator, reason='email_validator is installed')
def test_email_validator_not_installed_email_str():
    with pytest.raises(ImportError):

        class Model(BaseModel):
            str_email: EmailStr = ...


@pytest.mark.skipif(email_validator, reason='email_validator is installed')
def test_email_validator_not_installed_name_email():
    with pytest.raises(ImportError):

        class Model(BaseModel):
            str_email: NameEmail = ...


def test_dict():
    class Model(BaseModel):
        v: dict

    assert Model(v={1: 10, 2: 20}).v == {1: 10, 2: 20}
    assert Model(v=[(1, 2), (3, 4)]).v == {1: 2, 3: 4}

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}]


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], [1, 2, '3']),
        ((1, 2, '3'), [1, 2, '3']),
        ({1, 2, '3'}, list({1, 2, '3'})),
        ((i ** 2 for i in range(5)), [0, 1, 4, 9, 16]),
    ),
)
def test_list_success(value, result):
    class Model(BaseModel):
        v: list

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123'))
def test_list_fails(value):
    class Model(BaseModel):
        v: list

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_ordered_dict():
    class Model(BaseModel):
        v: OrderedDict

    assert Model(v=OrderedDict([(1, 10), (2, 20)])).v == OrderedDict([(1, 10), (2, 20)])
    assert Model(v={1: 10, 2: 20}).v in (OrderedDict([(1, 10), (2, 20)]), OrderedDict([(2, 20), (1, 10)]))
    assert Model(v=[(1, 2), (3, 4)]).v == OrderedDict([(1, 2), (3, 4)])

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, 3])
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}]


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], (1, 2, '3')),
        ((1, 2, '3'), (1, 2, '3')),
        ({1, 2, '3'}, tuple({1, 2, '3'})),
        ((i ** 2 for i in range(5)), (0, 1, 4, 9, 16)),
    ),
)
def test_tuple_success(value, result):
    class Model(BaseModel):
        v: tuple

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123'))
def test_tuple_fails(value):
    class Model(BaseModel):
        v: tuple

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid tuple', 'type': 'type_error.tuple'}]


@pytest.mark.parametrize(
    'value,cls,result',
    (
        ([1, 2, '3'], int, (1, 2, 3)),
        ((1, 2, '3'), int, (1, 2, 3)),
        ((i ** 2 for i in range(5)), int, (0, 1, 4, 9, 16)),
        (('a', 'b', 'c'), str, ('a', 'b', 'c')),
    ),
)
def test_tuple_variable_len_success(value, cls, result):
    class Model(BaseModel):
        v: Tuple[cls, ...]

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'value, cls, exc',
    [
        (('a', 'b', [1, 2], 'c'), str, [{'loc': ('v', 2), 'msg': 'str type expected', 'type': 'type_error.str'}]),
        (
            ('a', 'b', [1, 2], 'c', [3, 4]),
            str,
            [
                {'loc': ('v', 2), 'msg': 'str type expected', 'type': 'type_error.str'},
                {'loc': ('v', 4), 'msg': 'str type expected', 'type': 'type_error.str'},
            ],
        ),
    ],
)
def test_tuple_variable_len_fails(value, cls, exc):
    class Model(BaseModel):
        v: Tuple[cls, ...]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == exc


@pytest.mark.parametrize(
    'value,result',
    (
        ({1, 2, 2, '3'}, {1, 2, '3'}),
        ((1, 2, 2, '3'), {1, 2, '3'}),
        ([1, 2, 2, '3'], {1, 2, '3'}),
        ({i ** 2 for i in range(5)}, {0, 1, 4, 9, 16}),
    ),
)
def test_set_success(value, result):
    class Model(BaseModel):
        v: set

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (123, '123'))
def test_set_fails(value):
    class Model(BaseModel):
        v: set

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid set', 'type': 'type_error.set'}]


def test_list_type_fails():
    class Model(BaseModel):
        v: List[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid list', 'type': 'type_error.list'}]


def test_set_type_fails():
    class Model(BaseModel):
        v: Set[int]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='123')
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid set', 'type': 'type_error.set'}]


@pytest.mark.parametrize(
    'cls, value,result',
    (
        (int, [1, 2, 3], [1, 2, 3]),
        (int, (1, 2, 3), (1, 2, 3)),
        (float, {1.0, 2.0, 3.0}, {1.0, 2.0, 3.0}),
        (Set[int], [{1, 2}, {3, 4}, {5, 6}], [{1, 2}, {3, 4}, {5, 6}]),
        (Tuple[int, str], ((1, 'a'), (2, 'b'), (3, 'c')), ((1, 'a'), (2, 'b'), (3, 'c'))),
    ),
)
def test_sequence_success(cls, value, result):
    class Model(BaseModel):
        v: Sequence[cls]

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'cls, value,result',
    (
        (int, (i for i in range(3)), iter([0, 1, 2])),
        (float, (float(i) for i in range(3)), iter([0.0, 1.0, 2.0])),
        (str, (str(i) for i in range(3)), iter(['0', '1', '2'])),
    ),
)
def test_sequence_generator_success(cls, value, result):
    class Model(BaseModel):
        v: Sequence[cls]

    validated = Model(v=value).v
    assert isinstance(validated, Iterator)
    assert list(validated) == list(result)


def test_infinite_iterable():
    class Model(BaseModel):
        it: Iterable[int]
        b: int

    def iterable():
        i = 0
        while True:
            i += 1
            yield i

    m = Model(it=iterable(), b=3)

    assert m.b == 3
    assert m.it

    for i in m.it:
        assert i
        if i == 10:
            break


def test_invalid_iterable():
    class Model(BaseModel):
        it: Iterable[int]
        b: int

    with pytest.raises(ValidationError) as exc_info:
        Model(it=3, b=3)
    assert exc_info.value.errors() == [
        {'loc': ('it',), 'msg': 'value is not a valid iterable', 'type': 'type_error.iterable'}
    ]


def test_infinite_iterable_validate_first():
    class Model(BaseModel):
        it: Iterable[int]
        b: int

        @validator('it')
        def infinite_first_int(cls, it, field):
            first_value = next(it)
            if field.sub_fields:
                sub_field = field.sub_fields[0]
                v, error = sub_field.validate(first_value, {}, loc='first_value')
                if error:
                    raise ValidationError([error], cls)
            return itertools.chain([first_value], it)

    def int_iterable():
        i = 0
        while True:
            i += 1
            yield i

    m = Model(it=int_iterable(), b=3)

    assert m.b == 3
    assert m.it

    for i in m.it:
        assert i
        if i == 10:
            break

    def str_iterable():
        while True:
            for c in 'foobarbaz':
                yield c

    with pytest.raises(ValidationError) as exc_info:
        Model(it=str_iterable(), b=3)
    assert exc_info.value.errors() == [
        {'loc': ('it', 'first_value'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


@pytest.mark.parametrize(
    'cls,value,errors',
    (
        (
            int,
            (i for i in ['a', 'b', 'c']),
            [
                {'loc': ('v', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
                {'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
                {'loc': ('v', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
            ],
        ),
        (
            float,
            (i for i in ['a', 'b', 'c']),
            [
                {'loc': ('v', 0), 'msg': 'value is not a valid float', 'type': 'type_error.float'},
                {'loc': ('v', 1), 'msg': 'value is not a valid float', 'type': 'type_error.float'},
                {'loc': ('v', 2), 'msg': 'value is not a valid float', 'type': 'type_error.float'},
            ],
        ),
    ),
)
def test_sequence_generator_fails(cls, value, errors):
    class Model(BaseModel):
        v: Sequence[cls]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


@pytest.mark.parametrize(
    'cls,value,errors',
    (
        (int, [1, 'a', 3], [{'loc': ('v', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]),
        (int, (1, 2, 'a'), [{'loc': ('v', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]),
        (float, range(10), [{'loc': ('v',), 'msg': 'value is not a valid sequence', 'type': 'type_error.sequence'}]),
        (float, ('a', 2.2, 3.3), [{'loc': ('v', 0), 'msg': 'value is not a valid float', 'type': 'type_error.float'}]),
        (float, (1.1, 2.2, 'a'), [{'loc': ('v', 2), 'msg': 'value is not a valid float', 'type': 'type_error.float'}]),
        (
            Set[int],
            [{1, 2}, {2, 3}, {'d'}],
            [{'loc': ('v', 2, 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}],
        ),
        (
            Tuple[int, str],
            ((1, 'a'), ('a', 'a'), (3, 'c')),
            [{'loc': ('v', 1, 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}],
        ),
        (
            List[int],
            [{'a': 1, 'b': 2}, [1, 2], [2, 3]],
            [{'loc': ('v', 0), 'msg': 'value is not a valid list', 'type': 'type_error.list'}],
        ),
    ),
)
def test_sequence_fails(cls, value, errors):
    class Model(BaseModel):
        v: Sequence[cls]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    assert exc_info.value.errors() == errors


def test_int_validation():
    class Model(BaseModel):
        a: PositiveInt = None
        b: NegativeInt = None
        c: conint(gt=4, lt=10) = None
        d: conint(ge=0, le=10) = None
        e: conint(multiple_of=5) = None

    m = Model(a=5, b=-5, c=5, d=0, e=25)
    assert m == {'a': 5, 'b': -5, 'c': 5, 'd': 0, 'e': 25}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5, b=5, c=-5, d=11, e=42)
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'ensure this value is greater than 0',
            'type': 'value_error.number.not_gt',
            'ctx': {'limit_value': 0},
        },
        {
            'loc': ('b',),
            'msg': 'ensure this value is less than 0',
            'type': 'value_error.number.not_lt',
            'ctx': {'limit_value': 0},
        },
        {
            'loc': ('c',),
            'msg': 'ensure this value is greater than 4',
            'type': 'value_error.number.not_gt',
            'ctx': {'limit_value': 4},
        },
        {
            'loc': ('d',),
            'msg': 'ensure this value is less than or equal to 10',
            'type': 'value_error.number.not_le',
            'ctx': {'limit_value': 10},
        },
        {
            'loc': ('e',),
            'msg': 'ensure this value is a multiple of 5',
            'type': 'value_error.number.not_multiple',
            'ctx': {'multiple_of': 5},
        },
    ]


def test_float_validation():
    class Model(BaseModel):
        a: PositiveFloat = None
        b: NegativeFloat = None
        c: confloat(gt=4, lt=12.2) = None
        d: confloat(ge=0, le=9.9) = None
        e: confloat(multiple_of=0.5) = None

    m = Model(a=5.1, b=-5.2, c=5.3, d=9.9, e=2.5)
    assert m.dict() == {'a': 5.1, 'b': -5.2, 'c': 5.3, 'd': 9.9, 'e': 2.5}

    with pytest.raises(ValidationError) as exc_info:
        Model(a=-5.1, b=5.2, c=-5.3, d=9.91, e=4.2)
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'ensure this value is greater than 0',
            'type': 'value_error.number.not_gt',
            'ctx': {'limit_value': 0},
        },
        {
            'loc': ('b',),
            'msg': 'ensure this value is less than 0',
            'type': 'value_error.number.not_lt',
            'ctx': {'limit_value': 0},
        },
        {
            'loc': ('c',),
            'msg': 'ensure this value is greater than 4',
            'type': 'value_error.number.not_gt',
            'ctx': {'limit_value': 4},
        },
        {
            'loc': ('d',),
            'msg': 'ensure this value is less than or equal to 9.9',
            'type': 'value_error.number.not_le',
            'ctx': {'limit_value': 9.9},
        },
        {
            'loc': ('e',),
            'msg': 'ensure this value is a multiple of 0.5',
            'type': 'value_error.number.not_multiple',
            'ctx': {'multiple_of': 0.5},
        },
    ]


def test_strict_str():
    class Model(BaseModel):
        v: StrictStr

    assert Model(v='foobar').v == 'foobar'

    with pytest.raises(ValidationError):
        Model(v=123)

    with pytest.raises(ValidationError):
        Model(v=b'foobar')


def test_strict_str_subclass():
    class MyStrictStr(StrictStr):
        pass

    class Model(BaseModel):
        v: MyStrictStr

    m = Model(v=MyStrictStr('foobar'))
    assert isinstance(m.v, MyStrictStr)
    assert m.v == 'foobar'


def test_strict_bool():
    class Model(BaseModel):
        v: StrictBool

    assert Model(v=True).v is True
    assert Model(v=False).v is False

    with pytest.raises(ValidationError):
        Model(v=1)

    with pytest.raises(ValidationError):
        Model(v='1')

    with pytest.raises(ValidationError):
        Model(v=b'1')


def test_strict_int():
    class Model(BaseModel):
        v: StrictInt

    assert Model(v=123456).v == 123456

    with pytest.raises(ValidationError, match='value is not a valid int'):
        Model(v='123456')

    with pytest.raises(ValidationError, match='value is not a valid int'):
        Model(v=3.14159)


def test_strict_int_subclass():
    class MyStrictInt(StrictInt):
        pass

    class Model(BaseModel):
        v: MyStrictInt

    m = Model(v=MyStrictInt(123456))
    assert isinstance(m.v, MyStrictInt)
    assert m.v == 123456


def test_strict_float():
    class Model(BaseModel):
        v: StrictFloat

    assert Model(v=3.14159).v == 3.14159

    with pytest.raises(ValidationError, match='value is not a valid float'):
        Model(v='3.14159')

    with pytest.raises(ValidationError, match='value is not a valid float'):
        Model(v=123456)


def test_strict_float_subclass():
    class MyStrictFloat(StrictFloat):
        pass

    class Model(BaseModel):
        v: MyStrictFloat

    m = Model(v=MyStrictFloat(3.14159))
    assert isinstance(m.v, MyStrictFloat)
    assert m.v == 3.14159


def test_bool_unhashable_fails():
    class Model(BaseModel):
        v: bool

    with pytest.raises(ValidationError) as exc_info:
        Model(v={})
    assert exc_info.value.errors() == [
        {'loc': ('v',), 'msg': 'value could not be parsed to a boolean', 'type': 'type_error.bool'}
    ]


def test_uuid_error():
    class Model(BaseModel):
        v: UUID

    with pytest.raises(ValidationError) as exc_info:
        Model(v='ebcdab58-6eb8-46fb-a190-d07a3')
    assert exc_info.value.errors() == [{'loc': ('v',), 'msg': 'value is not a valid uuid', 'type': 'type_error.uuid'}]

    with pytest.raises(ValidationError):
        Model(v=None)


class UUIDModel(BaseModel):
    a: UUID1
    b: UUID3
    c: UUID4
    d: UUID5


def test_uuid_validation():
    a = uuid.uuid1()
    b = uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
    c = uuid.uuid4()
    d = uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')

    m = UUIDModel(a=a, b=b, c=c, d=d)
    assert m.dict() == {'a': a, 'b': b, 'c': c, 'd': d}

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=d, b=c, c=b, d=a)
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': 'uuid version 1 expected',
            'type': 'value_error.uuid.version',
            'ctx': {'required_version': 1},
        },
        {
            'loc': ('b',),
            'msg': 'uuid version 3 expected',
            'type': 'value_error.uuid.version',
            'ctx': {'required_version': 3},
        },
        {
            'loc': ('c',),
            'msg': 'uuid version 4 expected',
            'type': 'value_error.uuid.version',
            'ctx': {'required_version': 4},
        },
        {
            'loc': ('d',),
            'msg': 'uuid version 5 expected',
            'type': 'value_error.uuid.version',
            'ctx': {'required_version': 5},
        },
    ]


def test_anystr_strip_whitespace_enabled():
    class Model(BaseModel):
        str_check: str
        bytes_check: bytes

        class Config:
            anystr_strip_whitespace = True

    m = Model(str_check='  123  ', bytes_check=b'  456  ')
    assert m.str_check == '123'
    assert m.bytes_check == b'456'


def test_anystr_strip_whitespace_disabled():
    class Model(BaseModel):
        str_check: str
        bytes_check: bytes

        class Config:
            anystr_strip_whitespace = False

    m = Model(str_check='  123  ', bytes_check=b'  456  ')
    assert m.str_check == '  123  '
    assert m.bytes_check == b'  456  '


@pytest.mark.parametrize(
    'type_,value,result',
    [
        (condecimal(gt=Decimal('42.24')), Decimal('43'), Decimal('43')),
        (
            condecimal(gt=Decimal('42.24')),
            Decimal('42'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure this value is greater than 42.24',
                    'type': 'value_error.number.not_gt',
                    'ctx': {'limit_value': Decimal('42.24')},
                }
            ],
        ),
        (condecimal(lt=Decimal('42.24')), Decimal('42'), Decimal('42')),
        (
            condecimal(lt=Decimal('42.24')),
            Decimal('43'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure this value is less than 42.24',
                    'type': 'value_error.number.not_lt',
                    'ctx': {'limit_value': Decimal('42.24')},
                }
            ],
        ),
        (condecimal(ge=Decimal('42.24')), Decimal('43'), Decimal('43')),
        (condecimal(ge=Decimal('42.24')), Decimal('42.24'), Decimal('42.24')),
        (
            condecimal(ge=Decimal('42.24')),
            Decimal('42'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure this value is greater than or equal to 42.24',
                    'type': 'value_error.number.not_ge',
                    'ctx': {'limit_value': Decimal('42.24')},
                }
            ],
        ),
        (condecimal(le=Decimal('42.24')), Decimal('42'), Decimal('42')),
        (condecimal(le=Decimal('42.24')), Decimal('42.24'), Decimal('42.24')),
        (
            condecimal(le=Decimal('42.24')),
            Decimal('43'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure this value is less than or equal to 42.24',
                    'type': 'value_error.number.not_le',
                    'ctx': {'limit_value': Decimal('42.24')},
                }
            ],
        ),
        (condecimal(max_digits=2, decimal_places=2), Decimal('0.99'), Decimal('0.99')),
        (
            condecimal(max_digits=2, decimal_places=1),
            Decimal('0.99'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 1 decimal places',
                    'type': 'value_error.decimal.max_places',
                    'ctx': {'decimal_places': 1},
                }
            ],
        ),
        (
            condecimal(max_digits=3, decimal_places=1),
            Decimal('999'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 2 digits before the decimal point',
                    'type': 'value_error.decimal.whole_digits',
                    'ctx': {'whole_digits': 2},
                }
            ],
        ),
        (condecimal(max_digits=4, decimal_places=1), Decimal('999'), Decimal('999')),
        (condecimal(max_digits=20, decimal_places=2), Decimal('742403889818000000'), Decimal('742403889818000000')),
        (condecimal(max_digits=20, decimal_places=2), Decimal('7.42403889818E+17'), Decimal('7.42403889818E+17')),
        (
            condecimal(max_digits=20, decimal_places=2),
            Decimal('7424742403889818000000'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 20 digits in total',
                    'type': 'value_error.decimal.max_digits',
                    'ctx': {'max_digits': 20},
                }
            ],
        ),
        (condecimal(max_digits=5, decimal_places=2), Decimal('7304E-1'), Decimal('7304E-1')),
        (
            condecimal(max_digits=5, decimal_places=2),
            Decimal('7304E-3'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 2 decimal places',
                    'type': 'value_error.decimal.max_places',
                    'ctx': {'decimal_places': 2},
                }
            ],
        ),
        (condecimal(max_digits=5, decimal_places=5), Decimal('70E-5'), Decimal('70E-5')),
        (
            condecimal(max_digits=5, decimal_places=5),
            Decimal('70E-6'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure that there are no more than 5 digits in total',
                    'type': 'value_error.decimal.max_digits',
                    'ctx': {'max_digits': 5},
                }
            ],
        ),
        *[
            (
                condecimal(decimal_places=2, max_digits=10),
                value,
                [{'loc': ('foo',), 'msg': 'value is not a valid decimal', 'type': 'value_error.decimal.not_finite'}],
            )
            for value in (
                'NaN',
                '-NaN',
                '+NaN',
                'sNaN',
                '-sNaN',
                '+sNaN',
                'Inf',
                '-Inf',
                '+Inf',
                'Infinity',
                '-Infinity',
                '-Infinity',
            )
        ],
        *[
            (
                condecimal(decimal_places=2, max_digits=10),
                Decimal(value),
                [{'loc': ('foo',), 'msg': 'value is not a valid decimal', 'type': 'value_error.decimal.not_finite'}],
            )
            for value in (
                'NaN',
                '-NaN',
                '+NaN',
                'sNaN',
                '-sNaN',
                '+sNaN',
                'Inf',
                '-Inf',
                '+Inf',
                'Infinity',
                '-Infinity',
                '-Infinity',
            )
        ],
        (
            condecimal(multiple_of=Decimal('5')),
            Decimal('42'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'ensure this value is a multiple of 5',
                    'type': 'value_error.number.not_multiple',
                    'ctx': {'multiple_of': Decimal('5')},
                }
            ],
        ),
    ],
)
def test_decimal_validation(type_, value, result):
    model = create_model('DecimalModel', foo=(type_, ...))

    if not isinstance(result, Decimal):
        with pytest.raises(ValidationError) as exc_info:
            model(foo=value)
        assert exc_info.value.errors() == result
        assert exc_info.value.json().startswith('[')
    else:
        assert model(foo=value).foo == result


@pytest.mark.parametrize('value,result', (('/test/path', Path('/test/path')), (Path('/test/path'), Path('/test/path'))))
def test_path_validation_success(value, result):
    class Model(BaseModel):
        foo: Path

    assert Model(foo=value).foo == result


def test_path_validation_fails():
    class Model(BaseModel):
        foo: Path

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=123)
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'value is not a valid path', 'type': 'type_error.path'}]


@pytest.mark.parametrize(
    'value,result',
    (('tests/test_types.py', Path('tests/test_types.py')), (Path('tests/test_types.py'), Path('tests/test_types.py'))),
)
def test_file_path_validation_success(value, result):
    class Model(BaseModel):
        foo: FilePath

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value,errors',
    (
        (
            'nonexistentfile',
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentfile" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentfile'},
                }
            ],
        ),
        (
            Path('nonexistentfile'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentfile" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentfile'},
                }
            ],
        ),
        (
            'tests',
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests" does not point to a file',
                    'type': 'value_error.path.not_a_file',
                    'ctx': {'path': 'tests'},
                }
            ],
        ),
        (
            Path('tests'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests" does not point to a file',
                    'type': 'value_error.path.not_a_file',
                    'ctx': {'path': 'tests'},
                }
            ],
        ),
    ),
)
def test_file_path_validation_fails(value, errors):
    class Model(BaseModel):
        foo: FilePath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors() == errors


@pytest.mark.parametrize('value,result', (('tests', Path('tests')), (Path('tests'), Path('tests'))))
def test_directory_path_validation_success(value, result):
    class Model(BaseModel):
        foo: DirectoryPath

    assert Model(foo=value).foo == result


@pytest.mark.skipif(sys.platform.startswith('win'), reason='paths look different on windows')
@pytest.mark.parametrize(
    'value,errors',
    (
        (
            'nonexistentdirectory',
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentdirectory" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentdirectory'},
                }
            ],
        ),
        (
            Path('nonexistentdirectory'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'file or directory at path "nonexistentdirectory" does not exist',
                    'type': 'value_error.path.not_exists',
                    'ctx': {'path': 'nonexistentdirectory'},
                }
            ],
        ),
        (
            'tests/test_types.py',
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests/test_types.py" does not point to a directory',
                    'type': 'value_error.path.not_a_directory',
                    'ctx': {'path': 'tests/test_types.py'},
                }
            ],
        ),
        (
            Path('tests/test_types.py'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'path "tests/test_types.py" does not point to a directory',
                    'type': 'value_error.path.not_a_directory',
                    'ctx': {'path': 'tests/test_types.py'},
                }
            ],
        ),
    ),
)
def test_directory_path_validation_fails(value, errors):
    class Model(BaseModel):
        foo: DirectoryPath

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors() == errors


base_message = r'.*ensure this value is {msg} \(type=value_error.number.not_{ty}; limit_value={value}\).*'


def test_number_gt():
    class Model(BaseModel):
        a: conint(gt=-1) = 0

    assert Model(a=0).dict() == {'a': 0}

    message = base_message.format(msg='greater than -1', ty='gt', value=-1)
    with pytest.raises(ValidationError, match=message):
        Model(a=-1)


def test_number_ge():
    class Model(BaseModel):
        a: conint(ge=0) = 0

    assert Model(a=0).dict() == {'a': 0}

    message = base_message.format(msg='greater than or equal to 0', ty='ge', value=0)
    with pytest.raises(ValidationError, match=message):
        Model(a=-1)


def test_number_lt():
    class Model(BaseModel):
        a: conint(lt=5) = 0

    assert Model(a=4).dict() == {'a': 4}

    message = base_message.format(msg='less than 5', ty='lt', value=5)
    with pytest.raises(ValidationError, match=message):
        Model(a=5)


def test_number_le():
    class Model(BaseModel):
        a: conint(le=5) = 0

    assert Model(a=5).dict() == {'a': 5}

    message = base_message.format(msg='less than or equal to 5', ty='le', value=5)
    with pytest.raises(ValidationError, match=message):
        Model(a=6)


@pytest.mark.parametrize('value', ((10), (100), (20)))
def test_number_multiple_of_int_valid(value):
    class Model(BaseModel):
        a: conint(multiple_of=5)

    assert Model(a=value).dict() == {'a': value}


@pytest.mark.parametrize('value', ((1337), (23), (6), (14)))
def test_number_multiple_of_int_invalid(value):
    class Model(BaseModel):
        a: conint(multiple_of=5)

    multiple_message = base_message.replace('limit_value', 'multiple_of')
    message = multiple_message.format(msg='a multiple of 5', ty='multiple', value=5)
    with pytest.raises(ValidationError, match=message):
        Model(a=value)


@pytest.mark.parametrize('value', ((0.2), (0.3), (0.4), (0.5), (1)))
def test_number_multiple_of_float_valid(value):
    class Model(BaseModel):
        a: confloat(multiple_of=0.1)

    assert Model(a=value).dict() == {'a': value}


@pytest.mark.parametrize('value', ((0.07), (1.27), (1.003)))
def test_number_multiple_of_float_invalid(value):
    class Model(BaseModel):
        a: confloat(multiple_of=0.1)

    multiple_message = base_message.replace('limit_value', 'multiple_of')
    message = multiple_message.format(msg='a multiple of 0.1', ty='multiple', value=0.1)
    with pytest.raises(ValidationError, match=message):
        Model(a=value)


@pytest.mark.parametrize('fn', [conint, confloat, condecimal])
def test_bounds_config_exceptions(fn):
    with pytest.raises(ConfigError):
        fn(gt=0, ge=0)

    with pytest.raises(ConfigError):
        fn(lt=0, le=0)


def test_new_type_success():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', List[int])

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    m = Model(a=42, b=24, c=[1, 2, 3])
    assert m.dict() == {'a': 42, 'b': 24, 'c': [1, 2, 3]}
    assert repr(Model.__fields__['c']) == "ModelField(name='c', type=List[int], required=True)"


def test_new_type_fails():
    a_type = NewType('a_type', int)
    b_type = NewType('b_type', a_type)
    c_type = NewType('c_type', List[int])

    class Model(BaseModel):
        a: a_type
        b: b_type
        c: c_type

    with pytest.raises(ValidationError) as exc_info:
        Model(a='foo', b='bar', c=['foo'])
    assert exc_info.value.errors() == [
        {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('b',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('c', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_valid_simple_json():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = '{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).dict() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_invalid_simple_json():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = '{a: 1, b: [2, 3]}'
    with pytest.raises(ValidationError) as exc_info:
        JsonModel(json_obj=obj)
    assert exc_info.value.errors()[0] == {'loc': ('json_obj',), 'msg': 'Invalid JSON', 'type': 'value_error.json'}


def test_valid_simple_json_bytes():
    class JsonModel(BaseModel):
        json_obj: Json

    obj = b'{"a": 1, "b": [2, 3]}'
    assert JsonModel(json_obj=obj).dict() == {'json_obj': {'a': 1, 'b': [2, 3]}}


def test_valid_detailed_json():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = '[1, 2, 3]'
    assert JsonDetailedModel(json_obj=obj).dict() == {'json_obj': [1, 2, 3]}


def test_invalid_detailed_json_value_error():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = '(1, 2, 3)'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    assert exc_info.value.errors()[0] == {'loc': ('json_obj',), 'msg': 'Invalid JSON', 'type': 'value_error.json'}


def test_valid_detailed_json_bytes():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = b'[1, 2, 3]'
    assert JsonDetailedModel(json_obj=obj).dict() == {'json_obj': [1, 2, 3]}


def test_invalid_detailed_json_type_error():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = '["a", "b", "c"]'
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    assert exc_info.value.errors() == [
        {'loc': ('json_obj', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('json_obj', 1), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
        {'loc': ('json_obj', 2), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]


def test_json_not_str():
    class JsonDetailedModel(BaseModel):
        json_obj: Json[List[int]]

    obj = 12
    with pytest.raises(ValidationError) as exc_info:
        JsonDetailedModel(json_obj=obj)
    assert exc_info.value.errors()[0] == {
        'loc': ('json_obj',),
        'msg': 'JSON object must be str, bytes or bytearray',
        'type': 'type_error.json',
    }


def test_json_pre_validator():
    call_count = 0

    class JsonModel(BaseModel):
        json_obj: Json

        @validator('json_obj', pre=True)
        def check(cls, v):
            assert v == '"foobar"'
            nonlocal call_count
            call_count += 1
            return v

    assert JsonModel(json_obj='"foobar"').dict() == {'json_obj': 'foobar'}
    assert call_count == 1


def test_json_optional_simple():
    class JsonOptionalModel(BaseModel):
        json_obj: Optional[Json]

    assert JsonOptionalModel(json_obj=None).dict() == {'json_obj': None}
    assert JsonOptionalModel(json_obj='["x", "y", "z"]').dict() == {'json_obj': ['x', 'y', 'z']}


def test_json_optional_complex():
    class JsonOptionalModel(BaseModel):
        json_obj: Optional[Json[List[int]]]

    JsonOptionalModel(json_obj=None)

    good = JsonOptionalModel(json_obj='[1, 2, 3]')
    assert good.json_obj == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        JsonOptionalModel(json_obj='["i should fail"]')
    assert exc_info.value.errors() == [
        {'loc': ('json_obj', 0), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_json_explicitly_required():
    class JsonRequired(BaseModel):
        json_obj: Json = ...

    assert JsonRequired(json_obj=None).dict() == {'json_obj': None}
    assert JsonRequired(json_obj='["x", "y", "z"]').dict() == {'json_obj': ['x', 'y', 'z']}
    with pytest.raises(ValidationError) as exc_info:
        JsonRequired()
    assert exc_info.value.errors() == [{'loc': ('json_obj',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_json_no_default():
    class JsonRequired(BaseModel):
        json_obj: Json

    assert JsonRequired(json_obj=None).dict() == {'json_obj': None}
    assert JsonRequired(json_obj='["x", "y", "z"]').dict() == {'json_obj': ['x', 'y', 'z']}
    assert JsonRequired().dict() == {'json_obj': None}


def test_pattern():
    class Foobar(BaseModel):
        pattern: Pattern

    f = Foobar(pattern=r'^whatev.r\d$')
    # SRE_Pattern for 3.6, Pattern for 3.7
    assert f.pattern.__class__.__name__ in {'SRE_Pattern', 'Pattern'}
    # check it's really a proper pattern
    assert f.pattern.match('whatever1')
    assert not f.pattern.match(' whatever1')

    # Check that pre-compiled patterns are accepted unchanged
    p = re.compile(r'^whatev.r\d$')
    f2 = Foobar(pattern=p)
    assert f2.pattern is p

    assert Foobar.schema() == {
        'type': 'object',
        'title': 'Foobar',
        'properties': {'pattern': {'type': 'string', 'format': 'regex', 'title': 'Pattern'}},
        'required': ['pattern'],
    }


def test_pattern_error():
    class Foobar(BaseModel):
        pattern: Pattern

    with pytest.raises(ValidationError) as exc_info:
        Foobar(pattern='[xx')
    assert exc_info.value.errors() == [
        {'loc': ('pattern',), 'msg': 'Invalid regular expression', 'type': 'value_error.regex_pattern'}
    ]


def test_secretstr():
    class Foobar(BaseModel):
        password: SecretStr
        empty_password: SecretStr

    # Initialize the model.
    f = Foobar(password='1234', empty_password='')

    # Assert correct types.
    assert f.password.__class__.__name__ == 'SecretStr'
    assert f.empty_password.__class__.__name__ == 'SecretStr'

    # Assert str and repr are correct.
    assert str(f.password) == '**********'
    assert str(f.empty_password) == ''
    assert repr(f.password) == "SecretStr('**********')"
    assert repr(f.empty_password) == "SecretStr('')"

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == '1234'
    assert f.empty_password.get_secret_value() == ''

    with pytest.warns(DeprecationWarning, match=r'`secret_str.display\(\)` is deprecated'):
        assert f.password.display() == '**********'
    with pytest.warns(DeprecationWarning, match=r'`secret_str.display\(\)` is deprecated'):
        assert f.empty_password.display() == ''

    # Assert that SecretStr is equal to SecretStr if the secret is the same.
    assert f == f.copy()
    assert f != f.copy(update=dict(password='4321'))


def test_secretstr_equality():
    assert SecretStr('abc') == SecretStr('abc')
    assert SecretStr('123') != SecretStr('321')
    assert SecretStr('123') != '123'
    assert SecretStr('123') is not SecretStr('123')


def test_secretstr_idempotent():
    class Foobar(BaseModel):
        password: SecretStr

    # Should not raise an exception
    m = Foobar(password=SecretStr('1234'))
    assert m.password.get_secret_value() == '1234'


def test_secretstr_error():
    class Foobar(BaseModel):
        password: SecretStr

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=[6, 23, 'abc'])
    assert exc_info.value.errors() == [{'loc': ('password',), 'msg': 'str type expected', 'type': 'type_error.str'}]


def test_secretbytes():
    class Foobar(BaseModel):
        password: SecretBytes
        empty_password: SecretBytes

    # Initialize the model.
    f = Foobar(password=b'wearebytes', empty_password=b'')

    # Assert correct types.
    assert f.password.__class__.__name__ == 'SecretBytes'
    assert f.empty_password.__class__.__name__ == 'SecretBytes'

    # Assert str and repr are correct.
    assert str(f.password) == '**********'
    assert str(f.empty_password) == ''
    assert repr(f.password) == "SecretBytes(b'**********')"
    assert repr(f.empty_password) == "SecretBytes(b'')"

    # Assert retrieval of secret value is correct
    assert f.password.get_secret_value() == b'wearebytes'
    assert f.empty_password.get_secret_value() == b''

    with pytest.warns(DeprecationWarning, match=r'`secret_bytes.display\(\)` is deprecated'):
        assert f.password.display() == '**********'
    with pytest.warns(DeprecationWarning, match=r'`secret_bytes.display\(\)` is deprecated'):
        assert f.empty_password.display() == ''

    # Assert that SecretBytes is equal to SecretBytes if the secret is the same.
    assert f == f.copy()
    assert f != f.copy(update=dict(password=b'4321'))


def test_secretbytes_equality():
    assert SecretBytes(b'abc') == SecretBytes(b'abc')
    assert SecretBytes(b'123') != SecretBytes(b'321')
    assert SecretBytes(b'123') != b'123'
    assert SecretBytes(b'123') is not SecretBytes(b'123')


def test_secretbytes_idempotent():
    class Foobar(BaseModel):
        password: SecretBytes

    # Should not raise an exception.
    _ = Foobar(password=SecretBytes(b'1234'))


def test_secretbytes_error():
    class Foobar(BaseModel):
        password: SecretBytes

    with pytest.raises(ValidationError) as exc_info:
        Foobar(password=[6, 23, 'abc'])
    assert exc_info.value.errors() == [{'loc': ('password',), 'msg': 'byte type expected', 'type': 'type_error.bytes'}]


def test_generic_without_params():
    class Model(BaseModel):
        generic_list: List
        generic_dict: Dict

    m = Model(generic_list=[0, 'a'], generic_dict={0: 'a', 'a': 0})
    assert m.dict() == {'generic_list': [0, 'a'], 'generic_dict': {0: 'a', 'a': 0}}


def test_generic_without_params_error():
    class Model(BaseModel):
        generic_list: List
        generic_dict: Dict

    with pytest.raises(ValidationError) as exc_info:
        Model(generic_list=0, generic_dict=0)
    assert exc_info.value.errors() == [
        {'loc': ('generic_list',), 'msg': 'value is not a valid list', 'type': 'type_error.list'},
        {'loc': ('generic_dict',), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'},
    ]


@pytest.mark.skipif(not typing_extensions, reason='typing_extensions not installed')
def test_literal_single():
    class Model(BaseModel):
        a: typing_extensions.Literal['a']

    Model(a='a')
    with pytest.raises(ValidationError) as exc_info:
        Model(a='b')
    assert exc_info.value.errors() == [
        {
            'loc': ('a',),
            'msg': "unexpected value; permitted: 'a'",
            'type': 'value_error.const',
            'ctx': {'given': 'b', 'permitted': ('a',)},
        }
    ]


@pytest.mark.skipif(not typing_extensions, reason='typing_extensions not installed')
def test_literal_multiple():
    class Model(BaseModel):
        a_or_b: typing_extensions.Literal['a', 'b']

    Model(a_or_b='a')
    Model(a_or_b='b')
    with pytest.raises(ValidationError) as exc_info:
        Model(a_or_b='c')
    assert exc_info.value.errors() == [
        {
            'loc': ('a_or_b',),
            'msg': "unexpected value; permitted: 'a', 'b'",
            'type': 'value_error.const',
            'ctx': {'given': 'c', 'permitted': ('a', 'b')},
        }
    ]


def test_unsupported_field_type():
    with pytest.raises(TypeError, match=r'MutableSet(.*)not supported'):

        class UnsupportedModel(BaseModel):
            unsupported: MutableSet[int]


def test_frozenset_field():
    class FrozenSetModel(BaseModel):
        set: FrozenSet[int]

    test_set = frozenset({1, 2, 3})
    object_under_test = FrozenSetModel(set=test_set)

    assert object_under_test.set == test_set


def test_frozenset_field_conversion():
    class FrozenSetModel(BaseModel):
        set: FrozenSet[int]

    test_list = [1, 2, 3]
    test_set = frozenset(test_list)
    object_under_test = FrozenSetModel(set=test_list)

    assert object_under_test.set == test_set


def test_frozenset_field_not_convertible():
    class FrozenSetModel(BaseModel):
        set: FrozenSet[int]

    with pytest.raises(ValidationError, match=r'frozenset'):
        FrozenSetModel(set=42)


@pytest.mark.parametrize(
    'input_value,output,human_bin,human_dec',
    (
        ('1', 1, '1.0B', '1.0B'),
        ('1.0', 1, '1.0B', '1.0B'),
        ('1b', 1, '1.0B', '1.0B'),
        ('1.5 KB', int(1.5e3), '1.5KiB', '1.5KB'),
        ('1.5 K', int(1.5e3), '1.5KiB', '1.5KB'),
        ('1.5 MB', int(1.5e6), '1.4MiB', '1.5MB'),
        ('1.5 M', int(1.5e6), '1.4MiB', '1.5MB'),
        ('5.1kib', 5222, '5.1KiB', '5.2KB'),
        ('6.2EiB', 7148113328562451456, '6.2EiB', '7.1EB'),
    ),
)
def test_bytesize_conversions(input_value, output, human_bin, human_dec):
    class Model(BaseModel):
        size: ByteSize

    m = Model(size=input_value)

    assert m.size == output

    assert m.size.human_readable() == human_bin
    assert m.size.human_readable(decimal=True) == human_dec


def test_bytesize_to():
    class Model(BaseModel):
        size: ByteSize

    m = Model(size='1GiB')

    assert m.size.to('MiB') == pytest.approx(1024)
    assert m.size.to('MB') == pytest.approx(1073.741824)
    assert m.size.to('TiB') == pytest.approx(0.0009765625)


def test_bytesize_raises():
    class Model(BaseModel):
        size: ByteSize

    with pytest.raises(ValidationError, match='parse value'):
        Model(size='d1MB')

    with pytest.raises(ValidationError, match='byte unit'):
        Model(size='1LiB')

    # 1Gi is not a valid unit unlike 1G
    with pytest.raises(ValidationError, match='byte unit'):
        Model(size='1Gi')

    m = Model(size='1MB')
    with pytest.raises(errors.InvalidByteSizeUnit, match='byte unit'):
        m.size.to('bad_unit')
