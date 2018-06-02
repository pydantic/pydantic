"""
Functions to parse datetime objects.

We're using regular expressions rather than time.strptime because:
- They provide both validation and parsing.
- They're more flexible for datetimes.
- The date/datetime/time constructors produce friendlier error messages.

Stolen from https://raw.githubusercontent.com/django/django/master/django/utils/dateparse.py at
9718fa2e8abe430c3526a9278dd976443d4ae3c6

Changed to:
* use standard python datetime types not django.utils.timezone
* raise ValueError when regex doesn't match rather than returning None
* support parsing unix timestamps for dates and datetimes
"""
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Union

from . import errors
from .utils import change_exception

date_re = re.compile(r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$')

time_re = re.compile(
    r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
)

datetime_re = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$'
)

standard_duration_re = re.compile(
    r'^'
    r'(?:(?P<days>-?\d+) (days?, )?)?'
    r'((?:(?P<hours>-?\d+):)(?=\d+:\d+))?'
    r'(?:(?P<minutes>-?\d+):)?'
    r'(?P<seconds>-?\d+)'
    r'(?:\.(?P<microseconds>\d{1,6})\d{0,6})?'
    r'$'
)

# Support the sections of ISO 8601 date representation that are accepted by timedelta
iso8601_duration_re = re.compile(
    r'^(?P<sign>[-+]?)'
    r'P'
    r'(?:(?P<days>\d+(.\d+)?)D)?'
    r'(?:T'
    r'(?:(?P<hours>\d+(.\d+)?)H)?'
    r'(?:(?P<minutes>\d+(.\d+)?)M)?'
    r'(?:(?P<seconds>\d+(.\d+)?)S)?'
    r')?'
    r'$'
)

EPOCH = datetime(1970, 1, 1)
MS_WATERSHED = int(1e11)  # if greater than this, the number is in ms (in seconds this is 3rd March 5138)
StrIntFloat = Union[str, int, float]


def get_numeric(value: StrIntFloat):
    if isinstance(value, (int, float)):
        return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass


def from_unix_seconds(seconds: int) -> datetime:
    while seconds > MS_WATERSHED:
        seconds /= 1000
    dt = EPOCH + timedelta(seconds=seconds)
    return dt.replace(tzinfo=timezone.utc)


def parse_date(value: Union[date, StrIntFloat]) -> date:
    """
    Parse a date/int/float/string and return a datetime.date.

    Raise ValueError if the input is well formatted but not a valid date.
    Raise ValueError if the input isn't well formatted.
    """
    if isinstance(value, date):
        return value

    number = get_numeric(value)
    if number is not None:
        return from_unix_seconds(number).date()

    match = date_re.match(value)
    if not match:
        raise errors.DateError()

    kw = {k: int(v) for k, v in match.groupdict().items()}

    with change_exception(errors.DateError, ValueError):
        return date(**kw)


def parse_time(value: Union[time, str]) -> time:
    """
    Parse a time/string and return a datetime.time.

    This function doesn't support time zone offsets.

    Raise ValueError if the input is well formatted but not a valid time.
    Raise ValueError if the input isn't well formatted, in particular if it contains an offset.
    """
    if isinstance(value, time):
        return value

    match = time_re.match(value)
    if not match:
        raise errors.TimeError()

    kw = match.groupdict()
    if kw['microsecond']:
        kw['microsecond'] = kw['microsecond'].ljust(6, '0')

    kw = {k: int(v) for k, v in kw.items() if v is not None}

    with change_exception(errors.TimeError, ValueError):
        return time(**kw)


def parse_datetime(value: Union[datetime, StrIntFloat]) -> datetime:
    """
    Parse a datetime/int/float/string and return a datetime.datetime.

    This function supports time zone offsets. When the input contains one,
    the output uses a timezone with a fixed offset from UTC.

    Raise ValueError if the input is well formatted but not a valid datetime.
    Raise ValueError if the input isn't well formatted.
    """
    if isinstance(value, datetime):
        return value

    number = get_numeric(value)
    if number is not None:
        return from_unix_seconds(number)

    match = datetime_re.match(value)
    if not match:
        raise errors.DateTimeError()

    kw = match.groupdict()
    if kw['microsecond']:
        kw['microsecond'] = kw['microsecond'].ljust(6, '0')

    tzinfo = kw.pop('tzinfo')
    if tzinfo == 'Z':
        tzinfo = timezone.utc
    elif tzinfo is not None:
        offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
        offset = 60 * int(tzinfo[1:3]) + offset_mins
        if tzinfo[0] == '-':
            offset = -offset
        tzinfo = timezone(timedelta(minutes=offset))

    kw = {k: int(v) for k, v in kw.items() if v is not None}
    kw['tzinfo'] = tzinfo

    with change_exception(errors.DateTimeError, ValueError):
        return datetime(**kw)


def parse_duration(value: StrIntFloat) -> timedelta:
    """
    Parse a duration int/float/string and return a datetime.timedelta.

    The preferred format for durations in Django is '%d %H:%M:%S.%f'.

    Also supports ISO 8601 representation.
    """
    if isinstance(value, (int, float)):
        # bellow code requires a string
        value = str(value)

    match = standard_duration_re.match(value) or iso8601_duration_re.match(value)
    if not match:
        raise errors.DurationError()

    kw = match.groupdict()
    sign = -1 if kw.pop('sign', '+') == '-' else 1
    if kw.get('microseconds'):
        kw['microseconds'] = kw['microseconds'].ljust(6, '0')

    if kw.get('seconds') and kw.get('microseconds') and kw['seconds'].startswith('-'):
        kw['microseconds'] = '-' + kw['microseconds']

    kw = {k: float(v) for k, v in kw.items() if v is not None}

    return sign * timedelta(**kw)
