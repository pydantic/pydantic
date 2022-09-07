import datetime
import json
import re
import sys
from dataclasses import dataclass as vanilla_dataclass
from decimal import Decimal
from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import pytest

from pydantic import BaseModel, NameEmail, create_model
from pydantic.color import Color
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.json import pydantic_encoder, timedelta_isoformat
from pydantic.types import ConstrainedDecimal, DirectoryPath, FilePath, SecretBytes, SecretStr


class MyEnum(Enum):
    foo = 'bar'
    snap = 'crackle'


@pytest.mark.parametrize(
    'input,output',
    [
        (UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), '"ebcdab58-6eb8-46fb-a190-d07a33e9eac8"'),
        (IPv4Address('192.168.0.1'), '"192.168.0.1"'),
        (Color('#000'), '"black"'),
        (Color((1, 12, 123)), '"#010c7b"'),
        (SecretStr('abcd'), '"**********"'),
        (SecretStr(''), '""'),
        (SecretBytes(b'xyz'), '"**********"'),
        (SecretBytes(b''), '""'),
        (NameEmail('foo bar', 'foobaR@example.com'), '"foo bar <foobaR@example.com>"'),
        (IPv6Address('::1:0:1'), '"::1:0:1"'),
        (IPv4Interface('192.168.0.0/24'), '"192.168.0.0/24"'),
        (IPv6Interface('2001:db00::/120'), '"2001:db00::/120"'),
        (IPv4Network('192.168.0.0/24'), '"192.168.0.0/24"'),
        (IPv6Network('2001:db00::/120'), '"2001:db00::/120"'),
        (datetime.datetime(2032, 1, 1, 1, 1), '"2032-01-01T01:01:00"'),
        (datetime.datetime(2032, 1, 1, 1, 1, tzinfo=datetime.timezone.utc), '"2032-01-01T01:01:00+00:00"'),
        (datetime.datetime(2032, 1, 1), '"2032-01-01T00:00:00"'),
        (datetime.time(12, 34, 56), '"12:34:56"'),
        (datetime.timedelta(days=12, seconds=34, microseconds=56), '1036834.000056'),
        (datetime.timedelta(seconds=-1), '-1.0'),
        ({1, 2, 3}, '[1, 2, 3]'),
        (frozenset([1, 2, 3]), '[1, 2, 3]'),
        ((v for v in range(4)), '[0, 1, 2, 3]'),
        (b'this is bytes', '"this is bytes"'),
        (Decimal('12.34'), '12.34'),
        (create_model('BarModel', a='b', c='d')(), '{"a": "b", "c": "d"}'),
        (MyEnum.foo, '"bar"'),
        (re.compile('^regex$'), '"^regex$"'),
    ],
)
def test_encoding(input, output):
    assert output == json.dumps(input, default=pydantic_encoder)


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
    assert m.dict() == {'a': 10.2, 'b': b'foobar', 'c': Decimal('10.2'), 'd': {'x': 123, 'y': '123'}}
    assert m.json() == '{"a": 10.2, "b": "foobar", "c": 10.2, "d": {"x": 123, "y": "123"}}'
    assert m.json(exclude={'b'}) == '{"a": 10.2, "c": 10.2, "d": {"x": 123, "y": "123"}}'


def test_subclass_encoding():
    class SubDate(datetime.datetime):
        pass

    class Model(BaseModel):
        a: datetime.datetime
        b: SubDate

    m = Model(a=datetime.datetime(2032, 1, 1, 1, 1), b=SubDate(2020, 2, 29, 12, 30))
    assert m.dict() == {'a': datetime.datetime(2032, 1, 1, 1, 1), 'b': SubDate(2020, 2, 29, 12, 30)}
    assert m.json() == '{"a": "2032-01-01T01:01:00", "b": "2020-02-29T12:30:00"}'


def test_subclass_custom_encoding():
    class SubDate(datetime.datetime):
        pass

    class SubDelta(datetime.timedelta):
        pass

    class Model(BaseModel):
        a: SubDate
        b: SubDelta

        class Config:
            json_encoders = {
                datetime.datetime: lambda v: v.strftime('%a, %d %b %C %H:%M:%S'),
                datetime.timedelta: timedelta_isoformat,
            }

    m = Model(a=SubDate(2032, 1, 1, 1, 1), b=SubDelta(hours=100))
    assert m.dict() == {'a': SubDate(2032, 1, 1, 1, 1), 'b': SubDelta(days=4, seconds=14400)}
    assert m.json() == '{"a": "Thu, 01 Jan 20 01:01:00", "b": "P4DT4H0M0.000000S"}'


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
        (datetime.timedelta(seconds=-1), '-P1DT23H59M59.000000S'),
        (datetime.timedelta(), 'P0DT0H0M0.000000S'),
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


def test_con_decimal_encode() -> None:
    """
    Makes sure a decimal with decimal_places = 0, as well as one with places
    can handle a encode/decode roundtrip.
    """

    class Id(ConstrainedDecimal):
        max_digits = 22
        decimal_places = 0
        ge = 0

    class Obj(BaseModel):
        id: Id
        price: Decimal = Decimal('0.01')

    assert Obj(id=1).json() == '{"id": 1, "price": 0.01}'
    assert Obj.parse_raw('{"id": 1, "price": 0.01}') == Obj(id=1)


def test_json_encoder_simple_inheritance():
    class Parent(BaseModel):
        dt: datetime.datetime = datetime.datetime.now()
        timedt: datetime.timedelta = datetime.timedelta(hours=100)

        class Config:
            json_encoders = {datetime.datetime: lambda _: 'parent_encoder'}

    class Child(Parent):
        class Config:
            json_encoders = {datetime.timedelta: lambda _: 'child_encoder'}

    assert Child().json() == '{"dt": "parent_encoder", "timedt": "child_encoder"}'


def test_json_encoder_inheritance_override():
    class Parent(BaseModel):
        dt: datetime.datetime = datetime.datetime.now()

        class Config:
            json_encoders = {datetime.datetime: lambda _: 'parent_encoder'}

    class Child(Parent):
        class Config:
            json_encoders = {datetime.datetime: lambda _: 'child_encoder'}

    assert Child().json() == '{"dt": "child_encoder"}'


def test_custom_encoder_arg():
    class Model(BaseModel):
        x: datetime.timedelta

    m = Model(x=123)
    assert m.json() == '{"x": 123.0}'
    assert m.json(encoder=lambda v: '__default__') == '{"x": "__default__"}'


def test_encode_dataclass():
    @vanilla_dataclass
    class Foo:
        bar: int
        spam: str

    f = Foo(bar=123, spam='apple pie')
    assert '{"bar": 123, "spam": "apple pie"}' == json.dumps(f, default=pydantic_encoder)


def test_encode_pydantic_dataclass():
    @pydantic_dataclass
    class Foo:
        bar: int
        spam: str

    f = Foo(bar=123, spam='apple pie')
    assert '{"bar": 123, "spam": "apple pie"}' == json.dumps(f, default=pydantic_encoder)


def test_encode_custom_root():
    class Model(BaseModel):
        __root__: List[str]

    assert Model(__root__=['a', 'b']).json() == '["a", "b"]'


def test_custom_decode_encode():
    load_calls, dump_calls = 0, 0

    def custom_loads(s):
        nonlocal load_calls
        load_calls += 1
        return json.loads(s.strip('$'))

    def custom_dumps(s, default=None, **kwargs):
        nonlocal dump_calls
        dump_calls += 1
        return json.dumps(s, default=default, indent=2)

    class Model(BaseModel):
        a: int
        b: str

        class Config:
            json_loads = custom_loads
            json_dumps = custom_dumps

    m = Model.parse_raw('${"a": 1, "b": "foo"}$$')
    assert m.dict() == {'a': 1, 'b': 'foo'}
    assert m.json() == '{\n  "a": 1,\n  "b": "foo"\n}'


def test_json_nested_encode_models():
    class Phone(BaseModel):
        manufacturer: str
        number: int

    class User(BaseModel):
        name: str
        SSN: int
        birthday: datetime.datetime
        phone: Phone
        friend: Optional['User'] = None  # noqa: F821  # https://github.com/PyCQA/pyflakes/issues/567

        class Config:
            json_encoders = {
                datetime.datetime: lambda v: v.timestamp(),
                Phone: lambda v: v.number if v else None,
                'User': lambda v: v.SSN,
            }

    User.update_forward_refs()

    iphone = Phone(manufacturer='Apple', number=18002752273)
    galaxy = Phone(manufacturer='Samsung', number=18007267864)

    timon = User(
        name='Timon', SSN=123, birthday=datetime.datetime(1993, 6, 1, tzinfo=datetime.timezone.utc), phone=iphone
    )
    pumbaa = User(
        name='Pumbaa', SSN=234, birthday=datetime.datetime(1993, 5, 15, tzinfo=datetime.timezone.utc), phone=galaxy
    )

    timon.friend = pumbaa

    assert iphone.json(models_as_dict=False) == '{"manufacturer": "Apple", "number": 18002752273}'
    assert (
        pumbaa.json(models_as_dict=False)
        == '{"name": "Pumbaa", "SSN": 234, "birthday": 737424000.0, "phone": 18007267864, "friend": null}'
    )
    assert (
        timon.json(models_as_dict=False)
        == '{"name": "Timon", "SSN": 123, "birthday": 738892800.0, "phone": 18002752273, "friend": 234}'
    )


def test_custom_encode_fallback_basemodel():
    class MyExoticType:
        pass

    def custom_encoder(o):
        if isinstance(o, MyExoticType):
            return 'exo'
        raise TypeError('not serialisable')

    class Foo(BaseModel):
        x: MyExoticType

        class Config:
            arbitrary_types_allowed = True

    class Bar(BaseModel):
        foo: Foo

    assert Bar(foo=Foo(x=MyExoticType())).json(encoder=custom_encoder) == '{"foo": {"x": "exo"}}'


def test_custom_encode_error():
    class MyExoticType:
        pass

    def custom_encoder(o):
        raise TypeError('not serialisable')

    class Foo(BaseModel):
        x: MyExoticType

        class Config:
            arbitrary_types_allowed = True

    with pytest.raises(TypeError, match='not serialisable'):
        Foo(x=MyExoticType()).json(encoder=custom_encoder)


def test_recursive():
    class Model(BaseModel):
        value: Optional[str]
        nested: Optional[BaseModel]

    assert Model(value=None, nested=Model(value=None)).json(exclude_none=True) == '{"nested": {}}'
