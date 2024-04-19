from decimal import Decimal

import pytest

from pydantic import BaseModel, ValidationError

from .conftest import Err


@pytest.fixture(scope='module', name='DecimalModel')
def decimal_model_fixture():
    class DecimalModel(BaseModel):
        v: Decimal

    return DecimalModel


@pytest.mark.parametrize(
    'value,result',
    [
        # Valid inputs
        ('1.234567890123456789012345678901234567890', Decimal(1.234567890123456789012345678901234567890)),
        (Decimal(1.234567890123456789012345678901234567890), Decimal(1.234567890123456789012345678901234567890)),
        ('12345678901234567890123456789012345678.9', Decimal(12345678901234567890123456789012345678.9)),
        (Decimal(12345678901234567890123456789012345678.9), Decimal(12345678901234567890123456789012345678.9)),
        (12345678901234567890123456789012345678, 12345678901234567890123456789012345678),
        (12345678901234567890123456789012345678, Decimal(12345678901234567890123456789012345678)),
        (float('inf'), Err('Input should be a finite number')),
        (float('-inf'), Err('Input should be a finite number')),
        (float('nan'), Err('Input should be a finite number')),
    ],
)
def test_decimal_parsing(DecimalModel, value, result):
    if isinstance(result, Err):
        with pytest.raises(ValidationError, match=result.message_escaped()):
            DecimalModel(v=value)
    else:
        assert DecimalModel(v=value).v == result
