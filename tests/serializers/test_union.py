import json
import re

import pytest

from pydantic_core import PydanticSerializationUnexpectedValue, SchemaSerializer, core_schema


@pytest.mark.parametrize('input_value,expected_value', [(True, True), (False, False), (1, 1), (123, 123), (-42, -42)])
def test_union_bool_int(input_value, expected_value):
    s = SchemaSerializer(core_schema.union_schema(core_schema.bool_schema(), core_schema.int_schema()))
    assert s.to_python(input_value) == expected_value
    assert s.to_python(input_value, mode='json') == expected_value
    assert s.to_json(input_value) == json.dumps(expected_value).encode()


def test_union_error():
    s = SchemaSerializer(core_schema.union_schema(core_schema.bool_schema(), core_schema.int_schema()))
    msg = 'Expected `Union[bool, int]` but got `str` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert s.to_python('a string') == 'a string'


class ModelA:
    def __init__(self, a, b):
        self.a = a
        self.b = b


class ModelB:
    def __init__(self, c, d):
        self.c = c
        self.d = d


@pytest.fixture(scope='module')
def model_serializer() -> SchemaSerializer:
    return SchemaSerializer(
        {
            'type': 'union',
            'choices': [
                {
                    'type': 'model',
                    'cls': ModelA,
                    'schema': {
                        'type': 'typed-dict',
                        'return_fields_set': True,
                        'fields': {
                            'a': {'schema': {'type': 'bytes'}},
                            'b': {
                                'schema': {
                                    'type': 'float',
                                    'serialization': {
                                        'type': 'format',
                                        'formatting_string': '0.1f',
                                        'when_used': 'unless-none',
                                    },
                                }
                            },
                        },
                    },
                },
                {
                    'type': 'model',
                    'cls': ModelB,
                    'schema': {
                        'type': 'typed-dict',
                        'return_fields_set': True,
                        'fields': {
                            'c': {'schema': {'type': 'bytes'}},
                            'd': {
                                'schema': {
                                    'type': 'float',
                                    'serialization': {
                                        'type': 'format',
                                        'formatting_string': '0.2f',
                                        'when_used': 'unless-none',
                                    },
                                }
                            },
                        },
                    },
                },
            ],
        }
    )


class SubclassA(ModelA):
    pass


@pytest.mark.parametrize('input_value', [ModelA(b'bite', 2.3456), SubclassA(b'bite', 2.3456)])
def test_model_a(model_serializer: SchemaSerializer, input_value):
    assert model_serializer.to_python(input_value) == {'a': b'bite', 'b': '2.3'}
    assert model_serializer.to_python(input_value, mode='json') == {'a': 'bite', 'b': '2.3'}
    assert model_serializer.to_json(input_value) == b'{"a":"bite","b":"2.3"}'


class SubclassB(ModelB):
    pass


@pytest.mark.parametrize('input_value', [ModelB(b'bite', 2.3456), SubclassB(b'bite', 2.3456)])
def test_model_b(model_serializer: SchemaSerializer, input_value):
    assert model_serializer.to_python(input_value) == {'c': b'bite', 'd': '2.35'}
    assert model_serializer.to_python(input_value, mode='json') == {'c': 'bite', 'd': '2.35'}
    assert model_serializer.to_json(input_value) == b'{"c":"bite","d":"2.35"}'


def test_keys():
    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.union_schema(
                core_schema.int_schema(), core_schema.float_schema(serialization=core_schema.format_ser_schema('0.0f'))
            ),
            core_schema.int_schema(),
        )
    )
    assert s.to_python({1: 2, 2.111: 3}) == {1: 2, 2.111: 3}
    assert s.to_python({1: 2, 2.111: 3}, mode='json') == {'1': 2, '2': 3}
    assert s.to_json({1: 2, 2.111: 3}) == b'{"1":2,"2":3}'


def test_union_of_functions():
    def repr_function(value, _info):
        if value == 'unexpected':
            raise PydanticSerializationUnexpectedValue()
        return f'func: {value!r}'

    s = SchemaSerializer(
        core_schema.union_schema(
            core_schema.any_schema(serialization=core_schema.function_plain_ser_schema(repr_function)),
            core_schema.float_schema(serialization=core_schema.format_ser_schema('_^14')),
        )
    )
    assert s.to_python('foobar') == "func: 'foobar'"
    assert s.to_python('foobar', mode='json') == "func: 'foobar'"
    assert s.to_json('foobar') == b'"func: \'foobar\'"'

    assert s.to_python('unexpected') == 'unexpected'
    assert s.to_python('unexpected', mode='json') == '__unexpected__'
    assert s.to_json('unexpected') == b'"__unexpected__"'


def test_typed_dict_literal():
    s = SchemaSerializer(
        core_schema.union_schema(
            core_schema.typed_dict_schema(
                dict(
                    pet_type=core_schema.typed_dict_field(core_schema.literal_schema('cat')),
                    sound=core_schema.typed_dict_field(
                        core_schema.int_schema(serialization=core_schema.format_ser_schema('04d'))
                    ),
                )
            ),
            core_schema.typed_dict_schema(
                dict(
                    pet_type=core_schema.typed_dict_field(core_schema.literal_schema('dog')),
                    sound=core_schema.typed_dict_field(
                        core_schema.float_schema(serialization=core_schema.format_ser_schema('0.3f'))
                    ),
                )
            ),
        )
    )

    assert s.to_python(dict(pet_type='cat', sound=3), mode='json') == {'pet_type': 'cat', 'sound': '0003'}
    assert s.to_python(dict(pet_type='dog', sound=3), mode='json') == {'pet_type': 'dog', 'sound': '3.000'}


def test_typed_dict_missing():
    """
    TODO, needs tests for each case
    """
    s = SchemaSerializer(
        core_schema.union_schema(
            core_schema.typed_dict_schema(dict(foo=core_schema.typed_dict_field(core_schema.int_schema()))),
            core_schema.typed_dict_schema(
                dict(
                    foo=core_schema.typed_dict_field(
                        core_schema.int_schema(serialization=core_schema.format_ser_schema('04d'))
                    ),
                    bar=core_schema.typed_dict_field(core_schema.int_schema()),
                )
            ),
        )
    )

    assert s.to_python(dict(foo=1)) == {'foo': 1}
    assert s.to_python(dict(foo=1), mode='json') == {'foo': 1}
    assert s.to_json(dict(foo=1)) == b'{"foo":1}'
    assert s.to_python(dict(foo=1, bar=2)) == {'foo': 1, 'bar': 2}
    assert s.to_python(dict(foo=1, bar=2), mode='json') == {'foo': '0001', 'bar': 2}
    assert s.to_json(dict(foo=1, bar=2)) == b'{"foo":"0001","bar":2}'


def test_typed_dict_extra():
    """
    TODO, needs tests for each case
    """
    s = SchemaSerializer(
        core_schema.union_schema(
            core_schema.typed_dict_schema(
                dict(
                    foo=core_schema.typed_dict_field(core_schema.int_schema()),
                    bar=core_schema.typed_dict_field(core_schema.int_schema()),
                )
            ),
            core_schema.typed_dict_schema(
                dict(
                    foo=core_schema.typed_dict_field(
                        core_schema.int_schema(serialization=core_schema.format_ser_schema('04d'))
                    )
                )
            ),
        )
    )

    assert s.to_python(dict(foo=1, bar=2)) == {'foo': 1, 'bar': 2}
    assert s.to_python(dict(foo=1, bar=2), mode='json') == {'foo': 1, 'bar': 2}
    assert s.to_json(dict(foo=1, bar=2)) == b'{"foo":1,"bar":2}'
    assert s.to_python(dict(foo=1)) == {'foo': 1}
    assert s.to_python(dict(foo=1), mode='json') == {'foo': '0001'}
    assert s.to_json(dict(foo=1)) == b'{"foo":"0001"}'


def test_typed_dict_different_fields():
    """
    TODO, needs tests for each case
    """
    s = SchemaSerializer(
        core_schema.union_schema(
            core_schema.typed_dict_schema(
                dict(
                    foo=core_schema.typed_dict_field(core_schema.int_schema()),
                    bar=core_schema.typed_dict_field(core_schema.int_schema()),
                )
            ),
            core_schema.typed_dict_schema(
                dict(
                    spam=core_schema.typed_dict_field(core_schema.int_schema()),
                    ham=core_schema.typed_dict_field(
                        core_schema.int_schema(serialization=core_schema.format_ser_schema('04d'))
                    ),
                )
            ),
        )
    )

    assert s.to_python(dict(foo=1, bar=2)) == {'foo': 1, 'bar': 2}
    assert s.to_python(dict(foo=1, bar=2), mode='json') == {'foo': 1, 'bar': 2}
    assert s.to_json(dict(foo=1, bar=2)) == b'{"foo":1,"bar":2}'
    assert s.to_python(dict(spam=1, ham=2)) == {'spam': 1, 'ham': 2}
    assert s.to_python(dict(spam=1, ham=2), mode='json') == {'spam': 1, 'ham': '0002'}
    assert s.to_json(dict(spam=1, ham=2)) == b'{"spam":1,"ham":"0002"}'
