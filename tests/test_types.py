import os
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum
from uuid import UUID

import pytest

from pydantic import (DSN, BaseModel, EmailStr, NameEmail, NegativeInt, PositiveInt, PyObject, StrictStr,
                      ValidationError, conint, constr)

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
    assert """\
{
  "v": {
    "error_msg": "length greater than maximum allowed: 10",
    "error_type": "ValueError",
    "track": "ConstrainedStrValue"
  }
}""" == exc_info.value.json(2)


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
    assert '"db_driver" field may not be missing or None' in str(exc_info.value)


class PyObjectModel(BaseModel):
    module: PyObject = 'os.path'


def test_module_import():
    m = PyObjectModel()
    assert m.module == os.path
    with pytest.raises(ValidationError) as exc_info:
        PyObjectModel(module='foobar')
    assert '"foobar" doesn\'t look like a module path' in str(exc_info.value)


class CheckModel(BaseModel):
    bool_check = True
    str_check = 's'
    bytes_check = b's'
    int_check = 1
    float_check = 1.0
    uuid_check: UUID = UUID('7bd00d58-6485-4ca6-b889-3da6d8df3ee4')

    class Config:
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
    ('str_check', b's', 's'),
    ('str_check', 1, '1'),
    ('str_check', 'x' * 11, ValidationError),
    ('str_check', b'x' * 11, ValidationError),

    ('bytes_check', 's', b's'),
    ('bytes_check', b's', b's'),
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
])
def test_default_validators(field, value, result):
    kwargs = {field: value}
    if result == ValidationError:
        with pytest.raises(ValidationError):
            CheckModel(**kwargs)
    else:
        assert CheckModel(**kwargs).dict()[field] == result


def test_string_too_long():
    with pytest.raises(ValidationError) as exc_info:
        CheckModel(str_check='x' * 150)
    assert 'length 150 not in range 0 to 10 (error_type=ValueError track=str)' in exc_info.value.display_errors


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
    assert exc_info.value.message == '4 errors validating input'
    assert """\
{
  "date_": {
    "error_msg": "Invalid date format",
    "error_type": "ValueError",
    "track": "date"
  },
  "dt": {
    "error_msg": "month must be in 1..12",
    "error_type": "ValueError",
    "track": "datetime"
  },
  "duration": {
    "error_msg": "Invalid duration format",
    "error_type": "ValueError",
    "track": "timedelta"
  },
  "time_": {
    "error_msg": "hour must be in 0..23",
    "error_type": "ValueError",
    "track": "time"
  }
}""" == exc_info.value.json(2)


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
    assert exc_info.value.message == 'error validating input'
    assert """\
{
  "tool": {
    "error_msg": "3 is not a valid ToolEnum",
    "error_type": "ValueError",
    "track": "ToolEnum"
  }
}""" == exc_info.value.json(2)


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_string_success():
    class MoreStringsModel(BaseModel):
        str_regex: constr(regex=r'^xxx\d{3}$') = ...
        str_min_length: constr(min_length=5) = ...
        str_curtailed: constr(curtail_length=5) = ...
        str_email: EmailStr = ...
        name_email: NameEmail = ...
    m = MoreStringsModel(
        str_regex='xxx123',
        str_min_length='12345',
        str_curtailed='123456',
        str_email='foobar@example.com  ',
        name_email='foo bar  <foobaR@example.com>',
    )
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
            str_regex='xxx123  ',
            str_min_length='1234',
            str_curtailed='123',  # doesn't fail
            str_email='foobar<@example.com',
            name_email='foobar @example.com',
        )
    assert exc_info.value.message == '4 errors validating input'
    assert """\
{
  "name_email": {
    "error_msg": "The email address contains invalid characters before the @-sign:  .",
    "error_type": "ValueError",
    "track": "NameEmail"
  },
  "str_email": {
    "error_msg": "The email address contains invalid characters before the @-sign: <.",
    "error_type": "ValueError",
    "track": "EmailStr"
  },
  "str_min_length": {
    "error_msg": "length less than minimum allowed: 5",
    "error_type": "ValueError",
    "track": "ConstrainedStrValue"
  },
  "str_regex": {
    "error_msg": "string does not match regex \\"^xxx\\\\d{3}$\\"",
    "error_type": "ValueError",
    "track": "ConstrainedStrValue"
  }
}""" == exc_info.value.json(2)


@pytest.mark.skipif(email_validator, reason='email_validator is installed')
def test_email_validator_not_installed():
    with pytest.raises(ImportError):
        class MoreStringsModel(BaseModel):
            str_email: EmailStr = ...


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
    assert 'value is not a valid dict, got list' in str(exc_info.value)


def test_list():
    m = ListDictTupleModel(b=[1, 2, '3'])
    assert m.a is None
    assert m.b == [1, 2, '3']
    assert ListDictTupleModel(b='xyz').b == ['x', 'y', 'z']
    assert ListDictTupleModel(b=(i**2 for i in range(5))).b == [0, 1, 4, 9, 16]
    with pytest.raises(ValidationError) as exc_info:
        ListDictTupleModel(b=1)
    assert "'int' object is not iterable" in str(exc_info.value)


def test_ordered_dict():
    assert ListDictTupleModel(c=OrderedDict([(1, 10), (2, 20)])).c == OrderedDict([(1, 10), (2, 20)])
    assert ListDictTupleModel(c={1: 10, 2: 20}).c in (OrderedDict([(1, 10), (2, 20)]), OrderedDict([(2, 20), (1, 10)]))
    assert ListDictTupleModel(c=[(1, 2), (3, 4)]).c == OrderedDict([(1, 2), (3, 4)])
    with pytest.raises(ValidationError) as exc_info:
        ListDictTupleModel(c=[1, 2, 3])
    assert "'int' object is not iterable" in str(exc_info.value)


def test_tuple():
    m = ListDictTupleModel(d=(1, 2, '3'))
    assert m.a is None
    assert m.d == (1, 2, '3')
    assert m.dict() == {'a': None, 'b': None, 'c': None, 'd': (1, 2, '3')}
    assert ListDictTupleModel(d='xyz').d == ('x', 'y', 'z')
    assert ListDictTupleModel(d=(i**2 for i in range(5))).d == (0, 1, 4, 9, 16)
    with pytest.raises(ValidationError) as exc_info:
        ListDictTupleModel(d=1)
    assert "'int' object is not iterable" in str(exc_info.value)


class IntModel(BaseModel):
    a: PositiveInt = None
    b: NegativeInt = None
    c: conint(gt=4, lt=10) = None


def test_int_validation():
    m = IntModel(a=5, b=-5, c=5)
    assert m == {'a': 5, 'b': -5, 'c': 5}
    with pytest.raises(ValidationError) as exc_info:
        IntModel(a=-5, b=5, c=-5)
    assert exc_info.value.message == '3 errors validating input'


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
    assert """\
error validating input
v:
  badly formed hexadecimal UUID string (error_type=ValueError track=UUID)""" == str(exc_info.value)

    with pytest.raises(ValidationError):
        Model(v=None)
