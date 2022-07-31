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
                        'kind': 'int_parsing',
                        'loc': ['apple', 'bar'],
                        'message': 'Input should be a valid integer, unable to parse string as an integer',
                        'input_value': 'wrong',
                    }
                ],
            ),
        ),
        (
            {'foo': 'banana'},
            Err(
                'Field required',
                [
                    {
                        'kind': 'missing',
                        'loc': ['banana', 'spam'],
                        'message': 'Field required',
                        'input_value': {'foo': 'banana'},
                    }
                ],
            ),
        ),
        (
            {'foo': 'other'},
            Err(
                'union_tag_invalid',
                [
                    {
                        'kind': 'union_tag_invalid',
                        'loc': [],
                        'message': (
                            "Input tag 'other' found using 'foo' does not match any "
                            "of the expected tags: 'apple', 'banana'"
                        ),
                        'input_value': {'foo': 'other'},
                        'context': {'discriminator': "'foo'", 'tag': 'other', 'expected_tags': "'apple', 'banana'"},
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
                        'kind': 'union_tag_not_found',
                        'loc': [],
                        'message': "Unable to extract tag using discriminator 'foo'",
                        'input_value': {},
                        'context': {'discriminator': "'foo'"},
                    }
                ],
            ),
        ),
        (
            'not a dict',
            Err(
                'dict_type',
                [
                    {
                        'kind': 'dict_type',
                        'loc': [],
                        'message': 'Input should be a valid dictionary',
                        'input_value': 'not a dict',
                    }
                ],
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
                'apple': {'type': 'typed-dict', 'fields': {'foo': {'schema': 'str'}, 'bar': {'schema': 'int'}}},
                'banana': {
                    'type': 'typed-dict',
                    'fields': {'foo': {'schema': 'str'}, 'spam': {'schema': {'type': 'list', 'items_schema': 'int'}}},
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
                'apple': {'type': 'typed-dict', 'fields': {'a': {'schema': 'str'}, 'b': {'schema': 'int'}}},
                'banana': {
                    'type': 'typed-dict',
                    'fields': {'c': {'schema': 'str'}, 'd': {'schema': {'type': 'list', 'items_schema': 'int'}}},
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
            'kind': 'union_tag_not_found',
            'loc': [],
            'message': "Unable to extract tag using discriminator 'food' | 'menu'.1",
            'input_value': {},
            'context': {'discriminator': "'food' | 'menu'.1"},
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
                        'kind': 'literal_error',
                        'loc': ['str'],
                        'message': "Input should be one of: 'foo', 'bar'",
                        'input_value': 'baz',
                        'context': {'expected': "'foo', 'bar'"},
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
                        'kind': 'union_tag_not_found',
                        'loc': [],
                        'message': 'Unable to extract tag using discriminator discriminator_function()',
                        'input_value': None,
                        'context': {'discriminator': 'discriminator_function()'},
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
                        'kind': 'union_tag_invalid',
                        'loc': [],
                        'message': (
                            "Input tag 'other' found using discriminator_function() "
                            "does not match any of the expected tags: 'str', 'int'"
                        ),
                        'input_value': ['wrong type'],
                        'context': {
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
                'apple': {'type': 'typed-dict', 'fields': {'a': {'schema': 'str'}, 'b': {'schema': 'int'}}},
                'banana': {'type': 'typed-dict', 'fields': {'c': {'schema': 'str'}, 'd': {'schema': 'int'}}},
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
                'apple': {'type': 'typed-dict', 'ref': 'apple', 'fields': {'a': {'schema': 'str'}}},
                'apple2': {'type': 'recursive-ref', 'schema_ref': 'apple'},
                'banana': {'type': 'typed-dict', 'fields': {'b': {'schema': 'str'}}},
            },
        },
        {'from_attributes': True},
    )
    assert v.validate_python({'foobar': 'apple', 'a': 'apple'}) == {'a': 'apple'}
    assert v.validate_python({'foobar': 'apple2', 'a': 'apple'}) == {'a': 'apple'}
    assert v.validate_python({'foobar': 'banana', 'b': 'banana'}) == {'b': 'banana'}


def test_downcast_error():
    v = SchemaValidator({'type': 'tagged-union', 'discriminator': lambda x: 123, 'choices': {'str': 'str'}})
    with pytest.raises(TypeError, match="'int' object cannot be converted to 'PyString'"):
        v.validate_python('x')
