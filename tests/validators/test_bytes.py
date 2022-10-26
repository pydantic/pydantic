import re
from typing import Any, Dict

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson


def test_strict_bytes_validator():
    v = SchemaValidator({'type': 'bytes', 'strict': True})

    assert v.validate_python(b'foo') == b'foo'
    assert v.validate_json('"foo"') == b'foo'

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        v.validate_python('foo')
    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        v.validate_python(bytearray(b'foo'))


def test_lax_bytes_validator():
    v = SchemaValidator({'type': 'bytes'})

    assert v.validate_python(b'foo') == b'foo'
    assert v.validate_python('foo') == b'foo'
    assert v.validate_python(bytearray(b'foo')) == b'foo'

    assert v.validate_json('"foo"') == b'foo'

    assert v.validate_python('🐈 Hello') == b'\xf0\x9f\x90\x88 Hello'
    # `.to_str()` Returns a `UnicodeEncodeError` if the input is not valid unicode (containing unpaired surrogates).
    # https://github.com/PyO3/pyo3/blob/6503128442b8f3e767c663a6a8d96376d7fb603d/src/types/string.rs#L477
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('🐈 Hello \ud800World')
    assert exc_info.value.errors() == [
        {
            'type': 'string_unicode',
            'loc': (),
            'msg': 'Input should be a valid string, unable to parse raw data as a unicode string',
            'input': '🐈 Hello \ud800World',
        }
    ]


@pytest.mark.parametrize(
    'opts,input,expected',
    [
        ({}, b'foo', b'foo'),
        ({'max_length': 5}, b'foo', b'foo'),
        ({'max_length': 5}, b'foobar', Err('Data should have at most 5 bytes')),
        ({'min_length': 2}, b'foo', b'foo'),
        ({'min_length': 2}, b'f', Err('Data should have at least 2 bytes')),
        ({'min_length': 1, 'max_length': 6, 'strict': True}, b'bytes?', b'bytes?'),
    ],
)
def test_constrained_bytes_python_bytes(opts: Dict[str, Any], input, expected):
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
        ({'max_length': 5}, 'foobar', Err('Data should have at most 5 bytes')),
        ({'min_length': 2}, 'foo', b'foo'),
        ({'min_length': 2}, 'f', Err('Data should have at least 2 bytes')),
        ({}, 1, Err('Input should be a valid bytes')),
        ({}, 1.0, Err('Input should be a valid bytes')),
        ({}, [], Err('Input should be a valid bytes')),
        ({}, {}, Err('Input should be a valid bytes')),
    ],
)
def test_constrained_bytes(py_and_json: PyAndJson, opts: Dict[str, Any], input, expected):
    v = py_and_json({'type': 'bytes', **opts})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input)
        assert v.isinstance_test(input) is False
    else:
        assert v.validate_test(input) == expected
        assert v.isinstance_test(input) is True


def test_union():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'str'}, {'type': 'bytes'}], 'strict': True})
    assert v.validate_python('oh, a string') == 'oh, a string'
    assert v.validate_python(b'oh, bytes') == b'oh, bytes'


def test_length_ctx():
    v = SchemaValidator({'type': 'bytes', 'min_length': 2, 'max_length': 3})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(b'1')
    assert exc_info.value.errors() == [
        {
            'type': 'bytes_too_short',
            'loc': (),
            'msg': 'Data should have at least 2 bytes',
            'input': b'1',
            'ctx': {'min_length': 2},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(b'1234')

    assert exc_info.value.errors() == [
        {
            'type': 'bytes_too_long',
            'loc': (),
            'msg': 'Data should have at most 3 bytes',
            'input': b'1234',
            'ctx': {'max_length': 3},
        }
    ]
