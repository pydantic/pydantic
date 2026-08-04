from typing import Annotated

import annotated_types
import pytest

from pydantic import BaseModel, Field, Strict, StrictBytes, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        pytest.param('s', b's', id='s_str'),
        pytest.param('  s  ', b'  s  ', id='s_str_untouched'),
        pytest.param(b's', b's', id='s_bytes'),
        (1, ValidationError),
        (bytearray('xx', encoding='utf8'), b'xx'),
        (True, ValidationError),
        (False, ValidationError),
        ({}, ValidationError),
        pytest.param('x' * 11, b'x' * 11, id='long_str'),
        pytest.param(b'x' * 11, b'x' * 11, id='long_bytes'),
    ],
)
def test_bytes_validation(value, expected):
    ta = TypeAdapter(bytes)

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_constrained_bytes_good():
    ta = TypeAdapter(Annotated[bytes, annotated_types.Len(0, 10)])

    assert ta.validate_python(b'short') == b'short'


def test_constrained_bytes_default():
    class Model(BaseModel):
        v: Annotated[bytes, annotated_types.Len(0, 10)] = b'foobar'

    m = Model()
    assert m.v == b'foobar'


@pytest.mark.parametrize(
    ('data', 'valid'),
    [(b'this is too long', False), ('⪶⓲⽷01'.encode(), False), (b'not long90', True), ('⪶⓲⽷0'.encode(), True)],
)
def test_constrained_bytes_too_long(data: bytes, valid: bool):
    ta = TypeAdapter(Annotated[bytes, annotated_types.Len(0, 10)])

    if valid:
        assert ta.validate_python(data) == data
    else:
        with pytest.raises(ValidationError) as exc_info:
            ta.validate_python(data)
        # insert_assert(exc_info.value.errors(include_url=False))
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'max_length': 10},
                'input': data,
                'loc': (),
                'msg': 'Data should have at most 10 bytes',
                'type': 'bytes_too_long',
            }
        ]


def test_constrained_bytes_strict_true():
    ta = TypeAdapter(Annotated[bytes, Strict()])

    assert ta.validate_python(b'foobar') == b'foobar'
    with pytest.raises(ValidationError):
        ta.validate_python(bytearray('foobar', 'utf-8'))

    with pytest.raises(ValidationError):
        ta.validate_python('foostring')

    with pytest.raises(ValidationError):
        ta.validate_python(42)

    with pytest.raises(ValidationError):
        ta.validate_python(0.42)


def test_constrained_bytes_strict_false():
    ta = TypeAdapter(Annotated[bytes, Strict(False)])

    assert ta.validate_python(b'foobar') == b'foobar'
    assert ta.validate_python(bytearray('foobar', 'utf-8')) == b'foobar'
    assert ta.validate_python('foostring') == b'foostring'

    with pytest.raises(ValidationError):
        ta.validate_python(42)

    with pytest.raises(ValidationError):
        ta.validate_python(0.42)


def test_constrained_bytes_strict_default():
    ta = TypeAdapter(bytes)

    assert ta.validate_python(b'foobar') == b'foobar'
    assert ta.validate_python(bytearray('foobar', 'utf-8')) == b'foobar'
    assert ta.validate_python('foostring') == b'foostring'

    with pytest.raises(ValidationError):
        ta.validate_python(42)

    with pytest.raises(ValidationError):
        ta.validate_python(0.42)


def test_strict_bytes():
    ta = TypeAdapter(StrictBytes)

    assert ta.validate_python(b'foobar') == b'foobar'
    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        ta.validate_python(bytearray('foobar', 'utf-8'))

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        ta.validate_python('foostring')

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        ta.validate_python(42)

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        ta.validate_python(0.42)


def test_strict_bytes_max_length():
    ta = TypeAdapter(Annotated[StrictBytes, Field(max_length=5)])

    assert ta.validate_python(b'foo') == b'foo'

    with pytest.raises(ValidationError, match=r'Input should be a valid bytes \[type=bytes_type'):
        ta.validate_python(123)
    with pytest.raises(ValidationError, match=r'Data should have at most 5 bytes \[type=bytes_too_long,'):
        ta.validate_python(b'1234567')
