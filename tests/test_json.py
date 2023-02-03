import json
import re
import sys
from dataclasses import dataclass as vanilla_dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import Generator, Optional, Pattern
from uuid import UUID

import pytest
from pydantic_core import SchemaSerializer

from pydantic import BaseModel, NameEmail, serializer
from pydantic._internal._generate_schema import GenerateSchema
from pydantic.color import Color
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.json import pydantic_encoder, timedelta_isoformat
from pydantic.types import DirectoryPath, FilePath, SecretBytes, SecretStr, condecimal

try:
    import email_validator
except ImportError:
    email_validator = None


class MyEnum(Enum):
    foo = 'bar'
    snap = 'crackle'


class MyModel(BaseModel):
    a: str = 'b'
    c: str = 'd'


@pytest.mark.parametrize(
    'ser_type,gen_value,json_output',
    [
        (UUID, lambda: 'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', b'"ebcdab58-6eb8-46fb-a190-d07a33e9eac8"'),
        (IPv4Address, lambda: '192.168.0.1', b'"192.168.0.1"'),
        (Color, lambda: Color('#000'), b'"black"'),
        (Color, lambda: Color((1, 12, 123)), b'"#010c7b"'),
        (SecretStr, lambda: SecretStr('abcd'), b'"**********"'),
        (SecretStr, lambda: SecretStr(''), b'""'),
        (SecretBytes, lambda: SecretBytes(b'xyz'), b'"**********"'),
        (SecretBytes, lambda: SecretBytes(b''), b'""'),
        (IPv6Address, lambda: IPv6Address('::1:0:1'), b'"::1:0:1"'),
        (IPv4Interface, lambda: IPv4Interface('192.168.0.0/24'), b'"192.168.0.0/24"'),
        (IPv6Interface, lambda: IPv6Interface('2001:db00::/120'), b'"2001:db00::/120"'),
        (IPv4Network, lambda: IPv4Network('192.168.0.0/24'), b'"192.168.0.0/24"'),
        (IPv6Network, lambda: IPv6Network('2001:db00::/120'), b'"2001:db00::/120"'),
        (datetime, lambda: datetime(2032, 1, 1, 1, 1), b'"2032-01-01T01:01:00"'),
        (datetime, lambda: datetime(2032, 1, 1, 1, 1, tzinfo=timezone.utc), b'"2032-01-01T01:01:00Z"'),
        (datetime, lambda: datetime(2032, 1, 1), b'"2032-01-01T00:00:00"'),
        (time, lambda: time(12, 34, 56), b'"12:34:56"'),
        (timedelta, lambda: timedelta(days=12, seconds=34, microseconds=56), b'"P12DT34.000056S"'),
        (timedelta, lambda: timedelta(seconds=-1), b'"-PT1S"'),
        (set, lambda: {1, 2, 3}, b'[1,2,3]'),
        (frozenset, lambda: frozenset([1, 2, 3]), b'[1,2,3]'),
        (Generator[int, None, None], lambda: (v for v in range(4)), b'[0,1,2,3]'),
        (bytes, lambda: b'this is bytes', b'"this is bytes"'),
        (Decimal, lambda: Decimal('12.34'), b'"12.34"'),
        (MyModel, lambda: MyModel(), b'{"a":"b","c":"d"}'),
        (MyEnum, lambda: MyEnum.foo, b'"bar"'),
        (Pattern, lambda: re.compile('^regex$'), b'"^regex$"'),
    ],
)
def test_json_serialization(ser_type, gen_value, json_output):
    gen = GenerateSchema(False, None)
    schema = gen.generate_schema(ser_type)
    serializer = SchemaSerializer(schema)
    assert serializer.to_json(gen_value()) == json_output


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_json_serialization_email():
    gen = GenerateSchema(False, None)
    schema = gen.generate_schema(NameEmail)
    serializer = SchemaSerializer(schema)
    assert serializer.to_json(NameEmail('foo bar', 'foobaR@example.com')) == b'"foo bar <foobaR@example.com>"'


@pytest.mark.skipif(sys.platform.startswith('win'), reason='paths look different on windows')
def test_path_encoding(tmpdir):
    class PathModel(BaseModel):
        path: Path
        file_path: FilePath
        dir_path: DirectoryPath

    tmpdir = Path(tmpdir)
    file_path = tmpdir / 'bar'
    file_path.touch()
    dir_path = tmpdir / 'baz'
    dir_path.mkdir()
    model = PathModel(path=Path('/path/test/example/'), file_path=file_path, dir_path=dir_path)
    expected = f'{{"path": "/path/test/example", "file_path": "{file_path}", "dir_path": "{dir_path}"}}'
    assert json.dumps(model, default=pydantic_encoder) == expected


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
    assert m.model_dump() == {'a': 10.2, 'b': b'foobar', 'c': Decimal('10.2'), 'd': {'x': 123, 'y': '123'}}
    assert m.model_dump_json() == b'{"a":10.2,"b":"foobar","c":"10.2","d":{"x":123,"y":"123"}}'
    assert m.model_dump_json(exclude={'b'}) == b'{"a":10.2,"c":"10.2","d":{"x":123,"y":"123"}}'


def test_subclass_encoding():
    class SubDate(datetime):
        pass

    class Model(BaseModel):
        a: datetime
        b: SubDate

    m = Model(a=datetime(2032, 1, 1, 1, 1), b=SubDate(2020, 2, 29, 12, 30))
    assert m.model_dump() == {'a': datetime(2032, 1, 1, 1, 1), 'b': SubDate(2020, 2, 29, 12, 30)}
    assert m.model_dump_json() == b'{"a":"2032-01-01T01:01:00","b":"2020-02-29T12:30:00"}'


# @pytest.mark.xfail(reason='working on V2')
def test_subclass_custom_encoding():
    class SubDt(datetime):
        pass

    class SubDelta(timedelta):
        pass

    class Model(BaseModel):
        a: SubDt
        b: SubDelta

        @serializer('a', when_used='json')
        def serialize_a(self, v: SubDt, _info):
            return v.strftime('%a, %d %b %C %H:%M:%S')

        class Config:
            ser_json_timedelta = 'float'

    m = Model(a=SubDt(2032, 1, 1, 1, 1), b=SubDelta(hours=100))
    assert m.model_dump() == {'a': SubDt(2032, 1, 1, 1, 1), 'b': SubDelta(days=4, seconds=14400)}
    assert m.model_dump(mode='json') == {'a': 'Thu, 01 Jan 20 01:01:00', 'b': 360000.0}
    assert m.model_dump_json() == b'{"a":"Thu, 01 Jan 20 01:01:00","b":360000.0}'


def test_invalid_model():
    class Foo:
        pass

    with pytest.raises(TypeError):
        json.dumps(Foo, default=pydantic_encoder)


@pytest.mark.parametrize(
    'input,output',
    [
        (timedelta(days=12, seconds=34, microseconds=56), 'P12DT0H0M34.000056S'),
        (timedelta(days=1001, hours=1, minutes=2, seconds=3, microseconds=654_321), 'P1001DT1H2M3.654321S'),
        (timedelta(seconds=-1), '-P1DT23H59M59.000000S'),
        (timedelta(), 'P0DT0H0M0.000000S'),
    ],
)
def test_iso_timedelta(input, output):
    assert output == timedelta_isoformat(input)


def test_custom_encoder():
    class Model(BaseModel):
        x: timedelta
        y: Decimal
        z: date

        @serializer('x')
        def serialize_x(self, v: timedelta, _info):
            return f'{v.total_seconds():0.3f}s'

        @serializer('y')
        def serialize_y(self, v: Decimal, _info):
            return 'a decimal'

    assert Model(x=123, y=5, z='2032-06-01').model_dump_json() == b'{"x":"123.000s","y":"a decimal","z":"2032-06-01"}'


def test_iso_timedelta_simple():
    class Model(BaseModel):
        x: timedelta

    m = Model(x=123)
    json_data = m.model_dump_json()
    assert json_data == b'{"x":"PT123S"}'
    assert Model.model_validate_json(json_data).x == timedelta(seconds=123)


def test_con_decimal_encode() -> None:
    """
    Makes sure a decimal with decimal_places = 0, as well as one with places
    can handle a encode/decode roundtrip.
    """

    class Obj(BaseModel):
        id: condecimal(gt=0, max_digits=22, decimal_places=0)
        price: Decimal = Decimal('0.01')

    json_data = b'{"id":"1","price":"0.01"}'
    assert Obj(id=1).model_dump_json() == json_data
    assert Obj.model_validate_json(json_data) == Obj(id=1)


def test_json_encoder_simple_inheritance():
    class Parent(BaseModel):
        dt: datetime = datetime.now()
        timedt: timedelta = timedelta(hours=100)

        @serializer('dt')
        def serialize_dt(self, _v: datetime, _info):
            return 'parent_encoder'

    class Child(Parent):
        @serializer('timedt')
        def serialize_timedt(self, _v: timedelta, _info):
            return 'child_encoder'

    assert Child().model_dump_json() == b'{"dt":"parent_encoder","timedt":"child_encoder"}'


def test_json_encoder_inheritance_override():
    class Parent(BaseModel):
        dt: datetime = datetime.now()

        @serializer('dt')
        def serialize_dt(self, _v: datetime, _info):
            return 'parent_encoder'

    class Child(Parent):
        @serializer('dt')
        def serialize_dt(self, _v: datetime, _info):
            return 'child_encoder'

    assert Child().model_dump_json() == b'{"dt":"child_encoder"}'


def test_encode_dataclass():
    @vanilla_dataclass
    class Foo:
        bar: int
        spam: str

    f = Foo(bar=123, spam='apple pie')
    assert '{"bar": 123, "spam": "apple pie"}' == json.dumps(f, default=pydantic_encoder)


@pytest.mark.xfail(reason='dataclasses not implemented')
def test_encode_pydantic_dataclass():
    @pydantic_dataclass
    class Foo:
        bar: int
        spam: str

    f = Foo(bar=123, spam='apple pie')
    assert '{"bar": 123, "spam": "apple pie"}' == json.dumps(f, default=pydantic_encoder)


def test_json_nested_encode_models():
    class Phone(BaseModel):
        manufacturer: str
        number: int

    class User(BaseModel):
        name: str
        SSN: int
        birthday: datetime
        phone: Phone
        friend: Optional['User'] = None  # noqa: F821

        @serializer('birthday')
        def serialize_birthday(self, v: datetime, _info):
            return v.timestamp()

        @serializer('phone', when_used='unless-none')
        def serialize_phone(self, v: Phone, _info):
            return v.number

        @serializer('friend', when_used='unless-none')
        def serialize_user(self, v, _info):
            return v.SSN

    User.model_rebuild()

    iphone = Phone(manufacturer='Apple', number=18002752273)
    galaxy = Phone(manufacturer='Samsung', number=18007267864)

    timon = User(name='Timon', SSN=123, birthday=datetime(1993, 6, 1, tzinfo=timezone.utc), phone=iphone)
    pumbaa = User(name='Pumbaa', SSN=234, birthday=datetime(1993, 5, 15, tzinfo=timezone.utc), phone=galaxy)

    timon.friend = pumbaa

    assert iphone.model_dump_json() == b'{"manufacturer":"Apple","number":18002752273}'
    assert (
        pumbaa.model_dump_json()
        == b'{"name":"Pumbaa","SSN":234,"birthday":737424000.0,"phone":18007267864,"friend":null}'
    )
    assert (
        timon.model_dump_json() == b'{"name":"Timon","SSN":123,"birthday":738892800.0,"phone":18002752273,"friend":234}'
    )


def test_custom_encode_fallback_basemodel():
    class MyExoticType:
        pass

    class Foo(BaseModel):
        x: MyExoticType

        @serializer('x')
        def serialize_x(self, _v: MyExoticType, _info):
            return 'exo'

        class Config:
            arbitrary_types_allowed = True

    class Bar(BaseModel):
        foo: Foo

    assert Bar(foo=Foo(x=MyExoticType())).model_dump_json() == b'{"foo":{"x":"exo"}}'


def test_recursive(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class Model(BaseModel):
    value: int
    nested: Optional[Model] = None
"""
    )
    M = module.Model

    assert M(value=1, nested=M(value=2)).model_dump_json(exclude_none=True) == b'{"value":1,"nested":{"value":2}}'
