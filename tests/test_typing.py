from __future__ import annotations as _annotations

from datetime import date, datetime, time
from typing import Any

from pydantic_core import PydanticKindError, SchemaError, SchemaValidator
from pydantic_core.core_schema import CoreConfig, CoreSchema, function_plain_schema


class Foo:
    bar: str


def foo(bar: str) -> None:
    ...


def validator(value: Any, **kwargs: Any) -> None:
    ...


def test_schema_typing() -> None:
    # this gets run by pyright, but we also check that it executes
    schema: CoreSchema = {
        'type': 'union',
        'choices': [{'type': 'int'}, {'type': 'int', 'ge': 1}, {'type': 'float', 'lt': 1.0}],
    }
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
    schema: CoreSchema = {'type': 'list', 'items_schema': {'type': 'str'}, 'min_length': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'set', 'items_schema': {'type': 'str'}, 'max_length': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'str'}, 'max_length': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'tuple', 'mode': 'positional', 'items_schema': [{'type': 'str'}, {'type': 'int'}]}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'frozenset', 'items_schema': {'type': 'str'}, 'max_length': 3}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'any'}}
    SchemaValidator(schema)
    schema: CoreSchema = {
        'type': 'new-class',
        'cls': Foo,
        'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'bar': {'schema': {'type': 'str'}}}},
    }
    SchemaValidator(schema)
    schema: CoreSchema = {
        'type': 'typed-dict',
        'fields': {
            'a': {'schema': {'type': 'str'}},
            'b': {'schema': {'type': 'str'}, 'alias': 'foobar'},
            'c': {'schema': {'type': 'str'}, 'alias': [['foobar', 0, 'bar'], ['foo']]},
            'd': {'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default': 'spam'}},
        },
    }
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'function', 'mode': 'wrap', 'function': validator, 'schema': {'type': 'str'}}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'function', 'mode': 'plain', 'function': validator}
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
    schema: CoreSchema = {'type': 'is-instance', 'cls': Foo}
    SchemaValidator(schema)
    schema: CoreSchema = {'type': 'callable'}
    SchemaValidator(schema)

    schema: CoreSchema = {
        'type': 'arguments',
        'arguments_schema': [
            {'name': 'a', 'mode': 'positional_only', 'schema': {'type': 'int'}},
            {'name': 'b', 'schema': {'type': 'str'}},
            {'name': 'c', 'mode': 'keyword_only', 'schema': {'type': 'bool'}},
        ],
    }
    SchemaValidator(schema)

    schema: CoreSchema = {'type': 'call', 'arguments_schema': {'type': 'any'}, 'function': foo}
    SchemaValidator(schema)


def test_schema_typing_error() -> None:
    _: CoreSchema = {'type': 'wrong'}  # type: ignore


def test_schema_validator() -> None:
    SchemaValidator({'type': 'int'})


def test_schema_validator_wrong() -> None:
    # use this instead of pytest.raises since pyright complains about input when pytest isn't installed
    try:
        SchemaValidator({'type': 'bad'})  # type: ignore
    except SchemaError:
        pass
    else:
        raise AssertionError('SchemaValidator did not raise SchemaError')


def test_correct_function_signature() -> None:
    def my_validator(value: Any, *, data: Any, config: CoreConfig | None, context: Any, **future_kwargs: Any) -> str:
        return str(value)

    v = SchemaValidator(function_plain_schema(my_validator))
    assert v.validate_python(1) == '1'


def test_wrong_function_signature() -> None:
    def wrong_validator(value: Any) -> Any:
        return value

    v = SchemaValidator(function_plain_schema(wrong_validator))  # type: ignore

    # use this instead of pytest.raises since pyright complains about input when pytest isn't installed
    try:
        v.validate_python(1)
    except TypeError as exc:
        assert 'unexpected keyword argument' in str(exc)
    else:
        raise AssertionError('v.validate_python(1) did not raise TypeError')


def test_kind_error():
    try:
        PydanticKindError('foobar')  # type: ignore
    except KeyError as exc:
        assert str(exc) == '"Invalid error kind: \'foobar\'"'
    else:
        raise AssertionError("PydanticKindError('foobar') did not raise KeyError")

    e = PydanticKindError('recursion_loop')
    assert isinstance(e, PydanticKindError)
