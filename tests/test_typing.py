from datetime import date, datetime, time

from pydantic_core import SchemaError, SchemaValidator
from pydantic_core.core_schema import CoreSchema, CoreSchemaCombined, CoreSchemaStrings


class Foo:
    bar: str


def foo(bar: str) -> None:
    ...


def test_schema_typing() -> None:
    # this gets run by pyright, but we also check that it executes
    schema: CoreSchema = {'type': 'union', 'choices': ['int', {'type': 'int', 'ge': 1}, {'type': 'float', 'lt': 1.0}]}
    SchemaValidator(schema)
    schema: CoreSchema = {
        'type': 'tagged-union',
        'discriminator': 'kind',
        'choices': {
            'apple': {'type': 'typed-dict', 'fields': {'pips': {'schema': {'type': 'int'}}}},
            'banana': {'type': 'typed-dict', 'fields': {'curvature': {'schema': {'type': 'float'}}}},
        },
    }
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'int', 'ge': 1}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'float', 'lt': 1.0}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'str', 'pattern': r'http://.*'}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'bool', 'strict': False}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'literal', 'expected': [1, '1']}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'any'}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'none'}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'bytes'}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'list', 'items_schema': {'type': 'str'}, 'min_items': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'set', 'items_schema': {'type': 'str'}, 'max_items': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'str'}, 'max_items': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'tuple', 'mode': 'positional', 'items_schema': [{'type': 'str'}, {'type': 'int'}]}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'frozenset', 'items_schema': {'type': 'str'}, 'max_items': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'any'}}
    SchemaValidator(schema)
    schema: CoreSchema = {
        'type': 'new-class',
        'class_type': Foo,
        'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'bar': {'schema': {'type': 'str'}}}},
    }
    SchemaValidator(schema)
    schema: CoreSchema = {
        'type': 'typed-dict',
        'fields': {
            'a': {'schema': {'type': 'str'}},
            'b': {'schema': {'type': 'str'}, 'alias': 'foobar'},
            'c': {'schema': {'type': 'str'}, 'alias': [['foobar', 0, 'bar'], ['foo']]},
            'd': {'schema': {'type': 'default', 'schema': 'str', 'default': 'spam'}},
        },
    }
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'function', 'mode': 'wrap', 'function': foo, 'schema': {'type': 'str'}}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'function', 'mode': 'plain', 'function': foo}
    SchemaValidator(schema)
    schema: CoreSchema = {
        'ref': 'Branch',
        'type': 'typed-dict',
        'fields': {
            'name': {'schema': {'type': 'str'}},
            'sub_branch': {
                'schema': {
                    'type': 'default',
                    'schema': {
                        'type': 'union',
                        'choices': [{'type': 'none'}, {'type': 'recursive-ref', 'schema_ref': 'Branch'}],
                    },
                    'default': None,
                }
            },
        },
    }
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'date', 'le': date.today()}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'time', 'lt': time(12, 13, 14)}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'datetime', 'ge': datetime.now()}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'is-instance', 'class_': Foo}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'callable'}
    SchemaValidator(schema)

    schema: CoreSchema = {
        'type': 'arguments',
        'arguments_schema': [
            {'name': 'a', 'mode': 'positional_only', 'schema': 'int'},
            {'name': 'b', 'schema': 'str'},
            {'name': 'c', 'mode': 'keyword_only', 'schema': 'bool'},
        ],
    }
    SchemaValidator(schema)

    schema: CoreSchema = {'type': 'call', 'arguments_schema': 'any', 'function': foo}
    SchemaValidator(schema)


def test_schema_unions():
    schema_str: CoreSchemaStrings = 'int'
    SchemaValidator(schema_str)

    schema_str_combined: CoreSchemaCombined = 'int'
    SchemaValidator(schema_str_combined)

    schema_dict_combined: CoreSchemaCombined = {'type': 'int'}
    SchemaValidator(schema_dict_combined)


def test_schema_typing_error() -> None:
    _: CoreSchema = {'type': 'wrong'}  # type: ignore


def test_schema_validator() -> None:
    SchemaValidator('int')


def test_schema_validator_wrong() -> None:
    # use this instead of pytest.raises since pyright complains about input when pytest isn't installed
    try:
        SchemaValidator('bad')  # type: ignore
    except SchemaError:
        pass
    else:
        raise AssertionError('SchemaValidator did not raise SchemaError')
