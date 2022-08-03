from datetime import date, datetime, time

from pydantic_core import Schema, SchemaError, SchemaValidator


class Foo:
    bar: str


def foo(bar: str) -> None:
    ...


def test_schema_typing() -> None:
    # this gets run by pyright, but we also check that it executes
    schema: Schema = {'type': 'union', 'choices': ['int', {'type': 'int', 'ge': 1}, {'type': 'float', 'lt': 1.0}]}
    SchemaValidator(schema)
    schema: Schema = {
        'type': 'tagged-union',
        'discriminator': 'kind',
        'choices': {
            'apple': {'type': 'typed-dict', 'fields': {'pips': {'schema': {'type': 'int'}}}},
            'banana': {'type': 'typed-dict', 'fields': {'curvature': {'schema': {'type': 'float'}}}},
        },
    }
    SchemaValidator(schema)
    schema: Schema = {'type': 'int', 'ge': 1}
    SchemaValidator(schema)
    schema: Schema = {'type': 'float', 'lt': 1.0}
    SchemaValidator(schema)
    schema: Schema = {'type': 'str', 'pattern': r'http://.*'}
    SchemaValidator(schema)
    schema: Schema = {'type': 'bool', 'strict': False}
    SchemaValidator(schema)
    schema: Schema = {'type': 'literal', 'expected': [1, '1']}
    SchemaValidator(schema)
    schema: Schema = {'type': 'any'}
    SchemaValidator(schema)
    schema: Schema = {'type': 'none'}
    SchemaValidator(schema)
    schema: Schema = {'type': 'bytes'}
    SchemaValidator(schema)
    schema: Schema = {'type': 'list', 'items_schema': {'type': 'str'}, 'min_items': 3}
    SchemaValidator(schema)
    schema: Schema = {'type': 'set', 'items_schema': {'type': 'str'}, 'max_items': 3}
    SchemaValidator(schema)
    schema: Schema = {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'str'}, 'max_items': 3}
    SchemaValidator(schema)
    schema: Schema = {'type': 'tuple', 'mode': 'positional', 'items_schema': [{'type': 'str'}, {'type': 'int'}]}
    SchemaValidator(schema)
    schema: Schema = {'type': 'frozenset', 'items_schema': {'type': 'str'}, 'max_items': 3}
    SchemaValidator(schema)
    schema: Schema = {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'any'}}
    SchemaValidator(schema)
    schema: Schema = {
        'type': 'new-class',
        'class_type': Foo,
        'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'bar': {'schema': {'type': 'str'}}}},
    }
    SchemaValidator(schema)
    schema: Schema = {
        'type': 'typed-dict',
        'fields': {
            'a': {'schema': {'type': 'str'}},
            'b': {'schema': {'type': 'str'}, 'alias': 'foobar'},
            'c': {'schema': {'type': 'str'}, 'alias': [['foobar', 0, 'bar'], ['foo']]},
            'd': {'schema': {'type': 'str'}, 'default': 'spam'},
        },
    }
    SchemaValidator(schema)
    schema: Schema = {'type': 'function', 'mode': 'wrap', 'function': foo, 'schema': {'type': 'str'}}
    SchemaValidator(schema)
    schema: Schema = {'type': 'function', 'mode': 'plain', 'function': foo}
    SchemaValidator(schema)
    schema: Schema = {
        'ref': 'Branch',
        'type': 'typed-dict',
        'fields': {
            'name': {'schema': {'type': 'str'}},
            'sub_branch': {
                'schema': {
                    'type': 'union',
                    'choices': [{'type': 'none'}, {'type': 'recursive-ref', 'schema_ref': 'Branch'}],
                },
                'default': None,
            },
        },
    }
    SchemaValidator(schema)
    schema: Schema = {'type': 'date', 'le': date.today()}
    SchemaValidator(schema)
    schema: Schema = {'type': 'time', 'lt': time(12, 13, 14)}
    SchemaValidator(schema)
    schema: Schema = {'type': 'datetime', 'ge': datetime.now()}
    SchemaValidator(schema)
    schema: Schema = {'type': 'is-instance', 'class_': Foo}
    SchemaValidator(schema)
    schema: Schema = {'type': 'callable'}
    SchemaValidator(schema)

    schema: Schema = {
        'type': 'arguments',
        'arguments_schema': [
            {'name': 'a', 'mode': 'positional_only', 'schema': 'int'},
            {'name': 'b', 'schema': 'str'},
            {'name': 'c', 'mode': 'keyword_only', 'schema': 'bool'},
        ],
    }
    SchemaValidator(schema)

    schema: Schema = {'type': 'call', 'arguments_schema': 'any', 'function': foo}
    SchemaValidator(schema)


def test_schema_typing_error() -> None:
    _: Schema = {'type': 'wrong'}  # type: ignore


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
