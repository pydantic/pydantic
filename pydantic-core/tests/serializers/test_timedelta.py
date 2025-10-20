from datetime import timedelta

import pytest

from pydantic_core import SchemaSerializer, core_schema

try:
    import pandas
except ImportError:
    pandas = None


def test_timedelta():
    v = SchemaSerializer(core_schema.timedelta_schema())
    assert v.to_python(timedelta(days=2, hours=3, minutes=4)) == timedelta(days=2, hours=3, minutes=4)

    assert v.to_python(timedelta(days=2, hours=3, minutes=4), mode='json') == 'P2DT3H4M'
    assert v.to_json(timedelta(days=2, hours=3, minutes=4)) == b'"P2DT3H4M"'

    with pytest.warns(
        UserWarning,
        match=r'Expected `timedelta` - serialized value may not be as expected \[input_value=123, input_type=int\]',
    ):
        assert v.to_python(123, mode='json') == 123

    with pytest.warns(
        UserWarning,
        match=r'Expected `timedelta` - serialized value may not be as expected \[input_value=123, input_type=int\]',
    ):
        assert v.to_json(123) == b'123'


def test_timedelta_float():
    v = SchemaSerializer(core_schema.timedelta_schema(), config={'ser_json_timedelta': 'float'})
    assert v.to_python(timedelta(seconds=4, microseconds=500_000)) == timedelta(seconds=4, microseconds=500_000)

    assert v.to_python(timedelta(seconds=4, microseconds=500_000), mode='json') == 4.5
    assert v.to_json(timedelta(seconds=4, microseconds=500_000)) == b'4.5'


def test_timedelta_key():
    v = SchemaSerializer(core_schema.dict_schema(core_schema.timedelta_schema(), core_schema.int_schema()))
    assert v.to_python({timedelta(days=2, hours=3, minutes=4): 1}) == {timedelta(days=2, hours=3, minutes=4): 1}
    assert v.to_python({timedelta(days=2, hours=3, minutes=4): 1}, mode='json') == {'P2DT3H4M': 1}
    assert v.to_json({timedelta(days=2, hours=3, minutes=4): 1}) == b'{"P2DT3H4M":1}'


@pytest.mark.skipif(not pandas, reason='pandas not installed')
def test_pandas():
    v = SchemaSerializer(core_schema.timedelta_schema())
    d = pandas.Timestamp('2023-01-01T02:00:00Z') - pandas.Timestamp('2023-01-01T00:00:00Z')
    assert v.to_python(d) == d
    assert v.to_python(d, mode='json') == 'PT2H'
    assert v.to_json(d) == b'"PT2H"'


@pytest.mark.parametrize(
    'td,expected_to_python,expected_to_json,expected_to_python_dict,expected_to_json_dict,mode',
    [
        (timedelta(hours=2), 7200000.0, b'7200000.0', {'7200000': 'foo'}, b'{"7200000":"foo"}', 'milliseconds'),
        (
            timedelta(hours=-2),
            -7200000.0,
            b'-7200000.0',
            {'-7200000': 'foo'},
            b'{"-7200000":"foo"}',
            'milliseconds',
        ),
        (timedelta(seconds=1.5), 1500.0, b'1500.0', {'1500': 'foo'}, b'{"1500":"foo"}', 'milliseconds'),
        (timedelta(seconds=-1.5), -1500.0, b'-1500.0', {'-1500': 'foo'}, b'{"-1500":"foo"}', 'milliseconds'),
        (timedelta(microseconds=1), 0.001, b'0.001', {'0.001': 'foo'}, b'{"0.001":"foo"}', 'milliseconds'),
        (
            timedelta(microseconds=-1),
            -0.001,
            b'-0.001',
            {'-0.001': 'foo'},
            b'{"-0.001":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1),
            86400000.0,
            b'86400000.0',
            {'86400000': 'foo'},
            b'{"86400000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=-1),
            -86400000.0,
            b'-86400000.0',
            {'-86400000': 'foo'},
            b'{"-86400000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1, seconds=1),
            86401000.0,
            b'86401000.0',
            {'86401000': 'foo'},
            b'{"86401000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=-1, seconds=-1),
            -86401000.0,
            b'-86401000.0',
            {'-86401000': 'foo'},
            b'{"-86401000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1, seconds=-1),
            86399000.0,
            b'86399000.0',
            {'86399000': 'foo'},
            b'{"86399000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1, seconds=1, microseconds=1),
            86401000.001,
            b'86401000.001',
            {'86401000.001': 'foo'},
            b'{"86401000.001":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=-1, seconds=-1, microseconds=-1),
            -86401000.001,
            b'-86401000.001',
            {'-86401000.001': 'foo'},
            b'{"-86401000.001":"foo"}',
            'milliseconds',
        ),
        (timedelta(hours=2), 7200.0, b'7200.0', {'7200': 'foo'}, b'{"7200":"foo"}', 'seconds'),
        (timedelta(hours=-2), -7200.0, b'-7200.0', {'-7200': 'foo'}, b'{"-7200":"foo"}', 'seconds'),
        (timedelta(seconds=1.5), 1.5, b'1.5', {'1.5': 'foo'}, b'{"1.5":"foo"}', 'seconds'),
        (timedelta(seconds=-1.5), -1.5, b'-1.5', {'-1.5': 'foo'}, b'{"-1.5":"foo"}', 'seconds'),
        (timedelta(microseconds=1), 1e-6, b'1e-6', {'0.000001': 'foo'}, b'{"0.000001":"foo"}', 'seconds'),
        (
            timedelta(microseconds=-1),
            -1e-6,
            b'-1e-6',
            {'-0.000001': 'foo'},
            b'{"-0.000001":"foo"}',
            'seconds',
        ),
        (timedelta(days=1), 86400.0, b'86400.0', {'86400': 'foo'}, b'{"86400":"foo"}', 'seconds'),
        (timedelta(days=-1), -86400.0, b'-86400.0', {'-86400': 'foo'}, b'{"-86400":"foo"}', 'seconds'),
        (timedelta(days=1, seconds=1), 86401.0, b'86401.0', {'86401': 'foo'}, b'{"86401":"foo"}', 'seconds'),
        (
            timedelta(days=-1, seconds=-1),
            -86401.0,
            b'-86401.0',
            {'-86401': 'foo'},
            b'{"-86401":"foo"}',
            'seconds',
        ),
        (timedelta(days=1, seconds=-1), 86399.0, b'86399.0', {'86399': 'foo'}, b'{"86399":"foo"}', 'seconds'),
        (
            timedelta(days=1, seconds=1, microseconds=1),
            86401.000001,
            b'86401.000001',
            {'86401.000001': 'foo'},
            b'{"86401.000001":"foo"}',
            'seconds',
        ),
        (
            timedelta(days=-1, seconds=-1, microseconds=-1),
            -86401.000001,
            b'-86401.000001',
            {'-86401.000001': 'foo'},
            b'{"-86401.000001":"foo"}',
            'seconds',
        ),
    ],
)
def test_config_timedelta(
    td: timedelta, expected_to_python, expected_to_json, expected_to_python_dict, expected_to_json_dict, mode
):
    s = SchemaSerializer(core_schema.timedelta_schema(), config={'ser_json_temporal': mode})
    assert s.to_python(td) == td
    assert s.to_python(td, mode='json') == expected_to_python
    assert s.to_json(td) == expected_to_json
    assert s.to_python({td: 'foo'}) == {td: 'foo'}
    with pytest.warns(UserWarning):
        assert s.to_python({td: 'foo'}, mode='json') == expected_to_python_dict
    with pytest.warns(
        UserWarning,
    ):
        assert s.to_json({td: 'foo'}) == expected_to_json_dict


@pytest.mark.parametrize(
    'td,expected_to_python,expected_to_json,expected_to_python_dict,expected_to_json_dict,temporal_mode',
    [
        (timedelta(hours=2), 7200000.0, b'7200000.0', {'7200000': 'foo'}, b'{"7200000":"foo"}', 'milliseconds'),
        (
            timedelta(hours=-2),
            -7200000.0,
            b'-7200000.0',
            {'-7200000': 'foo'},
            b'{"-7200000":"foo"}',
            'milliseconds',
        ),
        (timedelta(seconds=1.5), 1500.0, b'1500.0', {'1500': 'foo'}, b'{"1500":"foo"}', 'milliseconds'),
        (timedelta(seconds=-1.5), -1500.0, b'-1500.0', {'-1500': 'foo'}, b'{"-1500":"foo"}', 'milliseconds'),
        (timedelta(microseconds=1), 0.001, b'0.001', {'0.001': 'foo'}, b'{"0.001":"foo"}', 'milliseconds'),
        (
            timedelta(microseconds=-1),
            -0.001,
            b'-0.001',
            {'-0.001': 'foo'},
            b'{"-0.001":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1),
            86400000.0,
            b'86400000.0',
            {'86400000': 'foo'},
            b'{"86400000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=-1),
            -86400000.0,
            b'-86400000.0',
            {'-86400000': 'foo'},
            b'{"-86400000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1, seconds=1),
            86401000.0,
            b'86401000.0',
            {'86401000': 'foo'},
            b'{"86401000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=-1, seconds=-1),
            -86401000.0,
            b'-86401000.0',
            {'-86401000': 'foo'},
            b'{"-86401000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1, seconds=-1),
            86399000.0,
            b'86399000.0',
            {'86399000': 'foo'},
            b'{"86399000":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=1, seconds=1, microseconds=1),
            86401000.001,
            b'86401000.001',
            {'86401000.001': 'foo'},
            b'{"86401000.001":"foo"}',
            'milliseconds',
        ),
        (
            timedelta(days=-1, seconds=-1, microseconds=-1),
            -86401000.001,
            b'-86401000.001',
            {'-86401000.001': 'foo'},
            b'{"-86401000.001":"foo"}',
            'milliseconds',
        ),
        (timedelta(hours=2), 7200.0, b'7200.0', {'7200': 'foo'}, b'{"7200":"foo"}', 'seconds'),
        (timedelta(hours=-2), -7200.0, b'-7200.0', {'-7200': 'foo'}, b'{"-7200":"foo"}', 'seconds'),
        (timedelta(seconds=1.5), 1.5, b'1.5', {'1.5': 'foo'}, b'{"1.5":"foo"}', 'seconds'),
        (timedelta(seconds=-1.5), -1.5, b'-1.5', {'-1.5': 'foo'}, b'{"-1.5":"foo"}', 'seconds'),
        (timedelta(microseconds=1), 1e-6, b'1e-6', {'0.000001': 'foo'}, b'{"0.000001":"foo"}', 'seconds'),
        (
            timedelta(microseconds=-1),
            -1e-6,
            b'-1e-6',
            {'-0.000001': 'foo'},
            b'{"-0.000001":"foo"}',
            'seconds',
        ),
        (timedelta(days=1), 86400.0, b'86400.0', {'86400': 'foo'}, b'{"86400":"foo"}', 'seconds'),
        (timedelta(days=-1), -86400.0, b'-86400.0', {'-86400': 'foo'}, b'{"-86400":"foo"}', 'seconds'),
        (timedelta(days=1, seconds=1), 86401.0, b'86401.0', {'86401': 'foo'}, b'{"86401":"foo"}', 'seconds'),
        (
            timedelta(days=-1, seconds=-1),
            -86401.0,
            b'-86401.0',
            {'-86401': 'foo'},
            b'{"-86401":"foo"}',
            'seconds',
        ),
        (timedelta(days=1, seconds=-1), 86399.0, b'86399.0', {'86399': 'foo'}, b'{"86399":"foo"}', 'seconds'),
        (
            timedelta(days=1, seconds=1, microseconds=1),
            86401.000001,
            b'86401.000001',
            {'86401.000001': 'foo'},
            b'{"86401.000001":"foo"}',
            'seconds',
        ),
        (
            timedelta(days=-1, seconds=-1, microseconds=-1),
            -86401.000001,
            b'-86401.000001',
            {'-86401.000001': 'foo'},
            b'{"-86401.000001":"foo"}',
            'seconds',
        ),
    ],
)
@pytest.mark.parametrize('timedelta_mode', ['iso8601', 'float'])
def test_config_timedelta_timedelta_ser_flag_prioritised(
    td: timedelta,
    expected_to_python,
    expected_to_json,
    expected_to_python_dict,
    expected_to_json_dict,
    temporal_mode,
    timedelta_mode,
):
    s = SchemaSerializer(
        core_schema.timedelta_schema(),
        config={'ser_json_temporal': temporal_mode, 'ser_json_timedelta': timedelta_mode},
    )
    assert s.to_python(td) == td
    assert s.to_python(td, mode='json') == expected_to_python
    assert s.to_python({td: 'foo'}) == {td: 'foo'}

    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `timedelta` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.timedelta\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_python({td: 'foo'}, mode='json') == expected_to_python_dict
    with pytest.warns(
        UserWarning,
        match=(
            r'Expected `timedelta` - serialized value may not be as expected '
            r"\[input_value=\{datetime\.timedelta\([^)]*\): 'foo'\}, input_type=dict\]"
        ),
    ):
        assert s.to_json({td: 'foo'}) == expected_to_json_dict
