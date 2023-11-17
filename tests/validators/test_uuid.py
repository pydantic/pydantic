import copy
import re
from uuid import UUID

import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        # Valid UUIDs
        ('12345678-1234-1234-1234-567812345678', UUID('12345678-1234-1234-1234-567812345678')),
        ('550e8400-e29b-41d4-a716-446655440000', UUID('550e8400-e29b-41d4-a716-446655440000')),
        ('f47ac10b-58cc-4372-a567-0e02b2c3d479', UUID('f47ac10b-58cc-4372-a567-0e02b2c3d479')),
        ('123e4567-e89b-12d3-a456-426655440000', UUID('123e4567-e89b-12d3-a456-426655440000')),
        ('de305d54-75b4-431b-adb2-eb6b9e546014', UUID('de305d54-75b4-431b-adb2-eb6b9e546014')),
        ('00000000-0000-0000-0000-000000000000', UUID('00000000-0000-0000-0000-000000000000')),
        ('1b4e28ba-2fa1-11d2-883f-0016d3cca427', UUID('1b4e28ba-2fa1-11d2-883f-0016d3cca427')),
        ('6ba7b810-9dad-11d1-80b4-00c04fd430c8', UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')),
        ('886313e1-3b8a-5372-9b90-0c9aee199e5d', UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')),
        ('c0a8f9a8-aa5e-482b-a067-9cb3a51f5c11', UUID('c0a8f9a8-aa5e-482b-a067-9cb3a51f5c11')),
        ('00000000-8000-4000-8000-000000000000', UUID('00000000-8000-4000-8000-000000000000')),
        (b'\x12\x34\x56\x78' * 4, UUID('12345678-1234-5678-1234-567812345678')),
        (b'\x00\x00\x00\x00' * 4, UUID('00000000-0000-0000-0000-000000000000')),
        (b'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        (UUID('12345678-1234-5678-1234-567812345678'), UUID('12345678-1234-5678-1234-567812345678')),
        (UUID('550e8400-e29b-41d4-a716-446655440000'), UUID('550e8400-e29b-41d4-a716-446655440000')),
        # Invalid UUIDs
        (
            'not-a-valid-uuid',
            Err(
                'Input should be a valid UUID, invalid character: expected an optional prefix of'
                + ' `urn:uuid:` followed by [0-9a-fA-F-], found `n` at 1'
            ),
        ),
        (
            '12345678-1234-5678-1234-5678123456789',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 13'),
        ),
        (
            '12345678-1234-1234-1234-1234567890123',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 13'),
        ),
        (b'\x00\x00\x00\x000' * 4, Err('Input should be a valid UUID, invalid length: expected 16 bytes, found 20')),
        ('550e8400-e29b-41d4-a716', Err('Input should be a valid UUID, invalid group count: expected 5, found 4')),
        (
            'f47ac10b-58cc-4372-a567-0e02b2c3d47',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 11'),
        ),
        (
            'de305d54-75b4-431b-adb2-eb6b9e54601',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 11'),
        ),
        (
            '1b4e28ba-2fa1-11d2-883f-0016d3cca42',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 11'),
        ),
        (
            '6ba7b810-9dad-11d1-80b4-00c04fd430c',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 11'),
        ),
        (
            '886313e1-3b8a-5372-9b90-0c9aee199e5',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 11'),
        ),
        (
            'c0a8f9a8-aa5e-482b-a067-9cb3a51f5c1',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 11'),
        ),
        (0xA1A2A3A4B1B2C1C2D1D2D3D4D5D6D7D8, Err('UUID input should be a string, bytes or UUID object')),
        (00000000000000000000000000, Err('UUID input should be a string, bytes or UUID object')),
    ],
)
def test_uuid(input_value, expected):
    v = SchemaValidator({'type': 'uuid'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            result = v.validate_python(input_value)
            print(f'input_value={input_value} result={result}')
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, UUID)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (UUID('12345678-1234-5678-1234-567812345678'), UUID('12345678-1234-5678-1234-567812345678')),
        ('12345678-1234-5678-1234-567812345678', Err('Input should be an instance of UUID [type=is_instance_of,')),
        (b'12345678-1234-5678-1234-567812345678', Err('Input should be an instance of UUID [type=is_instance_of,')),
        (1654646400, Err('Input should be an instance of UUID [type=is_instance_of')),
    ],
)
def test_uuid_strict(input_value, expected):
    v = SchemaValidator({'type': 'uuid', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, UUID)


@pytest.mark.parametrize(
    'input_value, version, expected',
    [
        # Valid UUIDs
        ('a6cc5730-2261-11ee-9c43-2eb5a363657c', 1, UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c')),
        (UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c'), 1, UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c')),
        ('04e4aeb3-8f20-30d0-8852-d295e1265eed', 3, UUID('04e4aeb3-8f20-30d0-8852-d295e1265eed')),
        (UUID('04e4aeb3-8f20-30d0-8852-d295e1265eed'), 3, UUID('04e4aeb3-8f20-30d0-8852-d295e1265eed')),
        ('0e7ac198-9acd-4c0c-b4b4-761974bf71d7', 4, UUID('0e7ac198-9acd-4c0c-b4b4-761974bf71d7')),
        (UUID('0e7ac198-9acd-4c0c-b4b4-761974bf71d7'), 4, UUID('0e7ac198-9acd-4c0c-b4b4-761974bf71d7')),
        ('0e7ac198-9acd-4c0c-b4b4-761974bf71d7', 4, UUID('0e7ac198-9acd-4c0c-b4b4-761974bf71d7')),
        (UUID('0e7ac198-9acd-4c0c-b4b4-761974bf71d7'), 4, UUID('0e7ac198-9acd-4c0c-b4b4-761974bf71d7')),
        # Cases from pydantic#7355 and pydantic#7537
        # `UUID.version` makes sense for RFC 4122 UUIDs only. For non RFC 4122 UUIDs Python uses `UUID.version=None`
        ('00000000-8000-4000-8000-000000000000', 4, UUID('00000000-8000-4000-8000-000000000000')),
        (UUID('00000000-8000-4000-8000-000000000000'), 4, UUID('00000000-8000-4000-8000-000000000000')),
        ('00000000-7fff-4000-7fff-000000000000', None, UUID('00000000-7fff-4000-7fff-000000000000')),
        (UUID('00000000-7fff-4000-7fff-000000000000'), None, UUID('00000000-7fff-4000-7fff-000000000000')),
        (UUID('00000000-7fff-4000-7fff-000000000000'), 4, Err('UUID version 4 expected')),
        ('b34b6755-f49c-3bd2-6f06-131a708c2bf3', None, UUID('b34b6755-f49c-3bd2-6f06-131a708c2bf3')),
        (UUID('b34b6755-f49c-3bd2-6f06-131a708c2bf3'), None, UUID('b34b6755-f49c-3bd2-6f06-131a708c2bf3')),
        (UUID('b34b6755-f49c-3bd2-6f06-131a708c2bf3'), 4, Err('UUID version 4 expected')),
        # Invalid UUIDs
        ('a6cc5730-2261-11ee-9c43-2eb5a363657c', 5, Err('UUID version 5 expected')),
        (UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c'), 5, Err('UUID version 5 expected')),
        ('04e4aeb3-8f20-30d0-8852-d295e1265eed', 4, Err('UUID version 4 expected')),
        (UUID('04e4aeb3-8f20-30d0-8852-d295e1265eed'), 4, Err('UUID version 4 expected')),
        ('0e7ac198-9acd-4c0c-b4b4-761974bf71d7', 3, Err('UUID version 3 expected')),
        (UUID('0e7ac198-9acd-4c0c-b4b4-761974bf71d7'), 3, Err('UUID version 3 expected')),
        ('08ed0736-fb95-5cc5-85ed-37e4f3df9b29', 1, Err('UUID version 1 expected')),
        (UUID('08ed0736-fb95-5cc5-85ed-37e4f3df9b29'), 1, Err('UUID version 1 expected')),
    ],
)
def test_uuid_version(input_value, version, expected):
    schema = {'type': 'uuid'}
    if version is not None:
        schema['version'] = version

    v = SchemaValidator(schema)

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, UUID)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('a6cc5730-2261-11ee-9c43-2eb5a363657c', UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c')),
        ('12345678123456781234567812345678', UUID('12345678-1234-5678-1234-567812345678')),
        (
            'c0a8f9a8-aa5e-482b-a067-9cb3a51f5c1',
            Err('Input should be a valid UUID, invalid group length in group 4: expected 12, found 11'),
        ),
        (1e1, Err('input should be a string, bytes or UUID object')),
        (None, Err('input should be a string, bytes or UUID object')),
        (True, Err('input should be a string, bytes or UUID object')),
        (0xA1A2A3A4B1B2C1C2D1D2D3D4D5D6D7D8, Err('input should be a string, bytes or UUID object')),
        (0x12345678123456781234567812345678, Err('input should be a string, bytes or UUID object')),
    ],
)
def test_uuid_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'uuid'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, UUID)


def test_uuid_deepcopy():
    output = SchemaValidator({'type': 'uuid'}).validate_python('a6cc5730-2261-11ee-9c43-2eb5a363657c')
    c = copy.deepcopy(output)
    assert repr(output) == "UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c')"
    assert c == output
    assert isinstance(output, UUID)


def test_uuid_copy():
    output = SchemaValidator({'type': 'uuid'}).validate_python('a6cc5730-2261-11ee-9c43-2eb5a363657c')
    c = copy.copy(output)
    assert repr(output) == "UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c')"
    assert c == output
    assert isinstance(output, UUID)


def test_uuid_wrap_json():
    # https://github.com/pydantic/pydantic/issues/8147
    schema = core_schema.no_info_wrap_validator_function(lambda v, handler: handler(v), core_schema.uuid_schema())
    v = SchemaValidator(schema)

    assert v.validate_python(UUID('a6cc5730-2261-11ee-9c43-2eb5a363657c'), strict=True) == UUID(
        'a6cc5730-2261-11ee-9c43-2eb5a363657c'
    )
    assert v.validate_json('"a6cc5730-2261-11ee-9c43-2eb5a363657c"', strict=True) == UUID(
        'a6cc5730-2261-11ee-9c43-2eb5a363657c'
    )
