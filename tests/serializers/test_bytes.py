import base64
import json
from enum import Enum

import pytest

from pydantic_core import PydanticSerializationError, SchemaSerializer, core_schema, to_json


def test_bytes():
    s = SchemaSerializer(core_schema.bytes_schema())
    assert s.to_python(b'foobar') == b'foobar'
    assert s.to_python('emoji 💩'.encode()) == 'emoji 💩'.encode()
    assert s.to_json(b'foobar') == b'"foobar"'
    assert s.to_python(b'foobar', mode='json') == 'foobar'

    json_emoji = s.to_json('emoji 💩'.encode())
    # note! serde_json serializes unicode characters differently
    assert json_emoji == b'"emoji \xf0\x9f\x92\xa9"'
    assert json.loads(json_emoji) == 'emoji 💩'


def test_bytes_invalid_all():
    s = SchemaSerializer(core_schema.bytes_schema())
    assert s.to_python(b'\x81') == b'\x81'

    msg = 'Error serializing to JSON: invalid utf-8 sequence of 1 bytes from index 0'
    with pytest.raises(PydanticSerializationError, match=msg):
        s.to_json(b'\x81')


def test_bytes_invalid_cpython():
    # PyO3/pyo3#2770 is now fixed
    s = SchemaSerializer(core_schema.bytes_schema())

    with pytest.raises(UnicodeDecodeError, match="'utf-8' codec can't decode byte 0x81 in position 0: invalid utf-8"):
        s.to_python(b'\x81', mode='json')


def test_bytes_dict_key():
    s = SchemaSerializer(core_schema.dict_schema(core_schema.bytes_schema(), core_schema.int_schema()))
    assert s.to_python({b'foobar': 123}) == {b'foobar': 123}
    assert s.to_python({b'foobar': 123}, mode='json') == {'foobar': 123}
    assert s.to_json({b'foobar': 123}) == b'{"foobar":123}'


def test_bytes_fallback():
    s = SchemaSerializer(core_schema.bytes_schema())
    with pytest.warns(
        UserWarning, match='Expected `bytes` but got `int` with value `123` - serialized value may not be as expected'
    ):
        assert s.to_python(123) == 123
    with pytest.warns(
        UserWarning, match='Expected `bytes` but got `int` with value `123` - serialized value may not be as expected'
    ):
        assert s.to_python(123, mode='json') == 123
    with pytest.warns(
        UserWarning, match='Expected `bytes` but got `int` with value `123` - serialized value may not be as expected'
    ):
        assert s.to_json(123) == b'123'
    with pytest.warns(
        UserWarning, match="Expected `bytes` but got `str` with value `'foo'` - serialized value may not be as expected"
    ):
        assert s.to_json('foo') == b'"foo"'


class BytesSubclass(bytes):
    pass


class BasicClass:
    pass


class BytesMixin(bytes, BasicClass):
    pass


class BytesEnum(bytes, Enum):
    foo = b'foo-value'
    bar = b'bar-value'


@pytest.mark.parametrize('schema_type', ['bytes', 'any'])
@pytest.mark.parametrize(
    'input_value,expected_json',
    [(BytesSubclass(b'foo'), 'foo'), (BytesMixin(b'foo'), 'foo'), (BytesEnum.foo, 'foo-value')],
)
def test_subclass_bytes(schema_type, input_value, expected_json):
    s = SchemaSerializer({'type': schema_type})
    v = s.to_python(input_value)
    assert v == input_value
    assert type(v) == type(input_value)

    v = s.to_python(input_value, mode='json')
    assert v == expected_json
    assert type(v) == str

    assert s.to_json(input_value) == json.dumps(expected_json).encode('utf-8')


def test_bytes_base64():
    s = SchemaSerializer(core_schema.bytes_schema(), {'ser_json_bytes': 'base64'})
    assert s.to_python(b'foobar') == b'foobar'

    assert s.to_json(b'foobar') == b'"Zm9vYmFy"'
    assert s.to_python(b'foobar', mode='json') == 'Zm9vYmFy'
    assert base64.b64decode(s.to_python(b'foobar', mode='json').encode()) == b'foobar'

    # with padding
    assert s.to_json(b'foo bar') == b'"Zm9vIGJhcg=="'
    assert s.to_python(b'foo bar', mode='json') == 'Zm9vIGJhcg=='
    assert base64.b64decode(s.to_python(b'foo bar', mode='json').encode()) == b'foo bar'


def test_bytes_hex():
    s = SchemaSerializer(core_schema.bytes_schema(), {'ser_json_bytes': 'hex'})
    assert s.to_python(b'\xff\xff') == b'\xff\xff'
    assert s.to_json(b'\xff\xff') == b'"ffff"'
    assert s.to_python(b'\xff\xff', mode='json') == 'ffff' == b'\xff\xff'.hex()


def test_bytes_base64_dict_key():
    s = SchemaSerializer(core_schema.dict_schema(core_schema.bytes_schema()), {'ser_json_bytes': 'base64'})

    assert s.to_python({b'foo bar': 123}, mode='json') == {'Zm9vIGJhcg==': 123}
    assert s.to_json({b'foo bar': 123}) == b'{"Zm9vIGJhcg==":123}'


def test_any_bytes_base64():
    s = SchemaSerializer(core_schema.any_schema(), {'ser_json_bytes': 'base64'})
    assert s.to_python(b'foobar') == b'foobar'

    assert s.to_json(b'foobar') == b'"Zm9vYmFy"'
    assert s.to_json({b'foobar': 123}) == b'{"Zm9vYmFy":123}'
    assert s.to_python({b'foobar': 123}, mode='json') == {'Zm9vYmFy': 123}


class BasicModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_bytes_mode_set_via_model_config_not_serializer_config():
    s = SchemaSerializer(
        core_schema.model_schema(
            BasicModel,
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.bytes_schema()),
                }
            ),
            config=core_schema.CoreConfig(ser_json_bytes='base64'),
        )
    )

    bm = BasicModel(foo=b'foobar')
    assert s.to_python(bm) == {'foo': b'foobar'}
    assert s.to_json(bm) == b'{"foo":"Zm9vYmFy"}'
    assert s.to_python(bm, mode='json') == {'foo': 'Zm9vYmFy'}

    # assert doesn't override serializer config
    # in V3, we can change the serialization settings provided to to_json to override model config settings,
    # but that'd be a breaking change
    BasicModel.__pydantic_serializer__ = s
    assert to_json(bm, bytes_mode='utf8') == b'{"foo":"Zm9vYmFy"}'

    assert to_json({'foo': b'some bytes'}, bytes_mode='base64') == b'{"foo":"c29tZSBieXRlcw=="}'
    assert to_json({'bar': bm}, bytes_mode='base64') == b'{"bar":{"foo":"Zm9vYmFy"}}'
