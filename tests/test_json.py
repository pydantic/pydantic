import datetime
import json
from decimal import Decimal
from enum import Enum
from uuid import UUID

import pytest

from pydantic import BaseModel, create_model
from pydantic.json import pydantic_encoder


class MyEnum(Enum):
    foo = 'bar'
    snap = 'crackle'


class IsoTimeDelta(datetime.timedelta):
    def json(self):
        """ Returns ISO 8601 encoding """
        seconds = self.total_seconds()
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        days, hours, minutes = map(int, (days, hours, minutes))
        seconds = round(seconds, 6)
        return f'P{days}DT{hours}H{minutes}M{seconds}S'


@pytest.mark.parametrize('input,output', [
    (UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), '"ebcdab58-6eb8-46fb-a190-d07a33e9eac8"'),
    (datetime.datetime(2032, 1, 1, 1, 1), '"2032-01-01T01:01:00"'),
    (datetime.datetime(2032, 1, 1, 1, 1, tzinfo=datetime.timezone.utc), '"2032-01-01T01:01:00+00:00"'),
    (datetime.datetime(2032, 1, 1), '"2032-01-01T00:00:00"'),
    (datetime.time(12, 34, 56), '"12:34:56"'),
    (datetime.timedelta(12, 34, 56), '"1036834.000056"'),
    (IsoTimeDelta(12, 34, 56), '"P12DT0H0M34.000056S"'),
    ({1, 2, 3}, '[1, 2, 3]'),
    (frozenset([1, 2, 3]), '[1, 2, 3]'),
    ((v for v in range(4)), '[0, 1, 2, 3]'),
    (b'this is bytes', '"this is bytes"'),
    (Decimal('12.34'), '12.34'),
    (create_model('BarModel', a='b', c='d')(), '{"a": "b", "c": "d"}'),
    (MyEnum.foo, '"bar"')
])
def test_encoding(input, output):
    assert json.dumps(input, default=pydantic_encoder) == output


def test_model_encoding():
    class ModelA(BaseModel):
        x: int
        y: str

    class Model(BaseModel):
        a: float
        b: bytes
        c: Decimal
        d: ModelA

    m = Model(a=10.2, b='foobar', c=10.2, d={'x': 123, 'y': '123'})
    assert m.dict() == {'a': 10.2, 'b': b'foobar', 'c': Decimal('10.2'), 'd': {'x': 123, 'y': '123'}}
    assert m.json() == '{"a": 10.2, "b": "foobar", "c": 10.2, "d": {"x": 123, "y": "123"}}'
    assert m.json(exclude={'b'}) == '{"a": 10.2, "c": 10.2, "d": {"x": 123, "y": "123"}}'


def test_invalid_model():
    class Foo:
        pass

    with pytest.raises(TypeError):
        json.dumps(Foo, default=pydantic_encoder)
