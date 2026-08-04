from decimal import Decimal

import pytest

from pydantic import BaseModel, StrictBool, ValidationError


class BoolCastable:
    def __bool__(self) -> bool:
        return True


@pytest.mark.parametrize(
    'value,expected',
    [
        pytest.param(True, True, id='True_bool'),
        pytest.param(1, True, id='1_int'),
        pytest.param(1.0, True, id='1.0_float'),
        (Decimal(1), True),
        ('y', True),
        ('Y', True),
        ('yes', True),
        ('Yes', True),
        ('YES', True),
        ('true', True),
        pytest.param('True', True, id='True_str'),
        pytest.param('TRUE', True, id='TRUE_str'),
        ('on', True),
        ('On', True),
        ('ON', True),
        pytest.param('1', True, id='1_str'),
        ('t', True),
        ('T', True),
        pytest.param(b'TRUE', True, id='TRUE_bytes'),
        pytest.param(False, False, id='False_bool'),
        pytest.param(0, False, id='0_int'),
        pytest.param(0.0, False, id='0.0_float'),
        (Decimal(0), False),
        ('n', False),
        ('N', False),
        ('no', False),
        ('No', False),
        ('NO', False),
        ('false', False),
        pytest.param('False', False, id='False_str'),
        pytest.param('FALSE', False, id='FALSE_str'),
        ('off', False),
        ('Off', False),
        ('OFF', False),
        pytest.param('0', False, id='0_str'),
        ('f', False),
        ('F', False),
        pytest.param(b'FALSE', False, id='FALSE_bytes'),
        (None, ValidationError),
        ('', ValidationError),
        ([], ValidationError),
        ({}, ValidationError),
        ([1, 2, 3, 4], ValidationError),
        ({1: 2, 3: 4}, ValidationError),
        pytest.param(b'2', ValidationError, id='2_bytes'),
        pytest.param('2', ValidationError, id='2_str'),
        pytest.param(2, ValidationError, id='2_int'),
        (2.0, ValidationError),
        (Decimal(2), ValidationError),
        (b'\x81', ValidationError),
        (BoolCastable(), ValidationError),
    ],
)
def test_bool_validation(value, expected):
    class Model(BaseModel):
        v: bool

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v is expected


def test_strict_bool():
    class Model(BaseModel):
        v: StrictBool

    assert Model(v=True).v is True
    assert Model(v=False).v is False

    with pytest.raises(ValidationError):
        Model(v=1)

    with pytest.raises(ValidationError):
        Model(v='1')

    with pytest.raises(ValidationError):
        Model(v=b'1')


def test_bool_unhashable_fails():
    class Model(BaseModel):
        v: bool

    with pytest.raises(ValidationError) as exc_info:
        Model(v={})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'bool_type', 'loc': ('v',), 'msg': 'Input should be a valid boolean', 'input': {}}
    ]
