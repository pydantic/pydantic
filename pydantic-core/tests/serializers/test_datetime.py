from datetime import date, datetime, time, timedelta, timezone

import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_datetime():
    v = SchemaSerializer(core_schema.datetime_schema())
    assert v.to_python(datetime(2022, 12, 2, 12, 13, 14)) == datetime(2022, 12, 2, 12, 13, 14)

    assert v.to_python(datetime(2022, 12, 2, 12, 13, 14), mode='json') == '2022-12-02T12:13:14'
    assert v.to_json(datetime(2022, 12, 2, 12, 13, 14)) == b'"2022-12-02T12:13:14"'

    with pytest.warns(
        UserWarning,
        match=r'Expected `datetime` - serialized value may not be as expected \[input_value=123, input_type=int\]',
    ):
        assert v.to_python(123, mode='json') == 123

    with pytest.warns(
        UserWarning,
        match=r'Expected `datetime` - serialized value may not be as expected \[input_value=123, input_type=int\]',
    ):
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
        (datetime(2022, 12, 2, 12, 13, 14, 123_000), '2022-12-02T12:13:14.123000'),
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
    assert v.to_json(time(12, 13, 14, 123_000)) == b'"12:13:14.123000"'


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


def test_date_datetime_union():
    # See https://github.com/pydantic/pydantic/issues/7039#issuecomment-1671986746
    v = SchemaSerializer(core_schema.union_schema([core_schema.date_schema(), core_schema.datetime_schema()]))
    assert v.to_python(datetime(2022, 12, 2, 1)) == datetime(2022, 12, 2, 1)
    assert v.to_python(datetime(2022, 12, 2, 1), mode='json') == '2022-12-02T01:00:00'
    assert v.to_json(datetime(2022, 12, 2, 1)) == b'"2022-12-02T01:00:00"'


@pytest.mark.parametrize(
    'dt,expected_to_python,expected_to_json,expected_to_python_dict,expected_to_json_dict,mode',
    [
        (
            datetime(2024, 1, 1, 0, 0, 0),
            '2024-01-01T00:00:00',
            b'"2024-01-01T00:00:00"',
            {'2024-01-01T00:00:00': 'foo'},
            b'{"2024-01-01T00:00:00":"foo"}',
            'iso8601',
        ),
        (
            datetime(2024, 1, 1, 0, 0, 0),
            1704067200.0,
            b'1704067200.0',
            {'1704067200': 'foo'},
            b'{"1704067200":"foo"}',
            'seconds',
        ),
        (
            datetime(2024, 1, 1, 0, 0, 0),
            1704067200000.0,
            b'1704067200000.0',
            {'1704067200000': 'foo'},
            b'{"1704067200000":"foo"}',
            'milliseconds',
        ),
        (
            datetime(2024, 1, 1, 1, 1, 1, 23),
            1704070861.000023,
            b'1704070861.000023',
            {'1704070861.000023': 'foo'},
            b'{"1704070861.000023":"foo"}',
            'seconds',
        ),
        (
            datetime(2024, 1, 1, 1, 1, 1, 23),
            1704070861000.023,
            b'1704070861000.023',
            {'1704070861000.023': 'foo'},
            b'{"1704070861000.023":"foo"}',
            'milliseconds',
        ),
    ],
)
def test_config_datetime(
    dt: datetime, expected_to_python, expected_to_json, expected_to_python_dict, expected_to_json_dict, mode
):
    s = SchemaSerializer(core_schema.datetime_schema(), config={'ser_json_temporal': mode})
    assert s.to_python(dt) == dt
    assert s.to_python(dt, mode='json') == expected_to_python
    assert s.to_json(dt) == expected_to_json

    assert s.to_python({dt: 'foo'}) == {dt: 'foo'}
    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `datetime` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.datetime\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_python({dt: 'foo'}, mode='json') == expected_to_python_dict
    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `datetime` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.datetime\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_json({dt: 'foo'}) == expected_to_json_dict


@pytest.mark.parametrize(
    'dt,expected_to_python,expected_to_json,expected_to_python_dict,expected_to_json_dict,mode',
    [
        (
            date(2024, 1, 1),
            '2024-01-01',
            b'"2024-01-01"',
            {'2024-01-01': 'foo'},
            b'{"2024-01-01":"foo"}',
            'iso8601',
        ),
        (
            date(2024, 1, 1),
            1704067200.0,
            b'1704067200.0',
            {'1704067200': 'foo'},
            b'{"1704067200":"foo"}',
            'seconds',
        ),
        (
            date(2024, 1, 1),
            1704067200000.0,
            b'1704067200000.0',
            {'1704067200000': 'foo'},
            b'{"1704067200000":"foo"}',
            'milliseconds',
        ),
    ],
)
def test_config_date(
    dt: date, expected_to_python, expected_to_json, expected_to_python_dict, expected_to_json_dict, mode
):
    s = SchemaSerializer(core_schema.date_schema(), config={'ser_json_temporal': mode})
    assert s.to_python(dt) == dt
    assert s.to_python(dt, mode='json') == expected_to_python
    assert s.to_json(dt) == expected_to_json

    assert s.to_python({dt: 'foo'}) == {dt: 'foo'}
    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `date` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.date\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_python({dt: 'foo'}, mode='json') == expected_to_python_dict
    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `date` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.date\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_json({dt: 'foo'}) == expected_to_json_dict


@pytest.mark.parametrize(
    't,expected_to_python,expected_to_json,expected_to_python_dict,expected_to_json_dict,mode',
    [
        (
            time(3, 14, 1, 59263),
            '03:14:01.059263',
            b'"03:14:01.059263"',
            {'03:14:01.059263': 'foo'},
            b'{"03:14:01.059263":"foo"}',
            'iso8601',
        ),
        (
            time(3, 14, 1, 59263),
            11641.059263,
            b'11641.059263',
            {'11641.059263': 'foo'},
            b'{"11641.059263":"foo"}',
            'seconds',
        ),
        (
            time(3, 14, 1, 59263),
            11641059.263,
            b'11641059.263',
            {'11641059.263': 'foo'},
            b'{"11641059.263":"foo"}',
            'milliseconds',
        ),
    ],
)
def test_config_time(
    t: date, expected_to_python, expected_to_json, expected_to_python_dict, expected_to_json_dict, mode
):
    s = SchemaSerializer(core_schema.time_schema(), config={'ser_json_temporal': mode})
    assert s.to_python(t) == t
    assert s.to_python(t, mode='json') == expected_to_python
    assert s.to_json(t) == expected_to_json

    assert s.to_python({t: 'foo'}) == {t: 'foo'}
    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `time` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.time\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_python({t: 'foo'}, mode='json') == expected_to_python_dict
    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `time` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.time\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_json({t: 'foo'}) == expected_to_json_dict
