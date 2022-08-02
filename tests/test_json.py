import pytest

from pydantic_core import SchemaValidator, ValidationError


@pytest.mark.parametrize(
    'input_value,output_value',
    [('false', False), ('true', True), ('0', False), ('1', True), ('"yes"', True), ('"no"', False)],
)
def test_bool(input_value, output_value):
    v = SchemaValidator({'type': 'bool'})
    assert v.validate_json(input_value) == output_value


@pytest.mark.parametrize('input_value', ['[1, 2, 3]', b'[1, 2, 3]', bytearray(b'[1, 2, 3]')])
def test_input_types(input_value):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    assert v.validate_json(input_value) == [1, 2, 3]


def test_input_type_invalid():
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    with pytest.raises(TypeError, match='^JSON input should be str, bytes or bytearray, not list$'):
        v.validate_json([])


def test_null():
    assert SchemaValidator({'type': 'none'}).validate_json('null') is None


def test_str():
    s = SchemaValidator({'type': 'str'})
    assert s.validate_json('"foobar"') == 'foobar'
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[kind=str_type,'):
        s.validate_json('false')
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[kind=str_type,'):
        s.validate_json('123')


@pytest.mark.parametrize(
    'input_value,output_value',
    [('123.4', 123.4), ('123.0', 123.0), ('123', 123.0), ('"123.4"', 123.4), ('"123.0"', 123.0), ('"123"', 123.0)],
)
def test_float(input_value, output_value):
    v = SchemaValidator({'type': 'float'})
    assert v.validate_json(input_value) == output_value


def test_model():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
        }
    )

    # language=json
    input_str = '{"field_a": "abc", "field_b": 1}'
    assert v.validate_json(input_str) == {'field_a': 'abc', 'field_b': 1}


def test_float_no_remainder():
    v = SchemaValidator({'type': 'int'})
    assert v.validate_json('123.0') == 123


def test_error_loc():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'field_a': {'schema': {'type': 'list', 'items_schema': {'type': 'int'}}}},
            'extra_validator': {'type': 'int'},
            'extra_behavior': 'allow',
        }
    )

    # assert v.validate_json('{"field_a": [1, 2, "3"]}') == ({'field_a': [1, 2, 3]}, {'field_a'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('{"field_a": [1, 2, "wrong"]}')
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['field_a', 2],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_dict():
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    assert v.validate_json('{"1": 2, "3": 4}') == {1: 2, 3: 4}


def test_dict_any_value():
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'str'}})
    assert v.validate_json('{"1": 1, "2": "a", "3": null}') == {'1': 1, '2': 'a', '3': None}


def test_invalid_json():
    v = SchemaValidator({'type': 'bool'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"foobar')
    assert exc_info.value.errors() == [
        {
            'kind': 'invalid_json',
            'loc': [],
            'message': 'Invalid JSON: EOF while parsing a string at line 1 column 7',
            'input_value': '"foobar',
            'context': {'error': 'EOF while parsing a string at line 1 column 7'},
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('[1,\n2,\n3,]')
    assert exc_info.value.errors() == [
        {
            'kind': 'invalid_json',
            'loc': [],
            'message': 'Invalid JSON: trailing comma at line 3 column 3',
            'input_value': '[1,\n2,\n3,]',
            'context': {'error': 'trailing comma at line 3 column 3'},
        }
    ]
