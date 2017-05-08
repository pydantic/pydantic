import os
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from enum import Enum, IntEnum

import pytest

from pydantic import (DSN, BaseModel, EmailStr, Module, NameEmail, NegativeInt, PositiveInt, ValidationError,
                      conint, constr)


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
    "index": null,
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
    assert '"\\"db_driver\\" field may not be missing or None"' in exc_info.value.args[0]


class ModuleModel(BaseModel):
    module: Module = 'os.path'


def test_module_import():
    m = ModuleModel()
    assert m.module == os.path


class CheckModel(BaseModel):
    bool_check = True
    str_check = 's'
    bytes_check = b's'
    int_check = 1
    float_check = 1.0

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
])
def test_default_validators(field, value, result):
    kwargs = {field: value}
    if result == ValidationError:
        with pytest.raises(ValidationError):
            CheckModel(**kwargs)
    else:
        assert CheckModel(**kwargs).values[field] == result


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
    "index": null,
    "track": "date"
  },
  "dt": {
    "error_msg": "month must be in 1..12",
    "error_type": "ValueError",
    "index": null,
    "track": "datetime"
  },
  "duration": {
    "error_msg": "Invalid duration format",
    "error_type": "ValueError",
    "index": null,
    "track": "timedelta"
  },
  "time_": {
    "error_msg": "hour must be in 0..23",
    "error_type": "ValueError",
    "index": null,
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
    assert exc_info.value.message == '1 error validating input'
    assert """\
{
  "tool": {
    "error_msg": "3 is not a valid ToolEnum",
    "error_type": "ValueError",
    "index": null,
    "track": "ToolEnum"
  }
}""" == exc_info.value.json(2)


class MoreStringsModel(BaseModel):
    str_regex: constr(regex=r'^xxx\d{3}$') = ...
    str_min_length: constr(min_length=5) = ...
    str_curtailed: constr(curtail_length=5) = ...
    str_email: EmailStr = ...
    name_email: NameEmail = ...


def test_string_success():
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
    assert m.name_email.name == 'foo bar'
    assert m.name_email.email == 'foobar@example.com'


def test_string_fails():
    with pytest.raises(ValidationError) as exc_info:
        MoreStringsModel(
            str_regex='xxx123  ',
            str_min_length='1234',
            str_curtailed='123',  # doesn't fail
            str_email='foobar\n@example.com',
            name_email='foobar @example.com',
        )
    assert exc_info.value.message == '4 errors validating input'
    assert """\
{
  "name_email": {
    "error_msg": "Email address is not valid",
    "error_type": "ValueError",
    "index": null,
    "track": "NameEmail"
  },
  "str_email": {
    "error_msg": "Email address is not valid",
    "error_type": "ValueError",
    "index": null,
    "track": "EmailStr"
  },
  "str_min_length": {
    "error_msg": "length less than minimum allowed: 5",
    "error_type": "ValueError",
    "index": null,
    "track": "ConstrainedStrValue"
  },
  "str_regex": {
    "error_msg": "string does not match regex \\"^xxx\\\\d{3}$\\"",
    "error_type": "ValueError",
    "index": null,
    "track": "ConstrainedStrValue"
  }
}""" == exc_info.value.json(2)


class ListDictModel(BaseModel):
    a: dict = None
    b: list = None
    c: OrderedDict = None


def test_dict():
    m = ListDictModel(a={1: 10, 2: 20})
    assert m.a == {1: 10, 2: 20}
    m = ListDictModel(a=[(1, 2), (3, 4)])
    assert m.a == {1: 2, 3: 4}
    with pytest.raises(ValidationError) as exc_info:
        ListDictModel(a=[1, 2, 3])
    assert 'cannot convert dictionary update sequence element #0 to a sequence' in exc_info.value.args[0]


def test_list():
    m = ListDictModel(b=[1, 2, '3'])
    assert m.a is None
    assert m.b == [1, 2, '3']
    m = ListDictModel(b='xyz')
    assert m.b == ['x', 'y', 'z']
    m = ListDictModel(b=(i**2 for i in range(5)))
    assert m.b == [0, 1, 4, 9, 16]
    with pytest.raises(ValidationError) as exc_info:
        ListDictModel(b=1)
    assert '"\'int\' object is not iterable"' in exc_info.value.args[0]


def test_ordered_dict():
    m = ListDictModel(c=OrderedDict([(1, 10), (2, 20)]))
    assert m.c == OrderedDict([(1, 10), (2, 20)])
    m = ListDictModel(c={1: 10, 2: 20})
    assert m.c in (OrderedDict([(1, 10), (2, 20)]), OrderedDict([(2, 20), (1, 10)]))
    m = ListDictModel(c=[(1, 2), (3, 4)])
    assert m.c == OrderedDict([(1, 2), (3, 4)])
    with pytest.raises(ValidationError) as exc_info:
        ListDictModel(c=[1, 2, 3])
    assert '"\'int\' object is not iterable"' in exc_info.value.args[0]


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
