import pickle

import pytest

from pydantic_core import SchemaError, SchemaValidator
from pydantic_core import core_schema as cs


def test_build_error_type():
    with pytest.raises(SchemaError, match="Input tag 'foobar' found using 'type' does not match any of the"):
        SchemaValidator({'type': 'foobar', 'title': 'TestModel'})


def test_build_error_internal():
    with pytest.raises(SchemaError, match='Input should be a valid integer, unable to parse string as an integer'):
        SchemaValidator({'type': 'str', 'min_length': 'xxx', 'title': 'TestModel'})


def test_build_error_deep():
    with pytest.raises(SchemaError, match='Input should be a valid integer, unable to parse string as an integer'):
        SchemaValidator(
            {
                'title': 'MyTestModel',
                'type': 'typed-dict',
                'fields': {'age': {'schema': {'type': 'int', 'ge': 'not-int'}}},
            }
        )


def test_schema_as_string():
    v = SchemaValidator({'type': 'bool'})
    assert v.validate_python('tRuE') is True


def test_schema_wrong_type(pydantic_version):
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator(1)
    assert str(exc_info.value) == (
        'Invalid Schema:\n  Input should be a valid dictionary or object to'
        ' extract fields from [type=model_attributes_type, input_value=1, input_type=int]\n'
        f'    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/model_attributes_type'
    )
    assert exc_info.value.errors() == [
        {
            'input': 1,
            'loc': (),
            'msg': 'Input should be a valid dictionary or object to extract fields from',
            'type': 'model_attributes_type',
        }
    ]
    assert exc_info.value.error_count() == 1


@pytest.mark.parametrize('pickle_protocol', range(1, pickle.HIGHEST_PROTOCOL + 1))
def test_pickle(pickle_protocol: int) -> None:
    v1 = SchemaValidator({'type': 'bool'})
    assert v1.validate_python('tRuE') is True
    p = pickle.dumps(v1, protocol=pickle_protocol)
    v2 = pickle.loads(p)
    assert v2.validate_python('tRuE') is True
    assert repr(v1) == repr(v2)


def test_schema_definition_error():
    schema = {'type': 'union', 'choices': []}
    schema['choices'].append({'type': 'nullable', 'schema': schema})
    with pytest.raises(SchemaError, match='Recursion error - cyclic reference detected'):
        SchemaValidator(schema)


def test_not_schema_definition_error():
    schema = {
        'type': 'typed-dict',
        'fields': {
            f'f_{i}': {'type': 'typed-dict-field', 'schema': {'type': 'nullable', 'schema': {'type': 'int'}}}
            for i in range(101)
        },
    }
    v = SchemaValidator(schema)
    assert repr(v).count('TypedDictField') == 101


def test_no_type():
    with pytest.raises(SchemaError, match="Unable to extract tag using discriminator 'type'"):
        SchemaValidator({})


def test_wrong_type():
    with pytest.raises(SchemaError, match="Input tag 'unknown' found using 'type' does not match any of the"):
        SchemaValidator({'type': 'unknown'})


def test_function_no_mode():
    with pytest.raises(SchemaError, match="Input tag 'function' found using 'type' does not match any of the"):
        SchemaValidator({'type': 'function'})


def test_try_self_schema_discriminator():
    """Trying to use self-schema when it shouldn't be used"""
    v = SchemaValidator({'type': 'tagged-union', 'choices': {'int': {'type': 'int'}}, 'discriminator': 'self-schema'})
    assert 'discriminator: LookupKey' in repr(v)


def test_build_recursive_schema_from_defs() -> None:
    """
    Validate a schema representing mutually recursive models, analogous to the following JSON schema:

    ```json
    {
        "$schema": "https://json-schema.org/draft/2019-09/schema",
        "oneOf": [{"$ref": "#/$defs/a"}],
        "$defs": {
            "a": {
                "type": "object",
                "properties": {"b": {"type": "array", "items": {"$ref": "#/$defs/a"}}},
                "required": ["b"],
            },
            "b": {
                "type": "object",
                "properties": {"a": {"type": "array", "items": {"$ref": "#/$defs/b"}}},
                "required": ["a"],
            },
        },
    }
    ```
    """

    s = cs.definitions_schema(
        cs.definition_reference_schema(schema_ref='a'),
        [
            cs.typed_dict_schema(
                {'b': cs.typed_dict_field(cs.list_schema(cs.definition_reference_schema('b')))}, ref='a'
            ),
            cs.typed_dict_schema(
                {'a': cs.typed_dict_field(cs.list_schema(cs.definition_reference_schema('a')))}, ref='b'
            ),
        ],
    )

    SchemaValidator(s)
