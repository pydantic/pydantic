from datetime import date

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema


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


@pytest.mark.parametrize(
    'function,args_kwargs,expected_schema',
    [
        [core_schema.any_schema, args(), {'type': 'any'}],
        [core_schema.none_schema, args(), {'type': 'none'}],
        [core_schema.bool_schema, args(), {'type': 'bool'}],
        [core_schema.bool_schema, args(strict=True), {'type': 'bool', 'strict': True}],
        [core_schema.int_schema, args(), {'type': 'int'}],
        [
            core_schema.int_schema,
            args(multiple_of=5, gt=10, lt=20),
            {'type': 'int', 'multiple_of': 5, 'gt': 10, 'lt': 20},
        ],
        [core_schema.float_schema, args(), {'type': 'float'}],
        [core_schema.float_schema, args(multiple_of=5, gt=1.2), {'type': 'float', 'multiple_of': 5, 'gt': 1.2}],
        [core_schema.string_schema, args(), {'type': 'str'}],
        [
            core_schema.string_schema,
            args(min_length=5, max_length=10),
            {'type': 'str', 'min_length': 5, 'max_length': 10},
        ],
        [core_schema.bytes_schema, args(), {'type': 'bytes'}],
        [core_schema.bytes_schema, args(min_length=5, ref='xx'), {'type': 'bytes', 'min_length': 5, 'ref': 'xx'}],
        [core_schema.date_schema, args(), {'type': 'date'}],
        [core_schema.date_schema, args(gt=date(2020, 1, 1)), {'type': 'date', 'gt': date(2020, 1, 1)}],
        [core_schema.time_schema, args(), {'type': 'time'}],
        [core_schema.datetime_schema, args(), {'type': 'datetime'}],
        [core_schema.timedelta_schema, args(), {'type': 'timedelta'}],
        [core_schema.literal_schema, args('a', 'b'), {'type': 'literal', 'expected': ('a', 'b')}],
        [core_schema.is_instance_schema, args(int), {'type': 'is-instance', 'cls': int}],
        [core_schema.callable_schema, args(), {'type': 'callable'}],
        [core_schema.list_schema, args(), {'type': 'list'}],
        [core_schema.list_schema, args({'type': 'int'}), {'type': 'list', 'items_schema': {'type': 'int'}}],
        [
            core_schema.tuple_positional_schema,
            args({'type': 'int'}),
            {'type': 'tuple', 'mode': 'positional', 'items_schema': ({'type': 'int'},)},
        ],
        [
            core_schema.tuple_variable_schema,
            args({'type': 'int'}),
            {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'int'}},
        ],
        [
            core_schema.set_schema,
            args({'type': 'int'}, min_length=4),
            {'type': 'set', 'items_schema': {'type': 'int'}, 'min_length': 4},
        ],
        [
            core_schema.frozenset_schema,
            args({'type': 'int'}, max_length=5),
            {'type': 'frozenset', 'items_schema': {'type': 'int'}, 'max_length': 5},
        ],
        [core_schema.generator_schema, args({'type': 'int'}), {'type': 'generator', 'items_schema': {'type': 'int'}}],
        [core_schema.dict_schema, args(), {'type': 'dict'}],
        [
            core_schema.dict_schema,
            args({'type': 'str'}, {'type': 'int'}),
            {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'int'}},
        ],
        [
            core_schema.function_before_schema,
            args(val_function, {'type': 'int'}),
            {'type': 'function', 'mode': 'before', 'function': val_function, 'schema': {'type': 'int'}},
        ],
        [
            core_schema.function_after_schema,
            args(val_function, {'type': 'int'}),
            {'type': 'function', 'mode': 'after', 'function': val_function, 'schema': {'type': 'int'}},
        ],
        [
            core_schema.function_wrap_schema,
            args(val_function, {'type': 'int'}),
            {'type': 'function', 'mode': 'wrap', 'function': val_function, 'schema': {'type': 'int'}},
        ],
        [
            core_schema.function_plain_schema,
            args(val_function),
            {'type': 'function', 'mode': 'plain', 'function': val_function},
        ],
        [
            core_schema.with_default_schema,
            args({'type': 'int'}, default=5),
            {'type': 'default', 'schema': {'type': 'int'}, 'default': 5},
        ],
        [
            core_schema.with_default_schema,
            args({'type': 'int'}, default=None),
            {'type': 'default', 'schema': {'type': 'int'}, 'default': None},
        ],
        [
            core_schema.with_default_schema,
            args({'type': 'int'}, default_factory=make_5),
            {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': make_5},
        ],
        [core_schema.nullable_schema, args({'type': 'int'}), {'type': 'nullable', 'schema': {'type': 'int'}}],
        [
            core_schema.union_schema,
            args({'type': 'int'}, {'type': 'str'}),
            {'type': 'union', 'choices': ({'type': 'int'}, {'type': 'str'})},
        ],
        [
            core_schema.union_schema,
            args({'type': 'int'}, {'type': 'str'}, custom_error_kind='foobar', custom_error_message='This is Foobar'),
            {
                'type': 'union',
                'choices': ({'type': 'int'}, {'type': 'str'}),
                'custom_error': {'kind': 'foobar', 'message': 'This is Foobar'},
            },
        ],
        [
            core_schema.tagged_union_schema,
            args({'foo': {'type': 'int'}, 'bar': {'type': 'str'}}, 'foo'),
            {
                'type': 'tagged-union',
                'choices': {'foo': {'type': 'int'}, 'bar': {'type': 'str'}},
                'discriminator': 'foo',
            },
        ],
        [
            core_schema.chain_schema,
            args({'type': 'int'}, {'type': 'str'}),
            {'type': 'chain', 'steps': ({'type': 'int'}, {'type': 'str'})},
        ],
        [
            core_schema.typed_dict_field,
            args({'type': 'int'}, required=True),
            {'schema': {'type': 'int'}, 'required': True},
        ],
        [
            core_schema.typed_dict_schema,
            args({'foo': core_schema.typed_dict_field({'type': 'int'})}),
            {'type': 'typed-dict', 'fields': {'foo': {'schema': {'type': 'int'}}}},
        ],
        [
            core_schema.new_class_schema,
            args(MyModel, {'type': 'int'}),
            {'type': 'new-class', 'cls': MyModel, 'schema': {'type': 'int'}},
        ],
        [core_schema.arguments_parameter, args('foo', {'type': 'int'}), {'name': 'foo', 'schema': {'type': 'int'}}],
        [
            core_schema.arguments_schema,
            args(
                core_schema.arguments_parameter('foo', {'type': 'int'}),
                core_schema.arguments_parameter('bar', {'type': 'str'}),
            ),
            {
                'type': 'arguments',
                'arguments_schema': (
                    {'name': 'foo', 'schema': {'type': 'int'}},
                    {'name': 'bar', 'schema': {'type': 'str'}},
                ),
            },
        ],
        [
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
        ],
        [core_schema.recursive_reference_schema, args('foo'), {'type': 'recursive-ref', 'schema_ref': 'foo'}],
    ],
    ids=ids_function,
)
def test_schema_functions(function, args_kwargs, expected_schema):
    args, kwargs = args_kwargs
    schema = function(*args, **kwargs)
    assert schema == expected_schema
    if schema.get('type') not in {None, 'recursive-ref'}:
        v = SchemaValidator(schema)
        try:
            v.validate_python('foobar')
        except ValidationError:
            pass


def test_invalid_custom_error():
    s = core_schema.union_schema({'type': 'int'}, {'type': 'str'}, custom_error_message='foobar')
    with pytest.raises(SchemaError, match=r'custom_error \-> kind\s+Field required'):
        SchemaValidator(s)


def test_invalid_custom_error_kind():
    s = core_schema.union_schema(
        {'type': 'int'}, {'type': 'str'}, custom_error_kind='finite_number', custom_error_message='x'
    )
    with pytest.raises(SchemaError, match='custom_error.message should not be provided if kind matches a known error'):
        SchemaValidator(s)
