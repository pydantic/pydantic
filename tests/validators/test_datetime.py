import copy
import json
import pickle
import platform
import re
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Dict

import pytest
import pytz

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (datetime(2022, 6, 8, 12, 13, 14), datetime(2022, 6, 8, 12, 13, 14)),
        (date(2022, 6, 8), datetime(2022, 6, 8)),
        ('2022-06-08T12:13:14', datetime(2022, 6, 8, 12, 13, 14)),
        ('1000000000000', datetime(2001, 9, 9, 1, 46, 40, tzinfo=timezone.utc)),
        (b'2022-06-08T12:13:14', datetime(2022, 6, 8, 12, 13, 14)),
        (b'2022-06-08T12:13:14Z', datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone.utc)),
        ((1,), Err('Input should be a valid datetime [type=datetime_type')),
        (time(1, 2, 3), Err('Input should be a valid datetime [type=datetime_type')),
        (Decimal('1654646400'), datetime(2022, 6, 8, tzinfo=timezone.utc)),
        ('1654646400', datetime(2022, 6, 8, tzinfo=timezone.utc)),
        (Decimal('1654646400.123456'), datetime(2022, 6, 8, 0, 0, 0, 123456, tzinfo=timezone.utc)),
        (Decimal('1654646400.1234564'), datetime(2022, 6, 8, 0, 0, 0, 123456, tzinfo=timezone.utc)),
        (Decimal('1654646400.1234568'), datetime(2022, 6, 8, 0, 0, 0, 123457, tzinfo=timezone.utc)),
        ('1654646400.1234568', datetime(2022, 6, 8, 0, 0, 0, 123457, tzinfo=timezone.utc)),
        (253_402_300_800_000, Err('should be a valid datetime, dates after 9999 are not supported as unix timestamps')),
        (-20_000_000_000, Err('should be a valid datetime, dates before 1600 are not supported as unix timestamps')),
        (float('nan'), Err('Input should be a valid datetime, NaN values not permitted [type=datetime_parsing,')),
        (float('inf'), Err('Input should be a valid datetime, dates after 9999')),
        (float('-inf'), Err('Input should be a valid datetime, dates before 1600')),
    ],
)
def test_datetime(input_value, expected):
    v = SchemaValidator({'type': 'datetime'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            result = v.validate_python(input_value)
            print(f'input_value={input_value} result={result}')
    else:
        output = v.validate_python(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (datetime(2022, 6, 8, 12, 13, 14), datetime(2022, 6, 8, 12, 13, 14)),
        (date(2022, 6, 8), Err('Input should be a valid datetime [type=datetime_type')),
        ('2022-06-08T12:13:14', Err('Input should be a valid datetime [type=datetime_type')),
        (b'2022-06-08T12:13:14', Err('Input should be a valid datetime [type=datetime_type')),
        (time(1, 2, 3), Err('Input should be a valid datetime [type=datetime_type')),
        (1654646400, Err('Input should be a valid datetime [type=datetime_type')),
        (Decimal('1654646400'), Err('Input should be a valid datetime [type=datetime_type')),
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

    with pytest.raises(ValidationError, match=r'Input should be greater than 2022-01-01T00:00:00 \[type=greater_than'):
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
        (1655205632, datetime(2022, 6, 14, 11, 20, 32, tzinfo=timezone.utc)),
        (1655205632.331557, datetime(2022, 6, 14, 11, 20, 32, microsecond=331557, tzinfo=timezone.utc)),
        (
            '2022-06-08T12:13:14+24:00',
            Err('Input should be a valid datetime, timezone offset must be less than 24 hours [type=datetime_parsing,'),
        ),
        (True, Err('Input should be a valid datetime [type=datetime_type')),
        (None, Err('Input should be a valid datetime [type=datetime_type')),
        ([1, 2, 3], Err('Input should be a valid datetime [type=datetime_type')),
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
        (123, Err('Input should be a valid datetime [type=datetime_type')),
        (123.4, Err('Input should be a valid datetime [type=datetime_type')),
        (True, Err('Input should be a valid datetime [type=datetime_type')),
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
    with pytest.raises(ValidationError, match=r'Input should be greater than 2022-01-01T15:00:00Z \[type=greater_than'):
        SchemaValidator({'type': 'datetime', 'gt': uk_3pm}).validate_python('2022-01-01T16:00:00+01:00')


def test_tz_info_deepcopy():
    output = SchemaValidator({'type': 'datetime'}).validate_python('2023-02-15T16:23:44.037Z')
    c = copy.deepcopy(output)
    assert repr(output.tzinfo) == 'TzInfo(UTC)'
    assert repr(c.tzinfo) == 'TzInfo(UTC)'
    assert c == output


def test_tz_info_copy():
    output = SchemaValidator({'type': 'datetime'}).validate_python('2023-02-15T16:23:44.037Z')
    c = copy.copy(output)
    assert repr(output.tzinfo) == 'TzInfo(UTC)'
    assert repr(c.tzinfo) == 'TzInfo(UTC)'
    assert c == output


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

    assert excinfo.value.errors(include_url=False) == [
        {
            'type': 'datetime_object_invalid',
            'loc': (),
            'msg': f'Invalid datetime object, got {error_message}',
            'input': dt,
            'ctx': {'error': error_message},
        }
    ]


def test_dict_py():
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'datetime'}, 'values_schema': {'type': 'int'}})
    assert v.validate_python({datetime(2000, 1, 1): 2, datetime(2000, 1, 2): 4}) == {
        datetime(2000, 1, 1): 2,
        datetime(2000, 1, 2): 4,
    }


def test_dict(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'datetime'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'2000-01-01T00:00': 2, '2000-01-02T00:00': 4}) == {
        datetime(2000, 1, 1): 2,
        datetime(2000, 1, 2): 4,
    }


def test_union():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'str'}, {'type': 'datetime'}]})
    assert v.validate_python('2022-01-02T00:00') == '2022-01-02T00:00'
    assert v.validate_python(datetime(2022, 1, 2)) == datetime(2022, 1, 2)

    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'datetime'}, {'type': 'str'}]})
    assert v.validate_python('2022-01-02T00:00') == '2022-01-02T00:00'
    assert v.validate_python(datetime(2022, 1, 2)) == datetime(2022, 1, 2)


def test_invalid_constraint():
    with pytest.raises(SchemaError, match=r'datetime\.gt\n  Input should be a valid datetime'):
        SchemaValidator({'type': 'datetime', 'gt': 'foobar'})


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('2022-06-08T12:13:14', datetime(2022, 6, 8, 12, 13, 14)),
        ('2022-06-08T12:13:14Z', datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone.utc)),
        (1655205632, datetime(2022, 6, 14, 11, 20, 32, tzinfo=timezone.utc)),
        ('2068-06-08T12:13:14', Err('Input should be in the past [type=datetime_past,')),
        (3105730800, Err('Input should be in the past [type=datetime_past,')),
    ],
)
def test_datetime_past(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(core_schema.datetime_schema(now_utc_offset=0, now_op='past'))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected


def test_datetime_past_timezone():
    v = SchemaValidator(core_schema.datetime_schema(now_utc_offset=0, now_op='past'))
    now_utc = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert v.isinstance_python(now_utc)
    # "later" in the day
    assert v.isinstance_python(now_utc.astimezone(pytz.timezone('Europe/Istanbul')))
    # "earlier" in the day
    assert v.isinstance_python(now_utc.astimezone(pytz.timezone('America/Los_Angeles')))

    soon_utc = now_utc + timedelta(minutes=1)
    assert not v.isinstance_python(soon_utc)

    # "later" in the day
    assert not v.isinstance_python(soon_utc.astimezone(pytz.timezone('Europe/Istanbul')))
    # "earlier" in the day
    assert not v.isinstance_python(soon_utc.astimezone(pytz.timezone('America/Los_Angeles')))

    # input value is timezone naive, so we do a dumb comparison in these terms the istanbul time is later so fails
    # wile the LA time is earlier so passes
    assert not v.isinstance_python(soon_utc.astimezone(pytz.timezone('Europe/Istanbul')).replace(tzinfo=None))
    assert v.isinstance_python(soon_utc.astimezone(pytz.timezone('America/Los_Angeles')).replace(tzinfo=None))


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('2068-06-08T12:13:14', datetime(2068, 6, 8, 12, 13, 14)),
        ('2068-06-08T12:13:14Z', datetime(2068, 6, 8, 12, 13, 14, tzinfo=timezone.utc)),
        (3105730800, datetime(2068, 5, 31, 23, 0, tzinfo=timezone.utc)),
        ('2022-06-08T12:13:14', Err('Input should be in the future [type=datetime_future,')),
        (1655205632, Err('Input should be in the future [type=datetime_future,')),
    ],
)
def test_datetime_future(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(core_schema.datetime_schema(now_utc_offset=0, now_op='future'))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected


def test_datetime_future_timezone():
    v = SchemaValidator(core_schema.datetime_schema(now_utc_offset=0, now_op='future'))
    now_utc = datetime.now(timezone.utc)

    soon_utc = now_utc + timedelta(minutes=1)
    assert v.isinstance_python(soon_utc)

    # "later" in the day
    assert v.isinstance_python(soon_utc.astimezone(pytz.timezone('Europe/Istanbul')))
    # "earlier" in the day
    assert v.isinstance_python(soon_utc.astimezone(pytz.timezone('America/Los_Angeles')))

    past_utc = now_utc - timedelta(minutes=1)
    assert not v.isinstance_python(past_utc)

    # "later" in the day
    assert not v.isinstance_python(past_utc.astimezone(pytz.timezone('Europe/Istanbul')))
    # "earlier" in the day
    assert not v.isinstance_python(past_utc.astimezone(pytz.timezone('America/Los_Angeles')))


def test_mock_utc_offset_8_hours(mocker):
    """
    Test that mocking time.localtime() is working, note that due to caching in datetime_etc,
    time.localtime() will return `{'tm_gmtoff': 8 * 60 * 60}` for the rest of the session.
    """
    mocker.patch('time.localtime', return_value=type('time.struct_time', (), {'tm_gmtoff': 8 * 60 * 60}))
    v = SchemaValidator(core_schema.datetime_schema(now_op='future'))
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8, minutes=1)
    assert v.isinstance_python(future)

    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7, minutes=59)
    assert not v.isinstance_python(future)


def test_offset_too_large():
    with pytest.raises(SchemaError, match=r'Input should be greater than -86400 \[type=greater_than,'):
        SchemaValidator(core_schema.datetime_schema(now_op='past', now_utc_offset=-24 * 3600))


def test_raises_schema_error_for_unknown_constraint_kind():
    with pytest.raises(
        SchemaError,
        match=(r'Input should be \'aware\' or \'naive\' \[type=literal_error, input_value=\'foo\', input_type=str\]'),
    ):
        SchemaValidator({'type': 'datetime', 'tz_constraint': 'foo'})


def test_aware():
    v = SchemaValidator(core_schema.datetime_schema(tz_constraint='aware'))
    value = datetime.now(tz=timezone.utc)
    assert value is v.validate_python(value)
    assert v.validate_python('2022-06-08T12:13:14Z') == datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone.utc)

    value = datetime.now()
    with pytest.raises(ValidationError, match=r'Input should have timezone info \[type=timezone_aware,'):
        v.validate_python(value)

    with pytest.raises(ValidationError, match=r'Input should have timezone info \[type=timezone_aware,'):
        v.validate_python('2022-06-08T12:13:14')


def test_naive():
    v = SchemaValidator(core_schema.datetime_schema(tz_constraint='naive'))
    value = datetime.now()
    assert value is v.validate_python(value)
    assert v.validate_python('2022-06-08T12:13:14') == datetime(2022, 6, 8, 12, 13, 14)

    value = datetime.now(tz=timezone.utc)
    with pytest.raises(ValidationError, match=r'Input should not have timezone info \[type=timezone_naive,'):
        v.validate_python(value)

    with pytest.raises(ValidationError, match=r'Input should not have timezone info \[type=timezone_naive,'):
        v.validate_python('2022-06-08T12:13:14Z')


def test_aware_specific():
    v = SchemaValidator(core_schema.datetime_schema(tz_constraint=0))
    value = datetime.now(tz=timezone.utc)
    assert value is v.validate_python(value)
    assert v.validate_python('2022-06-08T12:13:14Z') == datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone.utc)

    value = datetime.now()
    with pytest.raises(ValidationError, match='Input should have timezone info'):
        v.validate_python(value)

    value = datetime.now(tz=timezone(timedelta(hours=1)))
    with pytest.raises(ValidationError, match='Timezone offset of 0 required, got 3600') as exc_info:
        v.validate_python(value)

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'timezone_offset',
            'loc': (),
            'msg': 'Timezone offset of 0 required, got 3600',
            'input': value,
            'ctx': {'tz_expected': 0, 'tz_actual': 3600},
        }
    ]
    with pytest.raises(ValidationError, match='Timezone offset of 0 required, got 3600'):
        v.validate_python('2022-06-08T12:13:14+01:00')


def test_neg_7200():
    v = SchemaValidator(core_schema.datetime_schema(tz_constraint=-7200))
    value = datetime.now(tz=timezone(timedelta(hours=-2)))
    assert value is v.validate_python(value)

    value = datetime.now()
    with pytest.raises(ValidationError, match='Input should have timezone info'):
        v.validate_python(value)

    value = datetime.now(tz=timezone.utc)
    with pytest.raises(ValidationError, match='Timezone offset of -7200 required, got 0'):
        v.validate_python(value)
    with pytest.raises(ValidationError, match='Timezone offset of -7200 required, got 0'):
        v.validate_python('2022-06-08T12:13:14Z')


def test_tz_constraint_too_high():
    with pytest.raises(SchemaError, match='OverflowError: Python int too large to convert to C long'):
        SchemaValidator(core_schema.datetime_schema(tz_constraint=2**64))


def test_tz_constraint_wrong():
    with pytest.raises(SchemaError, match="Input should be 'aware' or 'naive"):
        SchemaValidator(core_schema.datetime_schema(tz_constraint='wrong'))


def test_tz_pickle() -> None:
    """
    https://github.com/pydantic/pydantic-core/issues/589
    """
    v = SchemaValidator(core_schema.datetime_schema())
    original = datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone(timedelta(hours=-12, minutes=-15)))
    validated = v.validate_python('2022-06-08T12:13:14-12:15')
    assert validated == original
    assert pickle.loads(pickle.dumps(validated)) == validated == original


def test_tz_hash() -> None:
    v = SchemaValidator(core_schema.datetime_schema())
    lookup: Dict[datetime, str] = {}
    for day in range(1, 10):
        input_str = f'2022-06-{day:02}T12:13:14-12:15'
        validated = v.validate_python(input_str)
        lookup[validated] = input_str

    assert len(lookup) == 9
    assert (
        lookup[datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone(timedelta(hours=-12, minutes=-15)))]
        == '2022-06-08T12:13:14-12:15'
    )


def test_tz_cmp() -> None:
    v = SchemaValidator(core_schema.datetime_schema())
    validated1 = v.validate_python('2022-06-08T12:13:14-12:15')
    validated2 = v.validate_python('2022-06-08T12:13:14-12:14')

    assert validated1 > validated2
    assert validated2 < validated1
