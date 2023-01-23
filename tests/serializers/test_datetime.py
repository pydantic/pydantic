from datetime import date, datetime, time, timedelta, timezone

import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_datetime():
    v = SchemaSerializer(core_schema.datetime_schema())
    assert v.to_python(datetime(2022, 12, 2, 12, 13, 14)) == datetime(2022, 12, 2, 12, 13, 14)

    assert v.to_python(datetime(2022, 12, 2, 12, 13, 14), mode='json') == '2022-12-02T12:13:14'
    assert v.to_json(datetime(2022, 12, 2, 12, 13, 14)) == b'"2022-12-02T12:13:14"'

    with pytest.warns(UserWarning, match='Expected `datetime` but got `int` - serialized value may not be as expected'):
        assert v.to_python(123, mode='json') == 123

    with pytest.warns(UserWarning, match='Expected `datetime` but got `int` - serialized value may not be as expected'):
        assert v.to_json(123) == b'123'


def test_datetime_key():
    v = SchemaSerializer(core_schema.dict_schema(core_schema.datetime_schema(), core_schema.datetime_schema()))
    assert v.to_python({datetime(2022, 12, 2, 12, 13, 14): datetime(2022, 12, 2, 12, 13, 14)}) == {
        datetime(2022, 12, 2, 12, 13, 14): datetime(2022, 12, 2, 12, 13, 14)
    }
    assert v.to_python({datetime(2022, 12, 2, 12, 13, 14): datetime(2022, 12, 2, 12, 13, 14)}, mode='json') == {
        '2022-12-02T12:13:14': '2022-12-02T12:13:14'
    }
    assert (
        v.to_json({datetime(2022, 12, 2, 12, 13, 14): datetime(2022, 12, 2, 12, 13, 14)})
        == b'{"2022-12-02T12:13:14":"2022-12-02T12:13:14"}'
    )


def tz(**kwargs):
    return timezone(timedelta(**kwargs))


@pytest.mark.parametrize(
    'value,expected',
    [
        (datetime(2022, 12, 2, 12, 13, 14), '2022-12-02T12:13:14'),
        (datetime(2022, 12, 2, 12, tzinfo=timezone.utc), '2022-12-02T12:00:00Z'),
        (datetime(2022, 12, 2, 12, tzinfo=tz(hours=2)), '2022-12-02T12:00:00+02:00'),
        (datetime(2022, 12, 2, 12, tzinfo=tz(hours=2, minutes=30)), '2022-12-02T12:00:00+02:30'),
        (datetime(2022, 12, 2, 12, tzinfo=tz(hours=-2)), '2022-12-02T12:00:00-02:00'),
        (datetime(2022, 12, 2, 12, tzinfo=tz(hours=-2, minutes=-30)), '2022-12-02T12:00:00-02:30'),
        (datetime(2022, 12, 2, 12, 13, 14, 123456), '2022-12-02T12:13:14.123456'),
        (datetime(2022, 12, 2, 12, 13, 14, 123), '2022-12-02T12:13:14.000123'),
        (datetime(2022, 12, 2, 12, 13, 14, 123_000), '2022-12-02T12:13:14.123'),
        (datetime(2022, 12, 2, 12, 13, 14, 123456, tzinfo=tz(hours=-2)), '2022-12-02T12:13:14.123456-02:00'),
    ],
)
def test_datetime_json(value, expected):
    v = SchemaSerializer(core_schema.datetime_schema())
    assert v.to_python(value, mode='json') == expected
    assert v.to_json(value).decode() == f'"{expected}"'


def test_date():
    v = SchemaSerializer(core_schema.date_schema())
    assert v.to_python(date(2022, 12, 2)) == date(2022, 12, 2)

    assert v.to_python(date(2022, 12, 2), mode='json') == '2022-12-02'
    assert v.to_json(date(2022, 12, 2)) == b'"2022-12-02"'


def test_date_key():
    v = SchemaSerializer(core_schema.dict_schema(core_schema.date_schema(), core_schema.date_schema()))
    assert v.to_python({date(2022, 12, 2): date(2022, 12, 2)}) == {date(2022, 12, 2): date(2022, 12, 2)}
    assert v.to_python({date(2022, 12, 2): date(2022, 12, 2)}, mode='json') == {'2022-12-02': '2022-12-02'}
    assert v.to_json({date(2022, 12, 2): date(2022, 12, 2)}) == b'{"2022-12-02":"2022-12-02"}'


def test_time():
    v = SchemaSerializer(core_schema.time_schema())
    assert v.to_python(time(12, 13, 14)) == time(12, 13, 14)

    assert v.to_python(time(12, 13, 14), mode='json') == '12:13:14'
    assert v.to_python(time(12, 13, 14, 123456), mode='json') == '12:13:14.123456'

    assert v.to_json(time(12, 13, 14)) == b'"12:13:14"'
    assert v.to_json(time(12, 13, 14, 123_456)) == b'"12:13:14.123456"'
    assert v.to_json(time(12, 13, 14, 123)) == b'"12:13:14.000123"'
    assert v.to_json(time(12, 13, 14, 123_000)) == b'"12:13:14.123"'


def test_time_key():
    v = SchemaSerializer(core_schema.dict_schema(core_schema.time_schema(), core_schema.time_schema()))
    assert v.to_python({time(12, 13, 14): time(12, 13, 14)}) == {time(12, 13, 14): time(12, 13, 14)}
    assert v.to_python({time(12, 13, 14): time(12, 13, 14)}, mode='json') == {'12:13:14': '12:13:14'}
    assert v.to_json({time(12, 13, 14): time(12, 13, 14)}) == b'{"12:13:14":"12:13:14"}'


def test_any_datetime_key():
    v = SchemaSerializer(core_schema.dict_schema())
    input_value = {datetime(2022, 12, 2, 12, 13, 14): 1, date(2022, 12, 2): 2, time(12, 13, 14): 3}
    # assert v.to_python(input_value) == v
    assert v.to_python(input_value, mode='json') == {'2022-12-02T12:13:14': 1, '2022-12-02': 2, '12:13:14': 3}
    assert v.to_json(input_value) == b'{"2022-12-02T12:13:14":1,"2022-12-02":2,"12:13:14":3}'
