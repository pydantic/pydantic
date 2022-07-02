import re

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err


def test_strict_bytes_validator():
    v = SchemaValidator({'type': 'bytes', 'strict': True})

    assert v.validate_python(b'foo') == b'foo'
    assert v.validate_json('"foo"') == b'foo'

    with pytest.raises(ValidationError, match='Value must be a valid bytes'):
        assert v.validate_python('foo') == b'foo'


def test_lax_bytes_validator():
    v = SchemaValidator({'type': 'bytes'})

    assert v.validate_python(b'foo') == b'foo'
    assert v.validate_python('foo') == b'foo'

    assert v.validate_json('"foo"') == b'foo'


@pytest.mark.parametrize(
    'opts,input,expected',
    [
        ({}, b'foo', b'foo'),
        ({'max_length': 5}, b'foo', b'foo'),
        ({'max_length': 5}, b'foobar', Err('Data must have at most 5 bytes')),
        ({'min_length': 2}, b'foo', b'foo'),
        ({'min_length': 2}, b'f', Err('Data must have at least 2 bytes')),
        ({'min_length': 1, 'max_length': 6, 'strict': True}, b'bytes?', b'bytes?'),
    ],
)
def test_constrained_bytes_python_bytes(opts, input, expected):
    v = SchemaValidator({'type': 'bytes', **opts})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input)
    else:
        assert v.validate_python(input) == expected


@pytest.mark.parametrize(
    'opts,input,expected',
    [
        ({}, 'foo', b'foo'),
        ({'max_length': 5}, 'foo', b'foo'),
        ({'max_length': 5}, 'foobar', Err('Data must have at most 5 bytes')),
        ({'min_length': 2}, 'foo', b'foo'),
        ({'min_length': 2}, 'f', Err('Data must have at least 2 bytes')),
        ({}, 1, Err('Value must be a valid bytes')),
        ({}, 1.0, Err('Value must be a valid bytes')),
        ({}, [], Err('Value must be a valid bytes')),
        ({}, {}, Err('Value must be a valid bytes')),
    ],
)
def test_constrained_bytes(py_or_json, opts, input, expected):
    v = py_or_json({'type': 'bytes', **opts})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input)
        assert v.isinstance_test(input) is False
    else:
        assert v.validate_test(input) == expected
        assert v.isinstance_test(input) is True


def test_union():
    v = SchemaValidator({'type': 'union', 'choices': ['str', 'bytes'], 'strict': True})
    assert v.validate_python('oh, a string') == 'oh, a string'
    assert v.validate_python(b'oh, bytes') == b'oh, bytes'


def test_length_ctx():
    v = SchemaValidator({'type': 'bytes', 'min_length': 2, 'max_length': 3})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(b'1')
    assert exc_info.value.errors() == [
        {
            'kind': 'too_short',
            'loc': [],
            'message': 'Data must have at least 2 bytes',
            'input_value': b'1',
            'context': {'min_length': 2},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(b'1234')

    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': [],
            'message': 'Data must have at most 3 bytes',
            'input_value': b'1234',
            'context': {'max_length': 3},
        }
    ]
