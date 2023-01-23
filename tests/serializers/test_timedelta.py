from datetime import timedelta

import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_timedelta():
    v = SchemaSerializer(core_schema.timedelta_schema())
    assert v.to_python(timedelta(days=2, hours=3, minutes=4)) == timedelta(days=2, hours=3, minutes=4)

    assert v.to_python(timedelta(days=2, hours=3, minutes=4), mode='json') == 'P2DT11040S'
    assert v.to_json(timedelta(days=2, hours=3, minutes=4)) == b'"P2DT11040S"'

    with pytest.warns(
        UserWarning, match='Expected `timedelta` but got `int` - serialized value may not be as expected'
    ):
        assert v.to_python(123, mode='json') == 123

    with pytest.warns(
        UserWarning, match='Expected `timedelta` but got `int` - serialized value may not be as expected'
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
    assert v.to_python({timedelta(days=2, hours=3, minutes=4): 1}, mode='json') == {'P2DT11040S': 1}
    assert v.to_json({timedelta(days=2, hours=3, minutes=4): 1}) == b'{"P2DT11040S":1}'
