from uuid import UUID

import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_uuid():
    v = SchemaSerializer(core_schema.uuid_schema())
    assert v.to_python(UUID('12345678-1234-5678-1234-567812345678')) == UUID('12345678-1234-5678-1234-567812345678')

    assert (
        v.to_python(UUID('12345678-1234-5678-1234-567812345678'), mode='json') == '12345678-1234-5678-1234-567812345678'
    )
    assert v.to_json(UUID('12345678-1234-5678-1234-567812345678')) == b'"12345678-1234-5678-1234-567812345678"'

    with pytest.warns(
        UserWarning, match='Expected `uuid` but got `int` with value `123` - serialized value may not be as expected'
    ):
        assert v.to_python(123, mode='json') == 123

    with pytest.warns(
        UserWarning, match='Expected `uuid` but got `int` with value `123` - serialized value may not be as expected'
    ):
        assert v.to_json(123) == b'123'


def test_uuid_key():
    v = SchemaSerializer(core_schema.dict_schema(core_schema.uuid_schema(), core_schema.uuid_schema()))
    assert v.to_python(
        {UUID('12345678-1234-5678-1234-567812345678'): UUID('12345678-1234-5678-1234-567812345678')}
    ) == {UUID('12345678-1234-5678-1234-567812345678'): UUID('12345678-1234-5678-1234-567812345678')}
    assert v.to_python(
        {UUID('12345678-1234-5678-1234-567812345678'): UUID('12345678-1234-5678-1234-567812345678')}, mode='json'
    ) == {'12345678-1234-5678-1234-567812345678': '12345678-1234-5678-1234-567812345678'}
    assert (
        v.to_json({UUID('12345678-1234-5678-1234-567812345678'): UUID('12345678-1234-5678-1234-567812345678')})
        == b'{"12345678-1234-5678-1234-567812345678":"12345678-1234-5678-1234-567812345678"}'
    )


@pytest.mark.parametrize(
    'value,expected',
    [
        (UUID('12345678-1234-5678-1234-567812345678'), '12345678-1234-5678-1234-567812345678'),
        (UUID('550e8400-e29b-41d4-a716-446655440000'), '550e8400-e29b-41d4-a716-446655440000'),
        (UUID('123e4567-e89b-12d3-a456-426655440000'), '123e4567-e89b-12d3-a456-426655440000'),
        (UUID('00000000-0000-0000-0000-000000000000'), '00000000-0000-0000-0000-000000000000'),
    ],
)
def test_uuid_json(value, expected):
    v = SchemaSerializer(core_schema.uuid_schema())
    assert v.to_python(value, mode='json') == expected
    assert v.to_json(value).decode() == f'"{expected}"'


def test_any_uuid_key():
    v = SchemaSerializer(core_schema.dict_schema())
    input_value = {UUID('12345678-1234-5678-1234-567812345678'): 1}

    assert v.to_python(input_value, mode='json') == {'12345678-1234-5678-1234-567812345678': 1}
    assert v.to_json(input_value) == b'{"12345678-1234-5678-1234-567812345678":1}'
