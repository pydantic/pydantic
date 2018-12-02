import datetime
import json
from decimal import Decimal
from enum import Enum
from uuid import UUID

import pytest

from pydantic import BaseModel, create_model
from pydantic.json import jsonable_encoder, model_dict_jsonable, pydantic_encoder, timedelta_isoformat


class MyEnum(Enum):
    foo = 'bar'
    snap = 'crackle'


@pytest.mark.parametrize(
    'input,output',
    [
        (UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), '"ebcdab58-6eb8-46fb-a190-d07a33e9eac8"'),
        (datetime.datetime(2032, 1, 1, 1, 1), '"2032-01-01T01:01:00"'),
        (datetime.datetime(2032, 1, 1, 1, 1, tzinfo=datetime.timezone.utc), '"2032-01-01T01:01:00+00:00"'),
        (datetime.datetime(2032, 1, 1), '"2032-01-01T00:00:00"'),
        (datetime.time(12, 34, 56), '"12:34:56"'),
        (datetime.timedelta(days=12, seconds=34, microseconds=56), '1036834.000056'),
        ({1, 2, 3}, '[1, 2, 3]'),
        (frozenset([1, 2, 3]), '[1, 2, 3]'),
        ((v for v in range(4)), '[0, 1, 2, 3]'),
        (b'this is bytes', '"this is bytes"'),
        (Decimal('12.34'), '12.34'),
        (create_model('BarModel', a='b', c='d')(), '{"a": "b", "c": "d"}'),
        (MyEnum.foo, '"bar"'),
    ],
)
def test_encoding(input, output):
    assert output == json.dumps(input, default=pydantic_encoder)


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


@pytest.mark.parametrize(
    'input,output',
    [
        (datetime.timedelta(days=12, seconds=34, microseconds=56), 'P12DT0H0M34.000056S'),
        (datetime.timedelta(days=1001, hours=1, minutes=2, seconds=3, microseconds=654_321), 'P1001DT1H2M3.654321S'),
    ],
)
def test_iso_timedelta(input, output):
    assert output == timedelta_isoformat(input)


def test_custom_encoder():
    class Model(BaseModel):
        x: datetime.timedelta
        y: Decimal
        z: datetime.date

        class Config:
            json_encoders = {datetime.timedelta: lambda v: f'{v.total_seconds():0.3f}s', Decimal: lambda v: 'a decimal'}

    assert Model(x=123, y=5, z='2032-06-01').json() == '{"x": "123.000s", "y": "a decimal", "z": "2032-06-01"}'


def test_custom_iso_timedelta():
    class Model(BaseModel):
        x: datetime.timedelta

        class Config:
            json_encoders = {datetime.timedelta: timedelta_isoformat}

    m = Model(x=123)
    assert m.json() == '{"x": "P0DT0H2M3.000000S"}'


def test_custom_encoder_arg():
    class Model(BaseModel):
        x: datetime.timedelta

    m = Model(x=123)
    assert m.json() == '{"x": 123.0}'
    assert m.json(encoder=lambda v: '__default__') == '{"x": "__default__"}'


@pytest.mark.parametrize(
    'input,output',
    [
        (UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), 'ebcdab58-6eb8-46fb-a190-d07a33e9eac8'),
        (datetime.datetime(2032, 1, 1, 1, 1), '2032-01-01T01:01:00'),
        (datetime.datetime(2032, 1, 1, 1, 1, tzinfo=datetime.timezone.utc), '2032-01-01T01:01:00+00:00'),
        (datetime.datetime(2032, 1, 1), '2032-01-01T00:00:00'),
        (datetime.time(12, 34, 56), '12:34:56'),
        (datetime.timedelta(days=12, seconds=34, microseconds=56), 1_036_834.000_056),
        (b'this is bytes', 'this is bytes'),
        (Decimal('12.34'), 12.34),
        (create_model('BarModel', a='b', c='d')(), {"a": "b", "c": "d"}),
        (MyEnum.foo, 'bar'),
        ('a', 'a'),
        (1, 1),
        (2.5, 2.5),
        (True, True),
        (None, None),
        ({'a': 'a'}, {'a': 'a'}),
        ({'a': MyEnum.foo}, {'a': 'bar'}),
        ({MyEnum.foo: 2}, {'bar': 2}),
        ({3.0: True}, {3.0: True}),
        ([1, 2, 3], [1, 2, 3]),
        (set([1, 2, 3]), [1, 2, 3]),
        (frozenset([1, 2, 3]), [1, 2, 3]),
        ((v for v in range(4)), [0, 1, 2, 3]),
        ((1, 2, 3), [1, 2, 3]),
    ],
)
def test_jsonable(input, output):
    assert output == jsonable_encoder(input)


def test_invalid_model_jsonable():
    class Foo:
        pass

    with pytest.raises(TypeError):
        jsonable_encoder(Foo)


def test_model_jsonable():
    class ModelA(BaseModel):
        x: int
        y: str

    class Model(BaseModel):
        a: float
        b: bytes
        c: Decimal
        d: ModelA
        e: MyEnum

    m = Model(a=10.2, b='foobar', c=10.2, d={'x': 123, 'y': '123'}, e=MyEnum.foo)
    assert m.dict_jsonable() == {'a': 10.2, 'b': 'foobar', 'c': 10.2, 'd': {'x': 123, 'y': '123'}, 'e': 'bar'}
    assert m.dict_jsonable(exclude={'b'}) == {'a': 10.2, 'c': 10.2, 'd': {'x': 123, 'y': '123'}, 'e': 'bar'}
