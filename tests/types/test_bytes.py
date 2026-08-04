from typing import Annotated

import annotated_types
import pytest

from pydantic import BaseModel, Field, Strict, StrictBytes, ValidationError


class ConBytesModel(BaseModel):
    v: Annotated[bytes, annotated_types.Len(0, 10)] = b'foobar'


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
    class Model(BaseModel):
        v: bytes

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_constrained_bytes_good():
    m = ConBytesModel(v=b'short')
    assert m.v == b'short'


def test_constrained_bytes_default():
    m = ConBytesModel()
    assert m.v == b'foobar'


@pytest.mark.parametrize(
    ('data', 'valid'),
    [(b'this is too long', False), ('⪶⓲⽷01'.encode(), False), (b'not long90', True), ('⪶⓲⽷0'.encode(), True)],
)
def test_constrained_bytes_too_long(data: bytes, valid: bool):
    if valid:
        assert ConBytesModel(v=data).model_dump() == {'v': data}
    else:
        with pytest.raises(ValidationError) as exc_info:
            ConBytesModel(v=data)
        # insert_assert(exc_info.value.errors(include_url=False))
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'max_length': 10},
                'input': data,
                'loc': ('v',),
                'msg': 'Data should have at most 10 bytes',
                'type': 'bytes_too_long',
            }
        ]


def test_constrained_bytes_strict_true():
    class Model(BaseModel):
        v: Annotated[bytes, Strict()]

    assert Model(v=b'foobar').v == b'foobar'
    with pytest.raises(ValidationError):
        Model(v=bytearray('foobar', 'utf-8'))

    with pytest.raises(ValidationError):
        Model(v='foostring')

    with pytest.raises(ValidationError):
        Model(v=42)

    with pytest.raises(ValidationError):
        Model(v=0.42)


def test_constrained_bytes_strict_false():
    class Model(BaseModel):
        v: Annotated[bytes, Strict(False)]

    assert Model(v=b'foobar').v == b'foobar'
    assert Model(v=bytearray('foobar', 'utf-8')).v == b'foobar'
    assert Model(v='foostring').v == b'foostring'

    with pytest.raises(ValidationError):
        Model(v=42)

    with pytest.raises(ValidationError):
        Model(v=0.42)


def test_constrained_bytes_strict_default():
    class Model(BaseModel):
        v: bytes

    assert Model(v=b'foobar').v == b'foobar'
    assert Model(v=bytearray('foobar', 'utf-8')).v == b'foobar'
    assert Model(v='foostring').v == b'foostring'

    with pytest.raises(ValidationError):
        Model(v=42)

    with pytest.raises(ValidationError):
        Model(v=0.42)


def test_strict_bytes():
    class Model(BaseModel):
        v: StrictBytes

    assert Model(v=b'foobar').v == b'foobar'
    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v=bytearray('foobar', 'utf-8'))

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v='foostring')

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v=42)

    with pytest.raises(ValidationError, match='Input should be a valid bytes'):
        Model(v=0.42)


def test_strict_bytes_max_length():
    class Model(BaseModel):
        u: StrictBytes = Field(max_length=5)

    assert Model(u=b'foo').u == b'foo'

    with pytest.raises(ValidationError, match=r'Input should be a valid bytes \[type=bytes_type'):
        Model(u=123)
    with pytest.raises(ValidationError, match=r'Data should have at most 5 bytes \[type=bytes_too_long,'):
        Model(u=b'1234567')
