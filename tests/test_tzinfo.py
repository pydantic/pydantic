import copy
import functools
import pickle
import unittest
from datetime import datetime, timedelta, timezone, tzinfo

from pydantic_core import SchemaValidator, TzInfo, core_schema


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


def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += timedelta(days_to_go)
    return dt


DSTSTART = datetime(1, 4, 1, 2)
DSTEND = datetime(1, 10, 25, 1)


class TestTzInfo(unittest.TestCase):
    """Adapted from CPython `timezone` tests

    Original tests are located here https://github.com/python/cpython/blob/a0bb4a39d1ca10e4a75f50a9fbe90cc9db28d29e/Lib/test/datetimetester.py#L256
    """

    def setUp(self):
        self.ACDT = TzInfo(timedelta(hours=9.5).total_seconds())
        self.EST = TzInfo(-timedelta(hours=5).total_seconds())
        self.DT = datetime(2010, 1, 1)

    def test_str(self):
        for tz in [self.ACDT, self.EST]:
            self.assertEqual(str(tz), tz.tzname(None))

    def test_constructor(self):
        for subminute in [timedelta(microseconds=1), timedelta(seconds=1)]:
            tz = TzInfo(subminute.total_seconds())
            self.assertNotEqual(tz.utcoffset(None) % timedelta(minutes=1), 0)
        # invalid offsets
        for invalid in [timedelta(1, 1), timedelta(1)]:
            self.assertRaises(ValueError, TzInfo, invalid.total_seconds())
            self.assertRaises(ValueError, TzInfo, -invalid.total_seconds())

        with self.assertRaises(TypeError):
            TzInfo(None)
        with self.assertRaises(TypeError):
            TzInfo(timedelta(seconds=42))
        with self.assertRaises(TypeError):
            TzInfo(ZERO, None)
        with self.assertRaises(TypeError):
            TzInfo(ZERO, 42)
        with self.assertRaises(TypeError):
            TzInfo(ZERO, 'ABC', 'extra')

    def test_inheritance(self):
        self.assertIsInstance(self.EST, tzinfo)

    def test_utcoffset(self):
        dummy = self.DT
        for h in [0, 1.5, 12]:
            offset = h * HOUR
            self.assertEqual(timedelta(seconds=offset), TzInfo(offset).utcoffset(dummy))
            self.assertEqual(timedelta(seconds=-offset), TzInfo(-offset).utcoffset(dummy))

        self.assertEqual(self.EST.utcoffset(''), timedelta(hours=-5))
        self.assertEqual(self.EST.utcoffset(5), timedelta(hours=-5))

    def test_dst(self):
        self.EST.dst('') is None
        self.EST.dst(5) is None

    def test_tzname(self):
        self.assertEqual('-05:00', TzInfo(-5 * HOUR).tzname(None))
        self.assertEqual('+09:30', TzInfo(9.5 * HOUR).tzname(None))
        self.assertEqual('-00:01', TzInfo(timedelta(minutes=-1).total_seconds()).tzname(None))
        # Sub-minute offsets:
        self.assertEqual('+01:06:40', TzInfo(timedelta(0, 4000).total_seconds()).tzname(None))
        self.assertEqual('-01:06:40', TzInfo(-timedelta(0, 4000).total_seconds()).tzname(None))
        self.assertEqual('+01:06:40', TzInfo(timedelta(0, 4000, 1).total_seconds()).tzname(None))
        self.assertEqual('-01:06:40', TzInfo(-timedelta(0, 4000, 1).total_seconds()).tzname(None))

        self.assertEqual(self.EST.tzname(''), '-05:00')
        self.assertEqual(self.EST.tzname(5), '-05:00')

    def test_fromutc(self):
        for tz in [self.EST, self.ACDT]:
            utctime = self.DT.replace(tzinfo=tz)
            local = tz.fromutc(utctime)
            self.assertEqual(local - utctime, tz.utcoffset(local))
            self.assertEqual(local, self.DT.replace(tzinfo=timezone.utc))

    def test_comparison(self):
        self.assertNotEqual(TzInfo(ZERO), TzInfo(HOUR))
        self.assertEqual(TzInfo(HOUR), TzInfo(HOUR))
        self.assertFalse(TzInfo(ZERO) < TzInfo(ZERO))
        self.assertIn(TzInfo(ZERO), {TzInfo(ZERO)})
        self.assertTrue(TzInfo(ZERO) is not None)
        self.assertFalse(TzInfo(ZERO) is None)

        tz = TzInfo(ZERO)
        self.assertTrue(tz == ALWAYS_EQ)
        self.assertFalse(tz != ALWAYS_EQ)
        self.assertTrue(tz < LARGEST)
        self.assertFalse(tz > LARGEST)
        self.assertTrue(tz <= LARGEST)
        self.assertFalse(tz >= LARGEST)
        self.assertFalse(tz < SMALLEST)
        self.assertTrue(tz > SMALLEST)
        self.assertFalse(tz <= SMALLEST)
        self.assertTrue(tz >= SMALLEST)

    def test_copy(self):
        for tz in self.ACDT, self.EST:
            tz_copy = copy.copy(tz)
            self.assertEqual(tz_copy, tz)

    def test_deepcopy(self):
        for tz in self.ACDT, self.EST:
            tz_copy = copy.deepcopy(tz)
            self.assertEqual(tz_copy, tz)

    def test_offset_boundaries(self):
        # Test timedeltas close to the boundaries
        time_deltas = [timedelta(hours=23, minutes=59), timedelta(hours=23, minutes=59, seconds=59)]
        time_deltas.extend([-delta for delta in time_deltas])

        for delta in time_deltas:
            with self.subTest(test_type='good', delta=delta):
                print(delta.total_seconds())
                TzInfo(delta.total_seconds())

        # Test timedeltas on and outside the boundaries
        bad_time_deltas = [timedelta(hours=24), timedelta(hours=24, microseconds=1)]
        bad_time_deltas.extend([-delta for delta in bad_time_deltas])

        for delta in bad_time_deltas:
            with self.subTest(test_type='bad', delta=delta):
                with self.assertRaises(ValueError):
                    TzInfo(delta.total_seconds())


def test_tzinfo_could_be_reused():
    class Model:
        value: datetime

    v = SchemaValidator(
        core_schema.model_schema(
            Model, core_schema.model_fields_schema({'value': core_schema.model_field(core_schema.datetime_schema())})
        )
    )

    m = v.validate_python({'value': '2015-10-21T15:28:00.000000+01:00'})

    target = datetime(1955, 11, 12, 14, 38, tzinfo=m.value.tzinfo)
    assert target == datetime(1955, 11, 12, 14, 38, tzinfo=timezone(timedelta(hours=1)))

    now = datetime.now(tz=m.value.tzinfo)
    assert isinstance(now, datetime)
