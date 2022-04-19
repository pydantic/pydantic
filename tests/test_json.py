import pytest

from pydantic_core import SchemaValidator, ValidationError


@pytest.mark.parametrize(
    'input_value,output_value',
    [('false', False), ('true', True), ('0', False), ('1', True), ('"yes"', True), ('"no"', False)],
)
def test_bool(input_value, output_value):
    v = SchemaValidator({'type': 'bool', 'title': 'TestModel'})
    assert v.validate_json(input_value) == output_value


def test_null():
    assert SchemaValidator({'type': 'none'}).validate_json('null') is None


def test_str():
    assert SchemaValidator({'type': 'str'}).validate_json('"foobar"') == 'foobar'
    assert SchemaValidator({'type': 'str'}).validate_json('123') == '123'
    with pytest.raises(ValidationError, match=r'Value must be a valid string \(kind=str_type\)'):
        SchemaValidator({'type': 'str'}).validate_json('false')


@pytest.mark.parametrize(
    'input_value,output_value',
    [('123.4', 123.4), ('123.0', 123.0), ('123', 123.0), ('"123.4"', 123.4), ('"123.0"', 123.0), ('"123"', 123.0)],
)
def test_float(input_value, output_value):
    v = SchemaValidator({'type': 'float'})
    assert v.validate_json(input_value) == output_value


def test_model():
    v = SchemaValidator({'type': 'model', 'fields': {'field_a': {'type': 'str'}, 'field_b': {'type': 'int'}}})

    # language=json
    input_str = '{"field_a": 123, "field_b": 1}'
    assert v.validate_json(input_str) == ({'field_a': '123', 'field_b': 1}, {'field_b', 'field_a'})


def test_list():
    v = SchemaValidator({'type': 'list', 'items': {'type': 'int'}, 'title': 'TestModel'})
    # language=json
    input_str = '[1, 2, "3"]'
    assert v.validate_json(input_str) == [1, 2, 3]


def test_float_no_remainder():
    v = SchemaValidator({'type': 'int'})
    assert v.validate_json('123.0') == 123


def test_error_loc():
    v = SchemaValidator(
        {
            'type': 'model',
            'fields': {'field_a': {'type': 'list', 'items': {'type': 'int'}}},
            'extra_validator': {'type': 'int'},
            'config': {'extra': 'allow'},
        }
    )

    assert v.validate_json('{"field_a": [1, 2, "3"]}') == ({'field_a': [1, 2, 3]}, {'field_a'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('{"field_a": [1, 2, "wrong"]}')
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['field_a', 2],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_dict():
    v = SchemaValidator({'type': 'dict', 'keys': {'type': 'int'}, 'values': {'type': 'int'}})
    assert v.validate_json('{"1": 2, "3": 4}') == {1: 2, 3: 4}


def test_dict_any_value():
    v = SchemaValidator({'type': 'dict', 'keys': {'type': 'str'}})
    assert v.validate_json('{"1": 1, "2": "a", "3": null}') == {'1': 1, '2': 'a', '3': None}


def test_invalid_json():
    v = SchemaValidator({'type': 'bool'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"foobar')
    assert exc_info.value.errors() == [
        {
            'kind': 'invalid_json',
            'loc': [],
            'message': 'EOF while parsing a string at line 1 column 7',
            'input_value': '"foobar',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('[1,\n2,\n3,]')
    assert exc_info.value.errors() == [
        {
            'kind': 'invalid_json',
            'loc': [],
            'message': 'trailing comma at line 3 column 3',
            'input_value': '[1,\n2,\n3,]',
        }
    ]
