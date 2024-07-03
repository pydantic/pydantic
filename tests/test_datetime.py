import re
from datetime import date, datetime, time, timedelta, timezone

import pytest
from dirty_equals import HasRepr
from typing_extensions import Annotated

from pydantic import (
    AwareDatetime,
    BaseModel,
    FutureDate,
    FutureDatetime,
    NaiveDatetime,
    PastDate,
    PastDatetime,
    ValidationError,
    condate,
)

from .conftest import Err


def create_tz(minutes):
    return timezone(timedelta(minutes=minutes))


@pytest.fixture(scope='module', params=[FutureDate, Annotated[date, FutureDate()]])
def future_date_type(request):
    return request.param


@pytest.fixture(scope='module', params=[PastDate, Annotated[date, PastDate()]])
def past_date_type(request):
    return request.param


@pytest.fixture(scope='module', params=[FutureDatetime, Annotated[datetime, FutureDatetime()]])
def future_datetime_type(request):
    return request.param


@pytest.fixture(scope='module', params=[PastDatetime, Annotated[datetime, PastDatetime()]])
def past_datetime_type(request):
    return request.param


@pytest.fixture(scope='module', params=[AwareDatetime, Annotated[datetime, AwareDatetime()]])
def aware_datetime_type(request):
    return request.param


@pytest.fixture(scope='module', params=[NaiveDatetime, Annotated[datetime, NaiveDatetime()]])
def naive_datetime_type(request):
    return request.param


@pytest.fixture(scope='module', name='DateModel')
def date_model_fixture():
    class DateModel(BaseModel):
        d: date

    return DateModel


@pytest.mark.parametrize(
    'value,result',
    [
        # Valid inputs
        (1_493_942_400, date(2017, 5, 5)),
        (1_493_942_400_000, date(2017, 5, 5)),
        (0, date(1970, 1, 1)),
        ('2012-04-23', date(2012, 4, 23)),
        (b'2012-04-23', date(2012, 4, 23)),
        (date(2012, 4, 9), date(2012, 4, 9)),
        (datetime(2012, 4, 9, 0, 0), date(2012, 4, 9)),
        # Invalid inputs
        (datetime(2012, 4, 9, 12, 15), Err('Datetimes provided to dates should have zero time - e.g. be exact dates')),
        ('x20120423', Err('Input should be a valid date or datetime, input is too short')),
        ('2012-04-56', Err('Input should be a valid date or datetime, day value is outside expected range')),
        (19_999_958_400, date(2603, 10, 11)),  # just before watershed
        (20000044800, Err('type=date_from_datetime_inexact,')),  # just after watershed
        (1_549_238_400, date(2019, 2, 4)),  # nowish in s
        (1_549_238_400_000, date(2019, 2, 4)),  # nowish in ms
        (1_549_238_400_000_000, Err('Input should be a valid date or datetime, dates after 9999')),  # nowish in μs
        (1_549_238_400_000_000_000, Err('Input should be a valid date or datetime, dates after 9999')),  # nowish in ns
        ('infinity', Err('Input should be a valid date or datetime, input is too short')),
        (float('inf'), Err('Input should be a valid date or datetime, dates after 9999')),
        (int('1' + '0' * 100), Err('Input should be a valid date or datetime, dates after 9999')),
        (1e1000, Err('Input should be a valid date or datetime, dates after 9999')),
        (float('-infinity'), Err('Input should be a valid date or datetime, dates before 1600')),
        (float('nan'), Err('Input should be a valid date or datetime, NaN values not permitted')),
    ],
)
def test_date_parsing(DateModel, value, result):
    if isinstance(result, Err):
        with pytest.raises(ValidationError, match=result.message_escaped()):
            DateModel(d=value)
    else:
        assert DateModel(d=value).d == result


@pytest.fixture(scope='module', name='TimeModel')
def time_model_fixture():
    class TimeModel(BaseModel):
        d: time

    return TimeModel


@pytest.mark.parametrize(
    'value,result',
    [
        # Valid inputs
        ('09:15:00', time(9, 15)),
        ('10:10', time(10, 10)),
        ('10:20:30.400', time(10, 20, 30, 400_000)),
        (b'10:20:30.400', time(10, 20, 30, 400_000)),
        (time(4, 8, 16), time(4, 8, 16)),
        (3610, time(1, 0, 10, tzinfo=timezone.utc)),
        (3600.5, time(1, 0, 0, 500000, tzinfo=timezone.utc)),
        (86400 - 1, time(23, 59, 59, tzinfo=timezone.utc)),
        # Invalid inputs
        ('4:8:16', Err('Input should be in a valid time format, invalid character in hour [type=time_parsing,')),
        (86400, Err('Input should be in a valid time format, numeric times may not exceed 86,399 seconds')),
        ('xxx', Err('Input should be in a valid time format, input is too short [type=time_parsing,')),
        ('091500', Err('Input should be in a valid time format, invalid time separator, expected `:`')),
        (b'091500', Err('Input should be in a valid time format, invalid time separator, expected `:`')),
        ('09:15:90', Err('Input should be in a valid time format, second value is outside expected range of 0-59')),
        ('11:05:00Y', Err('Input should be in a valid time format, invalid timezone sign')),
        # https://github.com/pydantic/speedate/issues/10
        ('11:05:00-05:30', time(11, 5, 0, tzinfo=create_tz(-330))),
        ('11:05:00-0530', time(11, 5, 0, tzinfo=create_tz(-330))),
        ('11:05:00Z', time(11, 5, 0, tzinfo=timezone.utc)),
        ('11:05:00+00:00', time(11, 5, 0, tzinfo=timezone.utc)),
        ('11:05-06:00', time(11, 5, 0, tzinfo=create_tz(-360))),
        ('11:05+06:00', time(11, 5, 0, tzinfo=create_tz(360))),
        ('11:05:00-25:00', Err('Input should be in a valid time format, timezone offset must be less than 24 hours')),
    ],
)
def test_time_parsing(TimeModel, value, result):
    if isinstance(result, Err):
        with pytest.raises(ValidationError, match=result.message_escaped()):
            TimeModel(d=value)
    else:
        assert TimeModel(d=value).d == result


@pytest.fixture(scope='module', name='DatetimeModel')
def datetime_model_fixture():
    class DatetimeModel(BaseModel):
        dt: datetime

    return DatetimeModel


@pytest.mark.parametrize(
    'value,result',
    [
        # Valid inputs
        # values in seconds
        (1_494_012_444.883_309, datetime(2017, 5, 5, 19, 27, 24, 883_309, tzinfo=timezone.utc)),
        (1_494_012_444, datetime(2017, 5, 5, 19, 27, 24, tzinfo=timezone.utc)),
        # values in ms
        (1_494_012_444_000, datetime(2017, 5, 5, 19, 27, 24, tzinfo=timezone.utc)),
        ('2012-04-23T09:15:00', datetime(2012, 4, 23, 9, 15)),
        ('2012-04-23T09:15:00Z', datetime(2012, 4, 23, 9, 15, 0, 0, timezone.utc)),
        ('2012-04-23T10:20:30.400+02:30', datetime(2012, 4, 23, 10, 20, 30, 400_000, create_tz(150))),
        ('2012-04-23T10:20:30.400+02:00', datetime(2012, 4, 23, 10, 20, 30, 400_000, create_tz(120))),
        ('2012-04-23T10:20:30.400-02:00', datetime(2012, 4, 23, 10, 20, 30, 400_000, create_tz(-120))),
        (b'2012-04-23T10:20:30.400-02:00', datetime(2012, 4, 23, 10, 20, 30, 400_000, create_tz(-120))),
        (datetime(2017, 5, 5), datetime(2017, 5, 5)),
        (0, datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
        # Numeric inputs as strings
        ('1494012444.883309', datetime(2017, 5, 5, 19, 27, 24, 883309, tzinfo=timezone.utc)),
        ('1494012444', datetime(2017, 5, 5, 19, 27, 24, tzinfo=timezone.utc)),
        (b'1494012444', datetime(2017, 5, 5, 19, 27, 24, tzinfo=timezone.utc)),
        ('1494012444000.883309', datetime(2017, 5, 5, 19, 27, 24, 883, tzinfo=timezone.utc)),
        ('-1494012444000.883309', datetime(1922, 8, 29, 4, 32, 35, 999117, tzinfo=timezone.utc)),
        (19_999_999_999, datetime(2603, 10, 11, 11, 33, 19, tzinfo=timezone.utc)),  # just before watershed
        (20_000_000_001, datetime(1970, 8, 20, 11, 33, 20, 1000, tzinfo=timezone.utc)),  # just after watershed
        (1_549_316_052, datetime(2019, 2, 4, 21, 34, 12, 0, tzinfo=timezone.utc)),  # nowish in s
        (1_549_316_052_104, datetime(2019, 2, 4, 21, 34, 12, 104_000, tzinfo=timezone.utc)),  # nowish in ms
        # Invalid inputs
        (1_549_316_052_104_324, Err('Input should be a valid datetime, dates after 9999')),  # nowish in μs
        (1_549_316_052_104_324_096, Err('Input should be a valid datetime, dates after 9999')),  # nowish in ns
        (float('inf'), Err('Input should be a valid datetime, dates after 9999')),
        (float('-inf'), Err('Input should be a valid datetime, dates before 1600')),
        (1e50, Err('Input should be a valid datetime, dates after 9999')),
        (float('nan'), Err('Input should be a valid datetime, NaN values not permitted')),
    ],
)
def test_datetime_parsing(DatetimeModel, value, result):
    if isinstance(result, Err):
        with pytest.raises(ValidationError, match=result.message_escaped()):
            DatetimeModel(dt=value)
    else:
        assert DatetimeModel(dt=value).dt == result


@pytest.mark.parametrize(
    'value,result',
    [
        # Invalid inputs
        ('2012-4-9 4:8:16', Err('Input should be a valid datetime or date, invalid character in month')),
        ('x20120423091500', Err('Input should be a valid datetime or date, invalid character in year')),
        ('2012-04-56T09:15:90', Err('Input should be a valid datetime or date, day value is outside expected range')),
        (
            '2012-04-23T11:05:00-25:00',
            Err('Input should be a valid datetime or date, unexpected extra characters at the end of the input'),
        ),
        ('infinity', Err('Input should be a valid datetime or date, input is too short')),
    ],
)
def test_datetime_parsing_from_str(DatetimeModel, value, result):
    if isinstance(result, Err):
        with pytest.raises(ValidationError, match=result.message_escaped()):
            DatetimeModel(dt=value)
    else:
        assert DatetimeModel(dt=value).dt == result


def test_aware_datetime_validation_success(aware_datetime_type):
    class Model(BaseModel):
        foo: aware_datetime_type

    value = datetime.now(tz=timezone.utc)

    assert Model(foo=value).foo == value


def test_aware_datetime_validation_fails(aware_datetime_type):
    class Model(BaseModel):
        foo: aware_datetime_type

    value = datetime.now()

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'timezone_aware',
            'loc': ('foo',),
            'msg': 'Input should have timezone info',
            'input': value,
        }
    ]


def test_naive_datetime_validation_success(naive_datetime_type):
    class Model(BaseModel):
        foo: naive_datetime_type

    value = datetime.now()

    assert Model(foo=value).foo == value


def test_naive_datetime_validation_fails(naive_datetime_type):
    class Model(BaseModel):
        foo: naive_datetime_type

    value = datetime.now(tz=timezone.utc)

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'timezone_naive',
            'loc': ('foo',),
            'msg': 'Input should not have timezone info',
            'input': value,
        }
    ]


@pytest.fixture(scope='module', name='TimedeltaModel')
def timedelta_model_fixture():
    class TimedeltaModel(BaseModel):
        d: timedelta

    return TimedeltaModel


@pytest.mark.parametrize(
    'delta',
    [
        timedelta(days=4, minutes=15, seconds=30, milliseconds=100),  # fractions of seconds
        timedelta(hours=10, minutes=15, seconds=30),  # hours, minutes, seconds
        timedelta(days=4, minutes=15, seconds=30),  # multiple days
        timedelta(days=1, minutes=00, seconds=00),  # single day
        timedelta(days=-4, minutes=15, seconds=30),  # negative durations
        timedelta(minutes=15, seconds=30),  # minute & seconds
        timedelta(seconds=30),  # seconds
    ],
)
def test_parse_python_format(TimedeltaModel, delta):
    assert TimedeltaModel(d=delta).d == delta
    # assert TimedeltaModel(d=str(delta)).d == delta


@pytest.mark.parametrize(
    'value,result',
    [
        # seconds
        (timedelta(seconds=30), timedelta(seconds=30)),
        (30, timedelta(seconds=30)),
        (30.1, timedelta(seconds=30, milliseconds=100)),
        (9.9e-05, timedelta(microseconds=99)),
        # minutes seconds
        ('00:15:30', timedelta(minutes=15, seconds=30)),
        ('00:05:30', timedelta(minutes=5, seconds=30)),
        # hours minutes seconds
        ('10:15:30', timedelta(hours=10, minutes=15, seconds=30)),
        ('01:15:30', timedelta(hours=1, minutes=15, seconds=30)),
        # ('100:200:300', timedelta(hours=100, minutes=200, seconds=300)),
        # days
        ('4d,00:15:30', timedelta(days=4, minutes=15, seconds=30)),
        ('4d,10:15:30', timedelta(days=4, hours=10, minutes=15, seconds=30)),
        # fractions of seconds
        ('00:15:30.1', timedelta(minutes=15, seconds=30, milliseconds=100)),
        ('00:15:30.01', timedelta(minutes=15, seconds=30, milliseconds=10)),
        ('00:15:30.001', timedelta(minutes=15, seconds=30, milliseconds=1)),
        ('00:15:30.0001', timedelta(minutes=15, seconds=30, microseconds=100)),
        ('00:15:30.00001', timedelta(minutes=15, seconds=30, microseconds=10)),
        ('00:15:30.000001', timedelta(minutes=15, seconds=30, microseconds=1)),
        (b'00:15:30.000001', timedelta(minutes=15, seconds=30, microseconds=1)),
        # negative
        ('-4d,00:15:30', timedelta(days=-4, minutes=-15, seconds=-30)),
        (-172800, timedelta(days=-2)),
        ('-00:15:30', timedelta(minutes=-15, seconds=-30)),
        ('-01:15:30', timedelta(hours=-1, minutes=-15, seconds=-30)),
        (-30.1, timedelta(seconds=-30, milliseconds=-100)),
        # iso_8601
        ('30', Err('Input should be a valid timedelta, "day" identifier')),
        ('P4Y', timedelta(days=1460)),
        ('P4M', timedelta(days=120)),
        ('P4W', timedelta(days=28)),
        ('P4D', timedelta(days=4)),
        ('P0.5D', timedelta(hours=12)),
        ('PT5H', timedelta(hours=5)),
        ('PT5M', timedelta(minutes=5)),
        ('PT5S', timedelta(seconds=5)),
        ('PT0.000005S', timedelta(microseconds=5)),
        (b'PT0.000005S', timedelta(microseconds=5)),
    ],
)
def test_parse_durations(TimedeltaModel, value, result):
    if isinstance(result, Err):
        with pytest.raises(ValidationError, match=result.message_escaped()):
            TimedeltaModel(d=value)
    else:
        assert TimedeltaModel(d=value).d == result


@pytest.mark.parametrize(
    'field, value, error_message',
    [
        ('dt', [], 'Input should be a valid datetime'),
        ('dt', {}, 'Input should be a valid datetime'),
        ('dt', object, 'Input should be a valid datetime'),
        ('d', [], 'Input should be a valid date'),
        ('d', {}, 'Input should be a valid date'),
        ('d', object, 'Input should be a valid date'),
        ('t', [], 'Input should be a valid time'),
        ('t', {}, 'Input should be a valid time'),
        ('t', object, 'Input should be a valid time'),
        ('td', [], 'Input should be a valid timedelta'),
        ('td', {}, 'Input should be a valid timedelta'),
        ('td', object, 'Input should be a valid timedelta'),
    ],
)
def test_model_type_errors(field, value, error_message):
    class Model(BaseModel):
        dt: datetime = None
        d: date = None
        t: time = None
        td: timedelta = None

    with pytest.raises(ValidationError) as exc_info:
        Model(**{field: value})
    assert len(exc_info.value.errors(include_url=False)) == 1
    error = exc_info.value.errors(include_url=False)[0]
    assert error['msg'] == error_message


@pytest.mark.parametrize('field', ['dt', 'd', 't', 'dt'])
def test_unicode_decode_error(field):
    class Model(BaseModel):
        dt: datetime = None
        d: date = None
        t: time = None
        td: timedelta = None

    with pytest.raises(ValidationError) as exc_info:
        Model(**{field: b'\x81\x81\x81\x81\x81\x81\x81\x81'})
    assert exc_info.value.error_count() == 1
    # errors vary


def test_nan():
    class Model(BaseModel):
        dt: datetime
        d: date

    with pytest.raises(ValidationError) as exc_info:
        Model(dt=float('nan'), d=float('nan'))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_parsing',
            'loc': ('dt',),
            'msg': 'Input should be a valid datetime, NaN values not permitted',
            'input': HasRepr('nan'),
            'ctx': {'error': 'NaN values not permitted'},
        },
        {
            'type': 'date_from_datetime_parsing',
            'loc': ('d',),
            'msg': 'Input should be a valid date or datetime, NaN values not permitted',
            'input': HasRepr('nan'),
            'ctx': {'error': 'NaN values not permitted'},
        },
    ]


@pytest.mark.parametrize(
    'constraint,msg,ok_value,error_value',
    [
        ('gt', 'greater than', date(2020, 1, 2), date(2019, 12, 31)),
        ('gt', 'greater than', date(2020, 1, 2), date(2020, 1, 1)),
        ('ge', 'greater than or equal to', date(2020, 1, 2), date(2019, 12, 31)),
        ('ge', 'greater than or equal to', date(2020, 1, 1), date(2019, 12, 31)),
        ('lt', 'less than', date(2019, 12, 31), date(2020, 1, 2)),
        ('lt', 'less than', date(2019, 12, 31), date(2020, 1, 1)),
        ('le', 'less than or equal to', date(2019, 12, 31), date(2020, 1, 2)),
        ('le', 'less than or equal to', date(2020, 1, 1), date(2020, 1, 2)),
    ],
)
def test_date_constraints(constraint, msg, ok_value, error_value):
    class Model(BaseModel):
        a: condate(**{constraint: date(2020, 1, 1)})

    assert Model(a=ok_value).model_dump() == {'a': ok_value}

    with pytest.raises(ValidationError, match=re.escape(f'Input should be {msg} 2020-01-01')):
        Model(a=error_value)


@pytest.mark.parametrize(
    'value,result',
    (
        ('1996-01-22', date(1996, 1, 22)),
        (date(1996, 1, 22), date(1996, 1, 22)),
    ),
)
def test_past_date_validation_success(value, result, past_date_type):
    class Model(BaseModel):
        foo: past_date_type

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value',
    (
        date.today(),
        date.today() + timedelta(1),
        '2064-06-01',
    ),
)
def test_past_date_validation_fails(value, past_date_type):
    class Model(BaseModel):
        foo: past_date_type

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'date_past',
            'loc': ('foo',),
            'msg': 'Date should be in the past',
            'input': value,
        }
    ]


@pytest.mark.parametrize(
    'value,result',
    (
        (date.today() + timedelta(1), date.today() + timedelta(1)),
        ('2064-06-01', date(2064, 6, 1)),
    ),
)
def test_future_date_validation_success(value, result, future_date_type):
    class Model(BaseModel):
        foo: future_date_type

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value',
    (
        date.today(),
        date.today() - timedelta(1),
        '1996-01-22',
    ),
)
def test_future_date_validation_fails(value, future_date_type):
    class Model(BaseModel):
        foo: future_date_type

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'date_future',
            'loc': ('foo',),
            'msg': 'Date should be in the future',
            'input': value,
        }
    ]


@pytest.mark.parametrize(
    'value,result',
    (
        ('1996-01-22T10:20:30', datetime(1996, 1, 22, 10, 20, 30)),
        (datetime(1996, 1, 22, 10, 20, 30), datetime(1996, 1, 22, 10, 20, 30)),
    ),
)
def test_past_datetime_validation_success(value, result, past_datetime_type):
    class Model(BaseModel):
        foo: past_datetime_type

    assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value',
    (
        datetime.now() + timedelta(1),
        '2064-06-01T10:20:30',
    ),
)
def test_past_datetime_validation_fails(value, past_datetime_type):
    class Model(BaseModel):
        foo: past_datetime_type

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_past',
            'loc': ('foo',),
            'msg': 'Input should be in the past',
            'input': value,
        }
    ]


def test_future_datetime_validation_success(future_datetime_type):
    class Model(BaseModel):
        foo: future_datetime_type

    d = datetime.now() + timedelta(1)
    assert Model(foo=d).foo == d
    assert Model(foo='2064-06-01T10:20:30').foo == datetime(2064, 6, 1, 10, 20, 30)


@pytest.mark.parametrize(
    'value',
    (
        datetime.now(),
        datetime.now() - timedelta(1),
        '1996-01-22T10:20:30',
    ),
)
def test_future_datetime_validation_fails(value, future_datetime_type):
    class Model(BaseModel):
        foo: future_datetime_type

    with pytest.raises(ValidationError) as exc_info:
        Model(foo=value)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_future',
            'loc': ('foo',),
            'msg': 'Input should be in the future',
            'input': value,
        }
    ]


@pytest.mark.parametrize(
    'annotation',
    (
        PastDate,
        PastDatetime,
        FutureDate,
        FutureDatetime,
        NaiveDatetime,
        AwareDatetime,
    ),
)
def test_invalid_annotated_type(annotation):
    with pytest.raises(TypeError, match=f"'{annotation.__name__}' cannot annotate 'str'."):

        class Model(BaseModel):
            foo: Annotated[str, annotation()]


def test_tzinfo_could_be_reused():
    class Model(BaseModel):
        value: datetime

    m = Model(value='2015-10-21T15:28:00.000000+01:00')
    assert m.model_dump_json() == '{"value":"2015-10-21T15:28:00+01:00"}'

    target = datetime(1955, 11, 12, 14, 38, tzinfo=m.value.tzinfo)
    assert target == datetime(1955, 11, 12, 14, 38, tzinfo=timezone(timedelta(hours=1)))

    now = datetime.now(tz=m.value.tzinfo)
    assert isinstance(now, datetime)


def test_datetime_from_date_str():
    class Model(BaseModel):
        value: datetime

    m = Model(value='2015-10-21')
    assert m.value == datetime(2015, 10, 21, 0, 0)
