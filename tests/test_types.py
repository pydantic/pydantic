import os
import uuid
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from uuid import UUID

import pytest

from pydantic import (DSN, UUID1, UUID3, UUID4, UUID5, BaseModel, EmailStr, NameEmail, NegativeFloat, NegativeInt,
                      PositiveFloat, PositiveInt, PyObject, StrictStr, ValidationError, condecimal, confloat, conint,
                      constr, create_model)

try:
    import email_validator
except ImportError:
    email_validator = None


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
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v',),
            'msg': 'length greater than maximum allowed: 10',
            'type': 'value_error',
        },
    ]


class DsnModel(BaseModel):
    db_name = 'foobar'
    db_user = 'postgres'
    db_password: str = None
    db_host = 'localhost'
    db_port = '5432'
    db_driver = 'postgres'
    db_query: dict = None
    dsn: DSN = None


def test_dsn_compute():
    m = DsnModel()
    assert m.dsn == 'postgres://postgres@localhost:5432/foobar'


def test_dsn_define():
    m = DsnModel(dsn='postgres://postgres@localhost:5432/different')
    assert m.dsn == 'postgres://postgres@localhost:5432/different'


def test_dsn_pw_host():
    m = DsnModel(db_password='pword', db_host='before:after', db_query={'v': 1})
    assert m.dsn == 'postgres://postgres:pword@[before:after]:5432/foobar?v=1'


def test_dsn_no_driver():
    with pytest.raises(ValidationError) as exc_info:
        DsnModel(db_driver=None)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('db_driver',),
            'msg': 'None is not an allow value',
            'type': 'type_error',
        },
        {
            'loc': ('dsn',),
            'msg': '"db_driver" field may not be missing or None',
            'type': 'value_error',
        },
    ]


class PyObjectModel(BaseModel):
    module: PyObject = 'os.path'


def test_module_import():
    m = PyObjectModel()
    assert m.module == os.path
    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(module='foobar')
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('module',),
            'msg': '"foobar" doesn\'t look like a module path',
            'type': 'value_error',
        },
    ]


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
        max_number_size = 100


@pytest.mark.parametrize('field,value,result', [
    ('bool_check', True, True),
    ('bool_check', False, False),
    ('bool_check', None, False),
    ('bool_check', '', False),
    ('bool_check', 1, True),
    ('bool_check', 'TRUE', True),
    ('bool_check', b'TRUE', True),
    ('bool_check', 'true', True),
    ('bool_check', '1', True),
    ('bool_check', '2', False),
    ('bool_check', 2, True),
    ('bool_check', 'on', True),
    ('bool_check', 'yes', True),

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
    ('int_check', 123, ValidationError),
    ('int_check', '123', ValidationError),
    ('int_check', b'123', ValidationError),

    ('float_check', 1, 1.0),
    ('float_check', 1.0, 1.0),
    ('float_check', '1.0', 1.0),
    ('float_check', '1', 1.0),
    ('float_check', b'1.0', 1.0),
    ('float_check', b'1', 1.0),
    ('float_check', 123, ValidationError),
    ('float_check', '123', ValidationError),
    ('float_check', b'123', ValidationError),

    ('uuid_check', 'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
    ('uuid_check', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
    ('uuid_check', b'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
    ('uuid_check', 'ebcdab58-6eb8-46fb-a190-', ValidationError),
    ('uuid_check', 123, ValidationError),

    ('decimal_check', 42.24, Decimal('42.24')),
    ('decimal_check', '42.24', Decimal('42.24')),
    ('decimal_check', b'42.24', Decimal('42.24')),
    ('decimal_check', '  42.24  ', Decimal('42.24')),
    ('decimal_check', Decimal('42.24'), Decimal('42.24')),
    ('decimal_check', 'not a valid decimal', ValidationError),
    ('decimal_check', 'NaN', ValidationError),
])
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
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('str_check',),
            'msg': 'length greater than maximum allowed: 10',
            'type': 'value_error',
        },
    ]


def test_string_too_short():
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x')
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('str_check',),
            'msg': 'length less than minimum allowed: 5',
            'type': 'value_error',
        },
    ]


class NumberModel(BaseModel):
    int_check: int
    float_check: float

    class Config:
        min_number_size = 5
        max_number_size = 10


def test_number_too_big():
    with pytest.raises(ValidationError) as exc_info:
        NumberModel(int_check=50, float_check=150)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('int_check',),
            'msg': 'size greater than maximum allowed: 10',
            'type': 'value_error',
        },
        {
            'loc': ('float_check',),
            'msg': 'size greater than maximum allowed: 10',
            'type': 'value_error',
        },
    ]


def test_number_too_small():
    with pytest.raises(ValidationError) as exc_info:
        NumberModel(int_check=1, float_check=2.5)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('int_check',),
            'msg': 'size less than minimum allowed: 5',
            'type': 'value_error',
        },
        {
            'loc': ('float_check',),
            'msg': 'size less than minimum allowed: 5',
            'type': 'value_error',
        },
    ]


class DatetimeModel(BaseModel):
    dt: datetime = ...
    date_: date = ...
    time_: time = ...
    duration: timedelta = ...


def test_datetime_successful():
    m = DatetimeModel(
        dt='2017-10-5T19:47:07',
        date_=1494012000,
        time_='10:20:30.400',
        duration='15:30.0001',
    )
    assert m.dt == datetime(2017, 10, 5, 19, 47, 7)
    assert m.date_ == date(2017, 5, 5)
    assert m.time_ == time(10, 20, 30, 400000)
    assert m.duration == timedelta(minutes=15, seconds=30, microseconds=100)


def test_datetime_errors():
    with pytest.raises(ValueError) as exc_info:
        DatetimeModel(
            dt='2017-13-5T19:47:07',
            date_='XX1494012000',
            time_='25:20:30.400',
            duration='15:30.0001 broken',
        )
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('dt',),
            'msg': 'month must be in 1..12',
            'type': 'value_error',
        },
        {
            'loc': ('date_',),
            'msg': 'Invalid date format',
            'type': 'value_error',
        },
        {
            'loc': ('time_',),
            'msg': 'hour must be in 0..23',
            'type': 'value_error',
        },
        {
            'loc': ('duration',),
            'msg': 'Invalid duration format',
            'type': 'value_error',
        },
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
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('tool',),
            'msg': '3 is not a valid ToolEnum',
            'type': 'value_error',
        }
    ]


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_success():
    class MoreStringsModel(BaseModel):
        str_strip_enabled: constr(strip_whitespace=True)
        str_strip_disabled: constr(strip_whitespace=False)
        str_regex: constr(regex=r'^xxx\d{3}$') = ...
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
    assert repr(m.name_email) == '<NameEmail("foo bar <foobar@example.com>")>'
    assert m.name_email.name == 'foo bar'
    assert m.name_email.email == 'foobar@example.com'


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_fails():
    class MoreStringsModel(BaseModel):
        str_regex: constr(regex=r'^xxx\d{3}$') = ...
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
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('str_regex',),
            'msg': 'string does not match regex "^xxx\\d{3}$"',
            'type': 'value_error',
        },
        {
            'loc': ('str_min_length',),
            'msg': 'length less than minimum allowed: 5',
            'type': 'value_error',
        },
        {
            'loc': ('str_email',),
            'msg': 'The email address contains invalid characters before the @-sign: <.',
            'type': 'value_error.email_not_valid_error.email_syntax_error',
        },
        {
            'loc': ('name_email',),
            'msg': 'The email address contains invalid characters before the @-sign:  .',
            'type': 'value_error.email_not_valid_error.email_syntax_error',
        },
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


class ListDictTupleModel(BaseModel):
    a: dict = None
    b: list = None
    c: OrderedDict = None
    d: tuple = None


def test_dict():
    assert ListDictTupleModel(a={1: 10, 2: 20}).a == {1: 10, 2: 20}
    assert ListDictTupleModel(a=[(1, 2), (3, 4)]).a == {1: 2, 3: 4}

    with pytest.raises(ValidationError) as exc_info:
        ListDictTupleModel(a=[1, 2, 3])
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('a',),
            'msg': 'value is not a valid dict, got list',
            'type': 'type_error',
        },
    ]


def test_list():
    m = ListDictTupleModel(b=[1, 2, '3'])
    assert m.a is None
    assert m.b == [1, 2, '3']
    assert ListDictTupleModel(b='xyz').b == ['x', 'y', 'z']
    assert ListDictTupleModel(b=(i**2 for i in range(5))).b == [0, 1, 4, 9, 16]

    with pytest.raises(ValidationError) as exc_info:
        ListDictTupleModel(b=1)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('b',),
            'msg': '\'int\' object is not iterable',
            'type': 'type_error',
        },
    ]


def test_ordered_dict():
    assert ListDictTupleModel(c=OrderedDict([(1, 10), (2, 20)])).c == OrderedDict([(1, 10), (2, 20)])
    assert ListDictTupleModel(c={1: 10, 2: 20}).c in (OrderedDict([(1, 10), (2, 20)]), OrderedDict([(2, 20), (1, 10)]))
    assert ListDictTupleModel(c=[(1, 2), (3, 4)]).c == OrderedDict([(1, 2), (3, 4)])

    with pytest.raises(ValidationError) as exc_info:
        ListDictTupleModel(c=[1, 2, 3])
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('c',),
            'msg': '\'int\' object is not iterable',
            'type': 'type_error',
        },
    ]


def test_tuple():
    m = ListDictTupleModel(d=(1, 2, '3'))
    assert m.a is None
    assert m.d == (1, 2, '3')
    assert m.dict() == {'a': None, 'b': None, 'c': None, 'd': (1, 2, '3')}
    assert ListDictTupleModel(d='xyz').d == ('x', 'y', 'z')
    assert ListDictTupleModel(d=(i**2 for i in range(5))).d == (0, 1, 4, 9, 16)

    with pytest.raises(ValidationError) as exc_info:
        ListDictTupleModel(d=1)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('d',),
            'msg': '\'int\' object is not iterable',
            'type': 'type_error',
        },
    ]


class IntModel(BaseModel):
    a: PositiveInt = None
    b: NegativeInt = None
    c: conint(gt=4, lt=10) = None


def test_int_validation():
    m = IntModel(a=5, b=-5, c=5)
    assert m == {'a': 5, 'b': -5, 'c': 5}

    with pytest.raises(ValidationError) as exc_info:
        IntModel(a=-5, b=5, c=-5)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('a',),
            'msg': 'size less than minimum allowed: 0',
            'type': 'value_error',
        },
        {
            'loc': ('b',),
            'msg': 'size greater than maximum allowed: 0',
            'type': 'value_error',
        },
        {
            'loc': ('c',),
            'msg': 'size less than minimum allowed: 4',
            'type': 'value_error',
        },
    ]


class FloatModel(BaseModel):
    a: PositiveFloat = None
    b: NegativeFloat = None
    c: confloat(gt=4, lt=12.2) = None


def test_float_validation():
    m = FloatModel(a=5.1, b=-5.2, c=5.3)
    assert m == {'a': 5.1, 'b': -5.2, 'c': 5.3}

    with pytest.raises(ValidationError) as exc_info:
        FloatModel(a=-5.1, b=5.2, c=-5.3)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('a',),
            'msg': 'size less than minimum allowed: 0',
            'type': 'value_error',
        },
        {
            'loc': ('b',),
            'msg': 'size greater than maximum allowed: 0',
            'type': 'value_error',
        },
        {
            'loc': ('c',),
            'msg': 'size less than minimum allowed: 4',
            'type': 'value_error',
        },
    ]


def test_set():
    class SetModel(BaseModel):
        v: set = ...

    m = SetModel(v=[1, 2, 3])
    assert m.v == {1, 2, 3}
    assert m.dict() == {'v': {1, 2, 3}}
    assert SetModel(v={'a', 'b', 'c'}).v == {'a', 'b', 'c'}


def test_strict_str():
    class Model(BaseModel):
        v: StrictStr

    assert Model(v='foobar').v == 'foobar'

    with pytest.raises(ValidationError):
        Model(v=123)

    with pytest.raises(ValidationError):
        Model(v=b'foobar')


def test_uuid_error():
    class Model(BaseModel):
        v: UUID

    with pytest.raises(ValidationError) as exc_info:
        Model(v='ebcdab58-6eb8-46fb-a190-d07a3')
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('v',),
            'msg': 'badly formed hexadecimal UUID string',
            'type': 'value_error',
        },
    ]

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
    assert m.dict() == {
        'a': a,
        'b': b,
        'c': c,
        'd': d,
    }

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=d, b=c, c=b, d=a)
    assert exc_info.value.flatten_errors() == [
        {
            'loc': ('a',),
            'msg': 'uuid version 1 expected, not 5',
            'type': 'value_error',
        },
        {
            'loc': ('b',),
            'msg': 'uuid version 3 expected, not 4',
            'type': 'value_error',
        },
        {
            'loc': ('c',),
            'msg': 'uuid version 4 expected, not 3',
            'type': 'value_error',
        },
        {
            'loc': ('d',),
            'msg': 'uuid version 5 expected, not 1',
            'type': 'value_error',
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


@pytest.mark.parametrize('type_,value,result', [
    (condecimal(gt=Decimal('42.24')), Decimal('43'), Decimal('43')),
    (condecimal(gt=Decimal('42.24')), Decimal('42'), ValidationError),
    (condecimal(lt=Decimal('42.24')), Decimal('42'), Decimal('42')),
    (condecimal(lt=Decimal('42.24')), Decimal('43'), ValidationError),
    (condecimal(max_digits=2, decimal_places=2), Decimal('0.99'), Decimal('0.99')),
    (condecimal(max_digits=2, decimal_places=1), Decimal('0.99'), ValidationError),
    (condecimal(max_digits=3, decimal_places=1), Decimal('999'), ValidationError),
    (condecimal(max_digits=4, decimal_places=1), Decimal('999'), Decimal('999')),
    (condecimal(max_digits=20, decimal_places=2), Decimal('742403889818000000'), Decimal('742403889818000000')),
    (condecimal(max_digits=20, decimal_places=2), Decimal('7.42403889818E+17'), Decimal('7.42403889818E+17')),
    (condecimal(max_digits=20, decimal_places=2), Decimal('7424742403889818000000'), ValidationError),
    (condecimal(max_digits=5, decimal_places=2), Decimal('7304E-1'), Decimal('7304E-1')),
    (condecimal(max_digits=5, decimal_places=2), Decimal('7304E-3'), ValidationError),
    (condecimal(max_digits=5, decimal_places=5), Decimal('70E-5'), Decimal('70E-5')),
    (condecimal(max_digits=5, decimal_places=5), Decimal('70E-6'), ValidationError),
    *[
        (condecimal(decimal_places=2, max_digits=10), Decimal(value), ValidationError)
        for value in (
            'NaN', '-NaN', '+NaN', 'sNaN', '-sNaN', '+sNaN',
            'Inf', '-Inf', '+Inf', 'Infinity', '-Infinity', '-Infinity',
        )
    ],
])
def test_decimal_validation(type_, value, result):
    model = create_model('DecimalModel', foo=(type_, ...))
    kwargs = {'foo': value}

    if result == ValidationError:
        with pytest.raises(ValidationError):
            model(**kwargs)
    else:
        assert model(**kwargs).dict()['foo'] == result
