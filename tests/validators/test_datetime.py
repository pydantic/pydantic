import json
import platform
import re
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest
import pytz

from pydantic_core import SchemaError, SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (datetime(2022, 6, 8, 12, 13, 14), datetime(2022, 6, 8, 12, 13, 14)),
        (date(2022, 6, 8), datetime(2022, 6, 8)),
        ('2022-06-08T12:13:14', datetime(2022, 6, 8, 12, 13, 14)),
        (b'2022-06-08T12:13:14', datetime(2022, 6, 8, 12, 13, 14)),
        (b'2022-06-08T12:13:14Z', datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone.utc)),
        ((1,), Err('Input should be a valid datetime [kind=datetime_type')),
        (time(1, 2, 3), Err('Input should be a valid datetime [kind=datetime_type')),
        (Decimal('1654646400'), datetime(2022, 6, 8)),
        (Decimal('1654646400.123456'), datetime(2022, 6, 8, 0, 0, 0, 123456)),
        (Decimal('1654646400.1234564'), datetime(2022, 6, 8, 0, 0, 0, 123456)),
        (Decimal('1654646400.1234568'), datetime(2022, 6, 8, 0, 0, 0, 123457)),
        (253_402_300_800_000, Err('should be a valid datetime, dates after 9999 are not supported as unix timestamps')),
        (-20_000_000_000, Err('should be a valid datetime, dates before 1600 are not supported as unix timestamps')),
    ],
)
def test_datetime(input_value, expected):
    v = SchemaValidator({'type': 'datetime'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (datetime(2022, 6, 8, 12, 13, 14), datetime(2022, 6, 8, 12, 13, 14)),
        (date(2022, 6, 8), Err('Input should be a valid datetime [kind=datetime_type')),
        ('2022-06-08T12:13:14', Err('Input should be a valid datetime [kind=datetime_type')),
        (b'2022-06-08T12:13:14', Err('Input should be a valid datetime [kind=datetime_type')),
        (time(1, 2, 3), Err('Input should be a valid datetime [kind=datetime_type')),
        (1654646400, Err('Input should be a valid datetime [kind=datetime_type')),
        (Decimal('1654646400'), Err('Input should be a valid datetime [kind=datetime_type')),
    ],
)
def test_datetime_strict(input_value, expected):
    v = SchemaValidator({'type': 'datetime', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


def test_keep_tz():
    tz = pytz.timezone('Europe/London')
    dt = tz.localize(datetime(2022, 6, 14, 12, 13, 14))
    v = SchemaValidator({'type': 'datetime'})

    output = v.validate_python(dt)
    assert output == dt

    # dst object is unaffected by validation
    assert output.tzinfo.dst(datetime(2022, 6, 1)) == timedelta(seconds=3600)
    assert output.tzinfo.dst(datetime(2022, 1, 1)) == timedelta(seconds=0)


def test_keep_tz_bound():
    tz = pytz.timezone('Europe/London')
    dt = tz.localize(datetime(2022, 6, 14, 12, 13, 14))
    v = SchemaValidator({'type': 'datetime', 'gt': datetime(2022, 1, 1)})

    output = v.validate_python(dt)
    assert output == dt

    # dst object is unaffected by validation
    assert output.tzinfo.dst(datetime(2022, 6, 1)) == timedelta(hours=1)
    assert output.tzinfo.dst(datetime(2022, 1, 1)) == timedelta(0)

    with pytest.raises(ValidationError, match=r'Input should be greater than 2022-01-01T00:00:00 \[kind=greater_than'):
        v.validate_python(tz.localize(datetime(2021, 6, 14)))


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('2022-06-08T12:13:14', datetime(2022, 6, 8, 12, 13, 14)),
        ('2022-06-08T12:13:14Z', datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone.utc)),
        (
            '2022-06-08T12:13:14+12:15',
            datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone(timedelta(hours=12, minutes=15))),
        ),
        (
            '2022-06-08T12:13:14+23:59',
            datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone(timedelta(hours=23, minutes=59))),
        ),
        (1655205632, datetime(2022, 6, 14, 11, 20, 32)),
        (1655205632.331557, datetime(2022, 6, 14, 11, 20, 32, microsecond=331557)),
        (
            '2022-06-08T12:13:14+24:00',
            Err('Input should be a valid datetime, timezone offset must be less than 24 hours [kind=datetime_parsing,'),
        ),
        (True, Err('Input should be a valid datetime [kind=datetime_type')),
        (None, Err('Input should be a valid datetime [kind=datetime_type')),
        ([1, 2, 3], Err('Input should be a valid datetime [kind=datetime_type')),
    ],
)
def test_datetime_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'datetime'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('2022-06-08T12:13:14', datetime(2022, 6, 8, 12, 13, 14)),
        ('2022-06-08T12:13:14Z', datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone.utc)),
        (123, Err('Input should be a valid datetime [kind=datetime_type')),
        (123.4, Err('Input should be a valid datetime [kind=datetime_type')),
        (True, Err('Input should be a valid datetime [kind=datetime_type')),
    ],
)
def test_datetime_strict_json(input_value, expected):
    v = SchemaValidator({'type': 'datetime', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_json(json.dumps(input_value))
    else:
        output = v.validate_json(json.dumps(input_value))
        assert output == expected


def test_custom_timezone_repr():
    output = SchemaValidator({'type': 'datetime'}).validate_python('2022-06-08T12:13:14-12:15')
    assert output == datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone(timedelta(hours=-12, minutes=-15)))
    assert output.tzinfo.utcoffset(output) == timedelta(hours=-12, minutes=-15)
    assert output.tzinfo.dst(output) is None
    assert output.tzinfo.tzname(output) == '-12:15'
    assert str(output.tzinfo) == '-12:15'
    assert repr(output.tzinfo) == 'TzInfo(-12:15)'


def test_custom_timezone_utc_repr():
    output = SchemaValidator({'type': 'datetime'}).validate_python('2022-06-08T12:13:14Z')
    assert output == datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone(timedelta(0)))
    assert output.tzinfo.utcoffset(output) == timedelta(0)
    assert output.tzinfo.dst(output) is None
    assert output.tzinfo.tzname(output) == 'UTC'
    assert str(output.tzinfo) == 'UTC'
    assert repr(output.tzinfo) == 'TzInfo(UTC)'


def test_tz_comparison():
    tz = pytz.timezone('Europe/London')
    uk_3pm = tz.localize(datetime(2022, 1, 1, 15, 0, 0))

    # two times are the same instant, therefore le and ge are both ok
    v = SchemaValidator({'type': 'datetime', 'le': uk_3pm}).validate_python('2022-01-01T16:00:00+01:00')
    assert v == datetime(2022, 1, 1, 16, 0, 0, tzinfo=timezone(timedelta(hours=1)))

    v = SchemaValidator({'type': 'datetime', 'ge': uk_3pm}).validate_python('2022-01-01T16:00:00+01:00')
    assert v == datetime(2022, 1, 1, 16, 0, 0, tzinfo=timezone(timedelta(hours=1)))

    # but not gt
    with pytest.raises(ValidationError, match=r'Input should be greater than 2022-01-01T15:00:00Z \[kind=greater_than'):
        SchemaValidator({'type': 'datetime', 'gt': uk_3pm}).validate_python('2022-01-01T16:00:00+01:00')


def test_custom_tz():
    class CustomTz(tzinfo):
        def utcoffset(self, _dt):
            return None

        def dst(self, _dt):
            return None

        def tzname(self, _dt):
            return 'CustomTZ'

    schema = SchemaValidator({'type': 'datetime', 'gt': datetime(2022, 1, 1, 15, 0, 0)})

    dt = datetime(2022, 1, 1, 16, 0, 0, tzinfo=CustomTz())
    outcome = schema.validate_python(dt)
    assert outcome == dt


def test_custom_invalid_tz():
    class CustomTz(tzinfo):
        # utcoffset is not implemented!

        def tzname(self, _dt):
            return 'CustomTZ'

    schema = SchemaValidator({'type': 'datetime', 'gt': datetime(2022, 1, 1, 15, 0, 0)})

    dt = datetime(2022, 1, 1, 16, 0, 0, tzinfo=CustomTz())
    # perhaps this should be a ValidationError? but we don't catch other errors
    with pytest.raises(ValidationError) as excinfo:
        schema.validate_python(dt)

    # exception messages differ between python and pypy
    if platform.python_implementation() == 'PyPy':
        error_message = 'NotImplementedError: tzinfo subclass must override utcoffset()'
    else:
        error_message = 'NotImplementedError: a tzinfo subclass must implement utcoffset()'

    assert excinfo.value.errors() == [
        {
            'kind': 'datetime_object_invalid',
            'loc': [],
            'message': f'Invalid datetime object, got {error_message}',
            'input_value': dt,
            'context': {'error': error_message},
        }
    ]


def test_dict_py():
    v = SchemaValidator({'type': 'dict', 'keys_schema': 'datetime', 'values_schema': 'int'})
    assert v.validate_python({datetime(2000, 1, 1): 2, datetime(2000, 1, 2): 4}) == {
        datetime(2000, 1, 1): 2,
        datetime(2000, 1, 2): 4,
    }


def test_dict(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': 'datetime', 'values_schema': 'int'})
    assert v.validate_test({'2000-01-01T00:00': 2, '2000-01-02T00:00': 4}) == {
        datetime(2000, 1, 1): 2,
        datetime(2000, 1, 2): 4,
    }


def test_union():
    v = SchemaValidator({'type': 'union', 'choices': ['str', 'datetime']})
    assert v.validate_python('2022-01-02T00:00') == '2022-01-02T00:00'
    assert v.validate_python(datetime(2022, 1, 2)) == datetime(2022, 1, 2)

    v = SchemaValidator({'type': 'union', 'choices': ['datetime', 'str']})
    assert v.validate_python('2022-01-02T00:00') == '2022-01-02T00:00'
    assert v.validate_python(datetime(2022, 1, 2)) == datetime(2022, 1, 2)


def test_invalid_constraint():
    with pytest.raises(SchemaError, match='datetime -> gt\n  Input should be a valid datetime'):
        SchemaValidator({'type': 'datetime', 'gt': 'foobar'})
