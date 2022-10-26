import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson
from .test_typed_dict import Cls


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': 'apple', 'bar': '123'}, {'foo': 'apple', 'bar': 123}),
        ({'foo': 'banana', 'spam': [1, 2, '3']}, {'foo': 'banana', 'spam': [1, 2, 3]}),
        (
            {'foo': 'apple', 'bar': 'wrong'},
            Err(
                'Input should be a valid integer',
                [
                    {
                        'type': 'int_parsing',
                        'loc': ('apple', 'bar'),
                        'msg': 'Input should be a valid integer, unable to parse string as an integer',
                        'input': 'wrong',
                    }
                ],
            ),
        ),
        (
            {'foo': 'banana'},
            Err(
                'Field required',
                [{'type': 'missing', 'loc': ('banana', 'spam'), 'msg': 'Field required', 'input': {'foo': 'banana'}}],
            ),
        ),
        (
            {'foo': 'other'},
            Err(
                'union_tag_invalid',
                [
                    {
                        'type': 'union_tag_invalid',
                        'loc': (),
                        'msg': (
                            "Input tag 'other' found using 'foo' does not match any "
                            "of the expected tags: 'apple', 'banana'"
                        ),
                        'input': {'foo': 'other'},
                        'ctx': {'discriminator': "'foo'", 'tag': 'other', 'expected_tags': "'apple', 'banana'"},
                    }
                ],
            ),
        ),
        (
            {},
            Err(
                'union_tag_not_found',
                [
                    {
                        'type': 'union_tag_not_found',
                        'loc': (),
                        'msg': "Unable to extract tag using discriminator 'foo'",
                        'input': {},
                        'ctx': {'discriminator': "'foo'"},
                    }
                ],
            ),
        ),
        (
            'not a dict',
            Err(
                'dict_type',
                [{'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': 'not a dict'}],
            ),
        ),
    ],
    ids=repr,
)
def test_simple_tagged_union(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'tagged-union',
            'discriminator': 'foo',
            'choices': {
                'apple': {
                    'type': 'typed-dict',
                    'fields': {'foo': {'schema': {'type': 'str'}}, 'bar': {'schema': {'type': 'int'}}},
                },
                'banana': {
                    'type': 'typed-dict',
                    'fields': {
                        'foo': {'schema': {'type': 'str'}},
                        'spam': {'schema': {'type': 'list', 'items_schema': {'type': 'int'}}},
                    },
                },
            },
        }
    )
    assert 'discriminator: LookupKey' in repr(v.validator)
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


def test_discriminator_path(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'tagged-union',
            'discriminator': [['food'], ['menu', 1]],
            'choices': {
                'apple': {
                    'type': 'typed-dict',
                    'fields': {'a': {'schema': {'type': 'str'}}, 'b': {'schema': {'type': 'int'}}},
                },
                'banana': {
                    'type': 'typed-dict',
                    'fields': {
                        'c': {'schema': {'type': 'str'}},
                        'd': {'schema': {'type': 'list', 'items_schema': {'type': 'int'}}},
                    },
                },
            },
        }
    )
    assert v.validate_test({'food': 'apple', 'a': 'apple', 'b': '13'}) == {'a': 'apple', 'b': 13}
    assert v.validate_test({'menu': ['x', 'banana'], 'c': 'C', 'd': [1, '2']}) == {'c': 'C', 'd': [1, 2]}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({})
    assert exc_info.value.errors() == [
        {
            'type': 'union_tag_not_found',
            'loc': (),
            'msg': "Unable to extract tag using discriminator 'food' | 'menu'.1",
            'input': {},
            'ctx': {'discriminator': "'food' | 'menu'.1"},
        }
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('foo', 'foo'),
        (123, 123),
        (
            'baz',
            Err(
                'literal_error',
                [
                    {
                        'type': 'literal_error',
                        'loc': ('str',),
                        'msg': "Input should be 'foo' or 'bar'",
                        'input': 'baz',
                        'ctx': {'expected': "'foo' or 'bar'"},
                    }
                ],
            ),
        ),
        (
            None,
            Err(
                'union_tag_not_found',
                [
                    {
                        'type': 'union_tag_not_found',
                        'loc': (),
                        'msg': 'Unable to extract tag using discriminator discriminator_function()',
                        'input': None,
                        'ctx': {'discriminator': 'discriminator_function()'},
                    }
                ],
            ),
        ),
        (
            ['wrong type'],
            Err(
                'union_tag_invalid',
                [
                    {
                        'type': 'union_tag_invalid',
                        'loc': (),
                        'msg': (
                            "Input tag 'other' found using discriminator_function() "
                            "does not match any of the expected tags: 'str', 'int'"
                        ),
                        'input': ['wrong type'],
                        'ctx': {
                            'discriminator': 'discriminator_function()',
                            'tag': 'other',
                            'expected_tags': "'str', 'int'",
                        },
                    }
                ],
            ),
        ),
    ],
)
def test_discriminator_function(py_and_json: PyAndJson, input_value, expected):
    def discriminator_function(obj):
        if isinstance(obj, str):
            return 'str'
        elif isinstance(obj, int):
            return 'int'
        elif obj is None:
            return None
        else:
            return 'other'

    v = py_and_json(
        {
            'type': 'tagged-union',
            'discriminator': discriminator_function,
            'choices': {'str': {'type': 'literal', 'expected': ['foo', 'bar']}, 'int': {'type': 'int'}},
        }
    )
    assert 'discriminator: Function' in repr(v.validator)
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message) as exc_info:
            v.validate_python(input_value)
        # debug(exc_info.value.errors())
        assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


def test_from_attributes():
    v = SchemaValidator(
        {
            'type': 'tagged-union',
            'discriminator': 'foobar',
            'choices': {
                'apple': {
                    'type': 'typed-dict',
                    'fields': {'a': {'schema': {'type': 'str'}}, 'b': {'schema': {'type': 'int'}}},
                },
                'banana': {
                    'type': 'typed-dict',
                    'fields': {'c': {'schema': {'type': 'str'}}, 'd': {'schema': {'type': 'int'}}},
                },
            },
        },
        {'from_attributes': True},
    )
    assert v.validate_python({'foobar': 'apple', 'a': 'apple', 'b': '13'}) == {'a': 'apple', 'b': 13}
    assert v.validate_python(Cls(foobar='apple', a='apple', b='13')) == {'a': 'apple', 'b': 13}
    assert v.validate_python({'foobar': 'banana', 'c': 'banana', 'd': '31'}) == {'c': 'banana', 'd': 31}
    assert v.validate_python(Cls(foobar='banana', c='banana', d='31')) == {'c': 'banana', 'd': 31}


def test_use_ref():
    v = SchemaValidator(
        {
            'type': 'tagged-union',
            'discriminator': 'foobar',
            'choices': {
                'apple': {'type': 'typed-dict', 'ref': 'apple', 'fields': {'a': {'schema': {'type': 'str'}}}},
                'apple2': {'type': 'recursive-ref', 'schema_ref': 'apple'},
                'banana': {'type': 'typed-dict', 'fields': {'b': {'schema': {'type': 'str'}}}},
            },
        },
        {'from_attributes': True},
    )
    assert v.validate_python({'foobar': 'apple', 'a': 'apple'}) == {'a': 'apple'}
    assert v.validate_python({'foobar': 'apple2', 'a': 'apple'}) == {'a': 'apple'}
    assert v.validate_python({'foobar': 'banana', 'b': 'banana'}) == {'b': 'banana'}


def test_downcast_error():
    v = SchemaValidator({'type': 'tagged-union', 'discriminator': lambda x: 123, 'choices': {'str': {'type': 'str'}}})
    with pytest.raises(TypeError, match="'int' object cannot be converted to 'PyString'"):
        v.validate_python('x')


def test_custom_error():
    v = SchemaValidator(
        {
            'type': 'tagged-union',
            'discriminator': 'foo',
            'custom_error_type': 'snap',
            'custom_error_message': 'Input should be a foo or bar',
            'choices': {
                'apple': {
                    'type': 'typed-dict',
                    'fields': {'foo': {'schema': {'type': 'str'}}, 'bar': {'schema': {'type': 'int'}}},
                },
                'banana': {
                    'type': 'typed-dict',
                    'fields': {
                        'foo': {'schema': {'type': 'str'}},
                        'spam': {'schema': {'type': 'list', 'items_schema': {'type': 'int'}}},
                    },
                },
            },
        }
    )
    assert v.validate_python({'foo': 'apple', 'bar': '123'}) == {'foo': 'apple', 'bar': 123}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'spam': 'apple', 'bar': 'Bar'})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'snap', 'loc': (), 'msg': 'Input should be a foo or bar', 'input': {'spam': 'apple', 'bar': 'Bar'}}
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'foo': 'other', 'bar': 'Bar'})
    assert exc_info.value.errors() == [
        {'type': 'snap', 'loc': (), 'msg': 'Input should be a foo or bar', 'input': {'foo': 'other', 'bar': 'Bar'}}
    ]


def test_custom_error_type():
    v = SchemaValidator(
        {
            'type': 'tagged-union',
            'discriminator': 'foo',
            'custom_error_type': 'finite_number',
            'choices': {
                'apple': {
                    'type': 'typed-dict',
                    'fields': {'foo': {'schema': {'type': 'str'}}, 'bar': {'schema': {'type': 'int'}}},
                },
                'banana': {
                    'type': 'typed-dict',
                    'fields': {
                        'foo': {'schema': {'type': 'str'}},
                        'spam': {'schema': {'type': 'list', 'items_schema': {'type': 'int'}}},
                    },
                },
            },
        }
    )
    assert v.validate_python({'foo': 'apple', 'bar': '123'}) == {'foo': 'apple', 'bar': 123}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'spam': 'apple', 'bar': 'Bar'})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'finite_number',
            'loc': (),
            'msg': 'Input should be a finite number',
            'input': {'spam': 'apple', 'bar': 'Bar'},
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'foo': 'other', 'bar': 'Bar'})
    assert exc_info.value.errors() == [
        {
            'type': 'finite_number',
            'loc': (),
            'msg': 'Input should be a finite number',
            'input': {'foo': 'other', 'bar': 'Bar'},
        }
    ]
