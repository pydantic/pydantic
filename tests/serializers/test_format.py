import json
import re
from datetime import date
from uuid import UUID

import pytest

from pydantic_core import PydanticSerializationError, SchemaSerializer, core_schema


@pytest.mark.parametrize(
    'value,formatting_string,expected_python,expected_json',
    [
        (42.12345, '0.4f', '42.1234', b'"42.1234"'),
        (42.12, '0.4f', '42.1200', b'"42.1200"'),
        (42.12, '', '42.12', b'"42.12"'),
        (42.1234567, '', '42.1234567', b'"42.1234567"'),
        (date(2022, 11, 20), '%Y-%m-%d', '2022-11-20', b'"2022-11-20"'),
        ('foo', '^5s', ' foo ', b'" foo "'),
        (
            UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'),
            '',
            'ebcdab58-6eb8-46fb-a190-d07a33e9eac8',
            b'"ebcdab58-6eb8-46fb-a190-d07a33e9eac8"',
        ),
    ],
)
def test_format(value, formatting_string, expected_python, expected_json):
    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.format_ser_schema(formatting_string)))
    assert s.to_python(value) == expected_python
    assert s.to_json(value) == expected_json
    assert s.to_python(value, mode='json') == json.loads(expected_json)


def test_format_error():
    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.format_ser_schema('^5d')))
    assert s.to_python(123) == ' 123 '

    # the actual error message differs slightly between cpython and pypy
    msg = "Error calling `format(value, '^5d')`: ValueError:"
    with pytest.raises(PydanticSerializationError, match=re.escape(msg)):
        s.to_python('x')

    with pytest.raises(PydanticSerializationError, match=re.escape(msg)):
        s.to_json('x')


def test_dict_keys():
    s = SchemaSerializer(
        core_schema.dict_schema(core_schema.float_schema(serialization=core_schema.format_ser_schema('0.4f')))
    )
    assert s.to_python({1: True}) == {'1.0000': True}


def test_format_fallback():
    s = SchemaSerializer(core_schema.any_schema(serialization=core_schema.format_ser_schema('^5s')))
    assert s.to_python('abc') == ' abc '
    assert s.to_python('abc', mode='json') == ' abc '
    assert s.to_json('abc') == b'" abc "'

    assert s.to_python(None) is None
    assert s.to_python(None, mode='json') is None
    assert s.to_json(None) == b'null'
