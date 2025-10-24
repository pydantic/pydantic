import pickle

import pytest

from pydantic_core import SchemaValidator
from pydantic_core import core_schema as cs


def test_schema_as_string():
    v = SchemaValidator(cs.bool_schema())
    assert v.validate_python('tRuE') is True


@pytest.mark.parametrize('pickle_protocol', range(1, pickle.HIGHEST_PROTOCOL + 1))
def test_pickle(pickle_protocol: int) -> None:
    v1 = SchemaValidator(cs.bool_schema())
    assert v1.validate_python('tRuE') is True
    p = pickle.dumps(v1, protocol=pickle_protocol)
    v2 = pickle.loads(p)
    assert v2.validate_python('tRuE') is True
    assert repr(v1) == repr(v2)


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


def test_try_self_schema_discriminator():
    """Trying to use self-schema when it shouldn't be used"""
    v = SchemaValidator(cs.tagged_union_schema(choices={'int': cs.int_schema()}, discriminator='self-schema'))
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
