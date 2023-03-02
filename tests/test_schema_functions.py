import re
from datetime import date

import pytest

from pydantic_core import SchemaError, SchemaSerializer, SchemaValidator, ValidationError, core_schema


def val_function(x, **kwargs):
    return x


def make_5():
    return 5


class MyModel:
    __slots__ = '__dict__', '__fields_set__'


def ids_function(val):
    if callable(val):
        return val.__name__
    elif isinstance(val, tuple) and len(val) == 2:
        return '({})'.format(', '.join([repr(a) for a in val[0]] + [f'{k}={v!r}' for k, v in val[1].items()]))
    else:
        return repr(val)


def args(*args, **kwargs):
    return args, kwargs


all_schema_functions = [
    (core_schema.any_schema, args(), {'type': 'any'}),
    (core_schema.any_schema, args(metadata=['foot', 'spa']), {'type': 'any', 'metadata': ['foot', 'spa']}),
    (core_schema.none_schema, args(), {'type': 'none'}),
    (core_schema.bool_schema, args(), {'type': 'bool'}),
    (core_schema.bool_schema, args(strict=True), {'type': 'bool', 'strict': True}),
    (core_schema.int_schema, args(), {'type': 'int'}),
    (core_schema.int_schema, args(metadata={'fred'}), {'type': 'int', 'metadata': {'fred'}}),
    (core_schema.int_schema, args(multiple_of=5, gt=10, lt=20), {'type': 'int', 'multiple_of': 5, 'gt': 10, 'lt': 20}),
    (core_schema.float_schema, args(), {'type': 'float'}),
    (core_schema.float_schema, args(multiple_of=5, gt=1.2), {'type': 'float', 'multiple_of': 5, 'gt': 1.2}),
    (core_schema.str_schema, args(), {'type': 'str'}),
    (core_schema.str_schema, args(min_length=5, max_length=10), {'type': 'str', 'min_length': 5, 'max_length': 10}),
    (core_schema.bytes_schema, args(), {'type': 'bytes'}),
    (core_schema.bytes_schema, args(min_length=5, ref='xx'), {'type': 'bytes', 'min_length': 5, 'ref': 'xx'}),
    (core_schema.date_schema, args(), {'type': 'date'}),
    (core_schema.date_schema, args(gt=date(2020, 1, 1)), {'type': 'date', 'gt': date(2020, 1, 1)}),
    (core_schema.time_schema, args(), {'type': 'time'}),
    (core_schema.datetime_schema, args(), {'type': 'datetime'}),
    (core_schema.timedelta_schema, args(), {'type': 'timedelta'}),
    (core_schema.literal_schema, args('a', 'b'), {'type': 'literal', 'expected': ('a', 'b')}),
    (core_schema.is_instance_schema, args(int), {'type': 'is-instance', 'cls': int}),
    (core_schema.callable_schema, args(), {'type': 'callable'}),
    (core_schema.list_schema, args(), {'type': 'list'}),
    (core_schema.list_schema, args({'type': 'int'}), {'type': 'list', 'items_schema': {'type': 'int'}}),
    (
        core_schema.tuple_positional_schema,
        args({'type': 'int'}),
        {'type': 'tuple', 'mode': 'positional', 'items_schema': ({'type': 'int'},)},
    ),
    (core_schema.tuple_positional_schema, args(), {'type': 'tuple', 'mode': 'positional', 'items_schema': ()}),
    (
        core_schema.tuple_variable_schema,
        args({'type': 'int'}),
        {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'int'}},
    ),
    (
        core_schema.set_schema,
        args({'type': 'int'}, min_length=4),
        {'type': 'set', 'items_schema': {'type': 'int'}, 'min_length': 4},
    ),
    (
        core_schema.frozenset_schema,
        args({'type': 'int'}, max_length=5),
        {'type': 'frozenset', 'items_schema': {'type': 'int'}, 'max_length': 5},
    ),
    (core_schema.generator_schema, args({'type': 'int'}), {'type': 'generator', 'items_schema': {'type': 'int'}}),
    (core_schema.dict_schema, args(), {'type': 'dict'}),
    (
        core_schema.dict_schema,
        args({'type': 'str'}, {'type': 'int'}),
        {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'int'}},
    ),
    (
        core_schema.function_before_schema,
        args(val_function, {'type': 'int'}),
        {'type': 'function', 'mode': 'before', 'function': val_function, 'schema': {'type': 'int'}},
    ),
    (
        core_schema.function_after_schema,
        args({'type': 'int'}, val_function),
        {'type': 'function', 'mode': 'after', 'function': val_function, 'schema': {'type': 'int'}},
    ),
    (
        core_schema.function_wrap_schema,
        args(val_function, {'type': 'int'}),
        {'type': 'function', 'mode': 'wrap', 'function': val_function, 'schema': {'type': 'int'}},
    ),
    (
        core_schema.function_plain_schema,
        args(val_function),
        {'type': 'function', 'mode': 'plain', 'function': val_function},
    ),
    (
        core_schema.with_default_schema,
        args({'type': 'int'}, default=5),
        {'type': 'default', 'schema': {'type': 'int'}, 'default': 5},
    ),
    (
        core_schema.with_default_schema,
        args({'type': 'int'}, default=None),
        {'type': 'default', 'schema': {'type': 'int'}, 'default': None},
    ),
    (
        core_schema.with_default_schema,
        args({'type': 'int'}, default_factory=make_5),
        {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': make_5},
    ),
    (core_schema.nullable_schema, args({'type': 'int'}), {'type': 'nullable', 'schema': {'type': 'int'}}),
    (
        core_schema.union_schema,
        args({'type': 'int'}, {'type': 'str'}),
        {'type': 'union', 'choices': ({'type': 'int'}, {'type': 'str'})},
    ),
    (
        core_schema.union_schema,
        args({'type': 'int'}, {'type': 'str'}, custom_error_type='foobar', custom_error_message='This is Foobar'),
        {
            'type': 'union',
            'choices': ({'type': 'int'}, {'type': 'str'}),
            'custom_error_type': 'foobar',
            'custom_error_message': 'This is Foobar',
        },
    ),
    (
        core_schema.tagged_union_schema,
        args({'foo': {'type': 'int'}, 'bar': {'type': 'str'}}, 'foo'),
        {'type': 'tagged-union', 'choices': {'foo': {'type': 'int'}, 'bar': {'type': 'str'}}, 'discriminator': 'foo'},
    ),
    (
        core_schema.chain_schema,
        args({'type': 'int'}, {'type': 'str'}),
        {'type': 'chain', 'steps': ({'type': 'int'}, {'type': 'str'})},
    ),
    (core_schema.typed_dict_field, args({'type': 'int'}, required=True), {'schema': {'type': 'int'}, 'required': True}),
    (
        core_schema.typed_dict_schema,
        args({'foo': core_schema.typed_dict_field({'type': 'int'})}),
        {'type': 'typed-dict', 'fields': {'foo': {'schema': {'type': 'int'}}}},
    ),
    (
        core_schema.model_schema,
        args(MyModel, {'type': 'int'}),
        {'type': 'model', 'cls': MyModel, 'schema': {'type': 'int'}},
    ),
    (core_schema.arguments_parameter, args('foo', {'type': 'int'}), {'name': 'foo', 'schema': {'type': 'int'}}),
    (
        core_schema.arguments_schema,
        args(
            core_schema.arguments_parameter('foo', {'type': 'int'}),
            core_schema.arguments_parameter('bar', {'type': 'str'}),
            serialization=core_schema.format_ser_schema('d'),
        ),
        {
            'type': 'arguments',
            'arguments_schema': (
                {'name': 'foo', 'schema': {'type': 'int'}},
                {'name': 'bar', 'schema': {'type': 'str'}},
            ),
            'serialization': {'type': 'format', 'formatting_string': 'd'},
        },
    ),
    (
        core_schema.call_schema,
        args(core_schema.arguments_schema(core_schema.arguments_parameter('foo', {'type': 'int'})), val_function),
        {
            'type': 'call',
            'function': val_function,
            'arguments_schema': {
                'type': 'arguments',
                'arguments_schema': ({'name': 'foo', 'schema': {'type': 'int'}},),
            },
        },
    ),
    (
        core_schema.custom_error_schema,
        args(core_schema.int_schema(), 'foobar', custom_error_message='Hello'),
        {
            'type': 'custom-error',
            'schema': {'type': 'int'},
            'custom_error_type': 'foobar',
            'custom_error_message': 'Hello',
        },
    ),
    (core_schema.json_schema, args({'type': 'int'}), {'type': 'json', 'schema': {'type': 'int'}}),
    (core_schema.url_schema, args(), {'type': 'url'}),
    (core_schema.multi_host_url_schema, args(), {'type': 'multi-host-url'}),
    (
        core_schema.lax_or_strict_schema,
        args({'type': 'int'}, {'type': 'int'}),
        {'type': 'lax-or-strict', 'lax_schema': {'type': 'int'}, 'strict_schema': {'type': 'int'}},
    ),
    (core_schema.is_subclass_schema, args(MyModel), {'type': 'is-subclass', 'cls': MyModel}),
    (
        core_schema.definitions_schema,
        args({'type': 'int'}, [{'type': 'int'}]),
        {'type': 'definitions', 'schema': {'type': 'int'}, 'definitions': [{'type': 'int'}]},
    ),
    (core_schema.definition_reference_schema, args('foo'), {'type': 'definition-ref', 'schema_ref': 'foo'}),
]


@pytest.mark.parametrize('function,args_kwargs,expected_schema', all_schema_functions, ids=ids_function)
def test_schema_functions(function, args_kwargs, expected_schema):
    args, kwargs = args_kwargs
    schema = function(*args, **kwargs)
    assert schema == expected_schema
    if schema.get('type') in {None, 'definition-ref'}:
        return

    v = SchemaValidator(schema)
    try:
        v.validate_python('foobar')
    except ValidationError:
        pass

    # also build the serializer, just to check it doesn't raise an error
    SchemaSerializer(schema)


def test_all_schema_functions_used():
    all_types = {
        re.sub(r".+'(.+?)'.+", r'\1', s.__annotations__['type'].__forward_arg__)
        for s in core_schema.CoreSchema.__args__
    }
    types_used = {args['type'] for _, _, args in all_schema_functions if 'type' in args}

    assert all_types == types_used


def test_invalid_custom_error():
    s = core_schema.union_schema({'type': 'int'}, {'type': 'str'}, custom_error_type='foobar')
    with pytest.raises(SchemaError, match=r"KeyError: 'custom_error_message'"):
        SchemaValidator(s)


def test_invalid_custom_error_type():
    s = core_schema.union_schema(
        {'type': 'int'}, {'type': 'str'}, custom_error_type='finite_number', custom_error_message='x'
    )
    msg = "custom_error.message should not be provided if 'custom_error_type' matches a known error"
    with pytest.raises(SchemaError, match=msg):
        SchemaValidator(s)


def repr_function(value, _info):
    return repr(value)


@pytest.mark.parametrize('json_return_type', core_schema.JsonReturnTypes.__args__)
def test_expected_serialization_types(json_return_type):
    SchemaSerializer(
        core_schema.any_schema(
            serialization=core_schema.function_plain_ser_schema(repr_function, json_return_type=json_return_type)
        )
    )
