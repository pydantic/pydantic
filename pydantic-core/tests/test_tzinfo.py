"""Adapted from CPython `timezone` tests.

Original tests are located here https://github.com/python/cpython/blob/a0bb4a39d1ca10e4a75f50a9fbe90cc9db28d29e/Lib/test/datetimetester.py#L256
"""

import copy
import functools
import pickle
import sys
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest
from pydantic import TypeAdapter

from pydantic_core import TzInfo


class _ALWAYS_EQ:
    """
    Object that is equal to anything.
    """

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


ALWAYS_EQ = _ALWAYS_EQ()


@functools.total_ordering
class _LARGEST:
    """
    Object that is greater than anything (except itself).
    """

    def __eq__(self, other):
        return isinstance(other, _LARGEST)

    def __lt__(self, other):
        return False


LARGEST = _LARGEST()


@functools.total_ordering
class _SMALLEST:
    """
    Object that is less than anything (except itself).
    """

    def __eq__(self, other):
        return isinstance(other, _SMALLEST)

    def __gt__(self, other):
        return False


SMALLEST = _SMALLEST()


pickle_choices = [(pickle, pickle, proto) for proto in range(pickle.HIGHEST_PROTOCOL + 1)]

HOUR = timedelta(hours=1).total_seconds()
ZERO = timedelta(0).total_seconds()

ACDT = TzInfo(timedelta(hours=9.5).total_seconds())
EST = TzInfo(-timedelta(hours=5).total_seconds())
UTC = TzInfo(timedelta(0).total_seconds())
DT = datetime(2010, 1, 1)


@pytest.mark.parametrize('tz', [ACDT, EST])
def test_str(tz):
    assert str(tz) == tz.tzname(None)


def test_constructor():
    for subminute in [timedelta(microseconds=1), timedelta(seconds=1)]:
        tz = TzInfo(subminute.total_seconds())
        assert tz.utcoffset(None) % timedelta(minutes=1) != 0
    # invalid offsets
    for invalid in [timedelta(1, 1), timedelta(1)]:
        with pytest.raises(ValueError):
            TzInfo(invalid.total_seconds())
        with pytest.raises(ValueError):
            TzInfo(-invalid.total_seconds())

    with pytest.raises(TypeError):
        TzInfo(None)
    with pytest.raises(TypeError):
        TzInfo(timedelta(seconds=42))
    with pytest.raises(TypeError):
        TzInfo(ZERO, None)
    with pytest.raises(TypeError):
        TzInfo(ZERO, 42)
    with pytest.raises(TypeError):
        TzInfo(ZERO, 'ABC', 'extra')


def test_inheritance():
    assert isinstance(EST, tzinfo)


def test_utcoffset():
    dummy = DT
    for h in [0, 1.5, 12]:
        offset = h * HOUR
        assert timedelta(seconds=offset) == TzInfo(offset).utcoffset(dummy)
        assert timedelta(seconds=-offset) == TzInfo(-offset).utcoffset(dummy)

    assert EST.utcoffset('') == timedelta(hours=-5)
    assert EST.utcoffset(5) == timedelta(hours=-5)


def test_dst():
    assert EST.dst('') is None
    assert EST.dst(5) is None


def test_tzname():
    assert TzInfo(-5 * HOUR).tzname(None) == '-05:00'
    assert TzInfo(9.5 * HOUR).tzname(None) == '+09:30'
    assert TzInfo(timedelta(minutes=-1).total_seconds()).tzname(None) == '-00:01'
    # Sub-minute offsets:
    assert TzInfo(timedelta(0, 4000).total_seconds()).tzname(None) == '+01:06:40'
    assert TzInfo(-timedelta(0, 4000).total_seconds()).tzname(None) == '-01:06:40'
    assert TzInfo(timedelta(0, 4000, 1).total_seconds()).tzname(None) == '+01:06:40'
    assert TzInfo(-timedelta(0, 4000, 1).total_seconds()).tzname(None) == '-01:06:40'

    assert EST.tzname('') == '-05:00'
    assert EST.tzname(5) == '-05:00'


@pytest.mark.parametrize('tz', [EST, ACDT])
def test_fromutc(tz):
    utctime = DT.replace(tzinfo=tz)
    local = tz.fromutc(utctime)
    assert local - utctime == tz.utcoffset(local)
    assert local == DT.replace(tzinfo=timezone.utc)


def test_comparison():
    assert TzInfo(ZERO) != TzInfo(HOUR)
    assert TzInfo(HOUR) == TzInfo(HOUR)
    assert not TzInfo(ZERO) < TzInfo(ZERO)
    assert TzInfo(ZERO) in {TzInfo(ZERO)}
    assert TzInfo(ZERO) is not None

    tz = TzInfo(ZERO)
    assert tz == ALWAYS_EQ
    assert not tz != ALWAYS_EQ
    assert tz < LARGEST
    assert not tz > LARGEST
    assert tz <= LARGEST
    assert not tz >= LARGEST
    assert not tz < SMALLEST
    assert tz > SMALLEST
    assert not tz <= SMALLEST
    assert tz >= SMALLEST

    # offset based comparison tests for tzinfo derived classes like datetime.timezone.
    utcdatetime = DT.replace(tzinfo=timezone.utc)
    assert tz == utcdatetime.tzinfo
    estdatetime = DT.replace(tzinfo=timezone(-timedelta(hours=5)))
    assert EST == estdatetime.tzinfo
    assert tz > estdatetime.tzinfo

    if sys.platform == 'linux':
        try:
            europe_london = ZoneInfo('Europe/London')
        except ZoneInfoNotFoundError:
            # tz data not available
            pass
        else:
            assert not tz == europe_london
            with pytest.raises(TypeError):
                tz > europe_london


@pytest.mark.parametrize('tz', [ACDT, EST])
def test_copy(tz):
    tz_copy = copy.copy(tz)
    assert tz_copy == tz


@pytest.mark.parametrize('tz', [ACDT, EST])
def test_deepcopy(tz):
    tz_copy = copy.deepcopy(tz)
    assert tz_copy == tz


@pytest.mark.parametrize(
    'delta',
    [
        # Test timedeltas close to the boundaries
        timedelta(hours=23, minutes=59),
        timedelta(hours=23, minutes=59, seconds=59),
        -timedelta(hours=23, minutes=59),
        -timedelta(hours=23, minutes=59, seconds=59),
    ],
)
def test_offset_boundaries_valid(delta):
    TzInfo(delta.total_seconds())


@pytest.mark.parametrize(
    'delta',
    [
        # Test timedeltas on and outside the boundaries
        timedelta(hours=24),
        timedelta(hours=24, microseconds=1),
        -timedelta(hours=24),
        -timedelta(hours=24, microseconds=1),
    ],
)
def test_offset_boundaries_invalid(delta):
    with pytest.raises(ValueError):
        TzInfo(delta.total_seconds())


def test_no_args_constructor():
    # Test that TzInfo can be constructed without arguments
    tz = TzInfo()
    assert tz.utcoffset(None) == timedelta(0)
    assert str(tz) == 'UTC'


@pytest.mark.parametrize('tz', [ACDT, EST, UTC])
@pytest.mark.parametrize(('pickler', 'unpickler', 'proto'), pickle_choices)
def test_pickle(tz, pickler, unpickler, proto):
    # Test that TzInfo can be pickled and unpickled
    pickled = pickler.dumps(tz, proto)
    unpickled = unpickler.loads(pickled)
    assert tz == unpickled
    assert tz.utcoffset(None) == unpickled.utcoffset(None)


def test_tzinfo_could_be_reused():
    value = TypeAdapter(datetime).validate_python('2015-10-21T15:28:00.000000+01:00')

    target = datetime(1955, 11, 12, 14, 38, tzinfo=value.tzinfo)
    assert target == datetime(1955, 11, 12, 14, 38, tzinfo=timezone(timedelta(hours=1)))

    now = datetime.now(tz=value.tzinfo)
    assert isinstance(now, datetime)
