from collections import deque

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import PyAndJson, plain_repr


def test_typed_dict_default():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default': '[default]'},
                },
            },
        }
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    assert v.validate_python({'x': 'x'}) == {'x': 'x', 'y': '[default]'}


def test_typed_dict_omit():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'omit'},
                    'required': False,
                },
            },
        }
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    assert v.validate_python({'x': 'x'}) == {'x': 'x'}
    assert v.validate_python({'x': 'x', 'y': 42}) == {'x': 'x'}


def test_arguments():
    v = SchemaValidator(
        {
            'type': 'arguments',
            'arguments_schema': [
                {
                    'name': 'a',
                    'mode': 'positional_or_keyword',
                    'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 1},
                }
            ],
        }
    )
    assert v.validate_python({'a': 2}) == ((), {'a': 2})
    assert v.validate_python({'__args__': (2,), '__kwargs__': {}}) == ((2,), {})
    assert v.validate_python(()) == ((), {'a': 1})


def test_arguments_omit():
    with pytest.raises(SchemaError, match="Parameter 'a': omit_on_error cannot be used with arguments"):
        SchemaValidator(
            {
                'type': 'arguments',
                'arguments_schema': [
                    {
                        'name': 'a',
                        'mode': 'positional_or_keyword',
                        'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default': 1, 'on_error': 'omit'},
                    }
                ],
            }
        )


@pytest.mark.parametrize(
    'input_value,expected', [([1, 2, 3], [1, 2, 3]), ([1, '2', 3], [1, 2, 3]), ([1, 'wrong', 3], [1, 3])]
)
def test_list_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {'type': 'list', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
    )
    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, '2', 3], [1, 2, 3]),
        ([1, 'wrong', 3], [1, 3]),
        ((1, '2', 3), [1, 2, 3]),
        ((1, 'wrong', 3), [1, 3]),
        (deque([1, '2', 3]), [1, 2, 3]),
        (deque([1, 'wrong', 3]), [1, 3]),
    ],
)
def test_list(input_value, expected):
    v = SchemaValidator(
        {'type': 'list', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
    )
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, '2', 3}, {1, 2, 3}),
        ([1, '2', 3], {1, 2, 3}),
        ([1, 'wrong', 3], {1, 3}),
        (deque([1, '2', 3]), {1, 2, 3}),
        (deque([1, 'wrong', 3]), {1, 3}),
    ],
)
def test_set(input_value, expected):
    v = SchemaValidator(
        {'type': 'set', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
    )
    assert v.validate_python(input_value) == expected


def test_dict_values(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'dict',
            'keys_schema': {'type': 'str'},
            'values_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'},
        }
    )
    assert v.validate_test({'a': 1, 'b': '2'}) == {'a': 1, 'b': 2}
    assert v.validate_test({'a': 1, 'b': 'wrong'}) == {'a': 1}
    assert v.validate_test({'a': 1, 'b': 'wrong', 'c': '3'}) == {'a': 1, 'c': 3}


def test_dict_keys():
    v = SchemaValidator(
        {
            'type': 'dict',
            'keys_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'},
            'values_schema': {'type': 'str'},
        }
    )
    assert v.validate_python({1: 'a', '2': 'b'}) == {1: 'a', 2: 'b'}
    assert v.validate_python({1: 'a', 'wrong': 'b'}) == {1: 'a'}
    assert v.validate_python({1: 'a', 'wrong': 'b', 3: 'c'}) == {1: 'a', 3: 'c'}


def test_tuple_variable(py_and_json: PyAndJson):
    v = py_and_json(
        {'type': 'tuple-variable', 'items_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'}}
    )
    assert v.validate_python((1, 2, 3)) == (1, 2, 3)
    assert v.validate_python([1, '2', 3]) == (1, 2, 3)
    assert v.validate_python([1, 'wrong', 3]) == (1, 3)


def test_tuple_positional():
    v = SchemaValidator(
        {
            'type': 'tuple-positional',
            'items_schema': [{'type': 'int'}, {'type': 'default', 'schema': {'type': 'int'}, 'default': 42}],
        }
    )
    assert v.validate_python((1, '2')) == (1, 2)
    assert v.validate_python([1, '2']) == (1, 2)
    assert v.validate_json('[1, "2"]') == (1, 2)
    assert v.validate_python((1,)) == (1, 42)


def test_tuple_positional_omit():
    v = SchemaValidator(
        {
            'type': 'tuple-positional',
            'items_schema': [{'type': 'int'}, {'type': 'int'}],
            'extra_schema': {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'},
        }
    )
    assert v.validate_python((1, '2')) == (1, 2)
    assert v.validate_python((1, '2', 3, '4')) == (1, 2, 3, 4)
    assert v.validate_python((1, '2', 'wrong', '4')) == (1, 2, 4)
    assert v.validate_python((1, '2', 3, 'x4')) == (1, 2, 3)
    assert v.validate_json('[1, "2", 3, "x4"]') == (1, 2, 3)


def test_on_error_default():
    v = SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'default': 2, 'on_error': 'default'})
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == 2


def test_factory_runtime_error():
    def broken():
        raise RuntimeError('this is broken')

    v = SchemaValidator(
        {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'default', 'default_factory': broken}
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    with pytest.raises(RuntimeError, match='this is broken'):
        v.validate_python('wrong')


def test_factory_type_error():
    def broken(x):
        return 7

    v = SchemaValidator(
        {'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'default', 'default_factory': broken}
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    with pytest.raises(TypeError, match=r"broken\(\) missing 1 required positional argument: 'x'"):
        v.validate_python('wrong')


def test_typed_dict_error():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default_factory': lambda y: y * 2},
                },
            },
        }
    )
    assert v.validate_python({'x': 'x', 'y': 'y'}) == {'x': 'x', 'y': 'y'}
    with pytest.raises(TypeError, match=r"<lambda>\(\) missing 1 required positional argument: 'y'"):
        v.validate_python({'x': 'x'})


def test_on_error_default_not_int():
    v = SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'default': [1, 2, 3], 'on_error': 'default'})
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    a = v.validate_python('wrong')
    assert a == [1, 2, 3]
    # default is not copied, so mutating it mutates the default
    a.append(4)
    assert v.validate_python('wrong') == [1, 2, 3, 4]


def test_on_error_default_factory():
    v = SchemaValidator(
        {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 17, 'on_error': 'default'}
    )
    assert v.validate_python(42) == 42
    assert v.validate_python('42') == 42
    assert v.validate_python('wrong') == 17


def test_on_error_omit():
    v = SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'omit'})
    assert v.validate_python(42) == 42
    with pytest.raises(SchemaError, match='Uncaught Omit error, please check your usage of `default` validators.'):
        v.validate_python('wrong')


def test_on_error_wrong():
    with pytest.raises(SchemaError, match="'on_error = default' requires a `default` or `default_factory`"):
        SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'on_error': 'default'})


def test_build_default_and_default_factory():
    with pytest.raises(SchemaError, match="'default' and 'default_factory' cannot be used together"):
        SchemaValidator({'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 1, 'default': 2})


def test_model_class():
    class MyModel:
        __slots__ = '__dict__', '__pydantic_fields_set__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'default',
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {
                        'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                        'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                    },
                },
                'default': ({'field_a': '[default-a]', 'field_b': '[default-b]'}, set()),
                'on_error': 'default',
            },
        }
    )
    assert 'expect_fields_set:true' in plain_repr(v)
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__pydantic_fields_set__ == {'field_a', 'field_b'}
    m = v.validate_python({'field_a': 'test', 'field_b': 'wrong'})
    assert isinstance(m, MyModel)
    assert m.field_a == '[default-a]'
    assert m.field_b == '[default-b]'
    assert m.__pydantic_fields_set__ == set()


def test_validate_default():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.with_default_schema(core_schema.int_schema(), default='42', validate_default=True)
                )
            }
        )
    )
    assert v.validate_python({'x': '2'}) == {'x': 2}
    assert v.validate_python({}) == {'x': 42}


def test_validate_default_factory():
    v = SchemaValidator(
        core_schema.tuple_positional_schema(
            [core_schema.with_default_schema(core_schema.int_schema(), default_factory=lambda: '42')]
        ),
        config=dict(validate_default=True),
    )
    assert v.validate_python(('2',)) == (2,)
    assert v.validate_python(()) == (42,)


def test_validate_default_error_tuple():
    v = SchemaValidator(
        core_schema.tuple_positional_schema(
            [core_schema.with_default_schema(core_schema.int_schema(), default='wrong', validate_default=True)]
        )
    )
    assert v.validate_python(('2',)) == (2,)
    with pytest.raises(ValidationError, match='Input should be a valid integer,') as exc_info:
        v.validate_python(())

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


def test_validate_default_error_typed_dict():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'x': core_schema.typed_dict_field(
                    core_schema.with_default_schema(core_schema.int_schema(), default='xx', validate_default=True)
                )
            }
        )
    )
    assert v.validate_python({'x': '2'}) == {'x': 2}
    with pytest.raises(ValidationError, match='Input should be a valid integer,') as exc_info:
        v.validate_python({})

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': ('x',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'xx',
        }
    ]
