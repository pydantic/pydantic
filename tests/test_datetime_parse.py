"""
Stolen from https://github.com/django/django/blob/master/tests/utils_tests/test_dateparse.py at
9718fa2e8abe430c3526a9278dd976443d4ae3c6

Changed to:
* use standard pytest layout
* parametrize tests
"""
from datetime import date, datetime, time, timedelta, timezone

import pytest

from pydantic import errors
from pydantic.datetime_parse import parse_date, parse_datetime, parse_duration, parse_time


def create_tz(minutes):
    return timezone(timedelta(minutes=minutes))


@pytest.mark.parametrize(
    'value,result',
    [
        # Valid inputs
        ('1494012444.883309', date(2017, 5, 5)),
        (1_494_012_444.883_309, date(2017, 5, 5)),
        ('1494012444', date(2017, 5, 5)),
        (1_494_012_444, date(2017, 5, 5)),
        (0, date(1970, 1, 1)),
        ('2012-04-23', date(2012, 4, 23)),
        ('2012-4-9', date(2012, 4, 9)),
        (date(2012, 4, 9), date(2012, 4, 9)),
        (datetime(2012, 4, 9, 12, 15), date(2012, 4, 9)),
        # Invalid inputs
        ('x20120423', errors.DateError),
        ('2012-04-56', errors.DateError),
    ],
)
def test_date_parsing(value, result):
    if result == errors.DateError:
        with pytest.raises(errors.DateError):
            parse_date(value)
    else:
        assert parse_date(value) == result


@pytest.mark.parametrize(
    'value,result',
    [
        # Valid inputs
        ('09:15:00', time(9, 15)),
        ('10:10', time(10, 10)),
        ('10:20:30.400', time(10, 20, 30, 400_000)),
        ('4:8:16', time(4, 8, 16)),
        (time(4, 8, 16), time(4, 8, 16)),
        # Invalid inputs
        ('091500', errors.TimeError),
        ('09:15:90', errors.TimeError),
    ],
)
def test_time_parsing(value, result):
    if result == errors.TimeError:
        with pytest.raises(errors.TimeError):
            parse_time(value)
    else:
        assert parse_time(value) == result


@pytest.mark.parametrize(
    'value,result',
    [
        # Valid inputs
        # values in seconds
        ('1494012444.883309', datetime(2017, 5, 5, 19, 27, 24, 883_309, tzinfo=timezone.utc)),
        (1_494_012_444.883_309, datetime(2017, 5, 5, 19, 27, 24, 883_309, tzinfo=timezone.utc)),
        ('1494012444', datetime(2017, 5, 5, 19, 27, 24, tzinfo=timezone.utc)),
        (1_494_012_444, datetime(2017, 5, 5, 19, 27, 24, tzinfo=timezone.utc)),
        # values in ms
        ('1494012444000.883309', datetime(2017, 5, 5, 19, 27, 24, 883, tzinfo=timezone.utc)),
        (1_494_012_444_000, datetime(2017, 5, 5, 19, 27, 24, tzinfo=timezone.utc)),
        ('2012-04-23T09:15:00', datetime(2012, 4, 23, 9, 15)),
        ('2012-4-9 4:8:16', datetime(2012, 4, 9, 4, 8, 16)),
        ('2012-04-23T09:15:00Z', datetime(2012, 4, 23, 9, 15, 0, 0, timezone.utc)),
        ('2012-4-9 4:8:16-0320', datetime(2012, 4, 9, 4, 8, 16, 0, create_tz(-200))),
        ('2012-04-23T10:20:30.400+02:30', datetime(2012, 4, 23, 10, 20, 30, 400_000, create_tz(150))),
        ('2012-04-23T10:20:30.400+02', datetime(2012, 4, 23, 10, 20, 30, 400_000, create_tz(120))),
        ('2012-04-23T10:20:30.400-02', datetime(2012, 4, 23, 10, 20, 30, 400_000, create_tz(-120))),
        (datetime(2017, 5, 5), datetime(2017, 5, 5)),
        (0, datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)),
        # Invalid inputs
        ('x20120423091500', errors.DateTimeError),
        ('2012-04-56T09:15:90', errors.DateTimeError),
    ],
)
def test_datetime_parsing(value, result):
    if result == errors.DateTimeError:
        with pytest.raises(errors.DateTimeError):
            parse_datetime(value)
    else:
        assert parse_datetime(value) == result


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
def test_parse_python_format(delta):
    assert parse_duration(delta) == delta
    assert parse_duration(str(delta)) == delta


@pytest.mark.parametrize(
    'value,result',
    [
        # seconds
        (timedelta(seconds=30), timedelta(seconds=30)),
        ('30', timedelta(seconds=30)),
        (30, timedelta(seconds=30)),
        (30.1, timedelta(seconds=30, milliseconds=100)),
        # minutes seconds
        ('15:30', timedelta(minutes=15, seconds=30)),
        ('5:30', timedelta(minutes=5, seconds=30)),
        # hours minutes seconds
        ('10:15:30', timedelta(hours=10, minutes=15, seconds=30)),
        ('1:15:30', timedelta(hours=1, minutes=15, seconds=30)),
        ('100:200:300', timedelta(hours=100, minutes=200, seconds=300)),
        # days
        ('4 15:30', timedelta(days=4, minutes=15, seconds=30)),
        ('4 10:15:30', timedelta(days=4, hours=10, minutes=15, seconds=30)),
        # fractions of seconds
        ('15:30.1', timedelta(minutes=15, seconds=30, milliseconds=100)),
        ('15:30.01', timedelta(minutes=15, seconds=30, milliseconds=10)),
        ('15:30.001', timedelta(minutes=15, seconds=30, milliseconds=1)),
        ('15:30.0001', timedelta(minutes=15, seconds=30, microseconds=100)),
        ('15:30.00001', timedelta(minutes=15, seconds=30, microseconds=10)),
        ('15:30.000001', timedelta(minutes=15, seconds=30, microseconds=1)),
        # negative
        ('-4 15:30', timedelta(days=-4, minutes=15, seconds=30)),
        ('-172800', timedelta(days=-2)),
        ('-15:30', timedelta(minutes=-15, seconds=30)),
        ('-1:15:30', timedelta(hours=-1, minutes=15, seconds=30)),
        ('-30.1', timedelta(seconds=-30, milliseconds=-100)),
        # iso_8601
        ('P4Y', errors.DurationError),
        ('P4M', errors.DurationError),
        ('P4W', errors.DurationError),
        ('P4D', timedelta(days=4)),
        ('P0.5D', timedelta(hours=12)),
        ('PT5H', timedelta(hours=5)),
        ('PT5M', timedelta(minutes=5)),
        ('PT5S', timedelta(seconds=5)),
        ('PT0.000005S', timedelta(microseconds=5)),
    ],
)
def test_parse_durations(value, result):
    if result == errors.DurationError:
        with pytest.raises(errors.DurationError):
            parse_duration(value)
    else:
        assert parse_duration(value) == result
