from collections import namedtuple
from typing import Any

import pytest

from pydantic import BaseModel, ValidationError
from pydantic.errors import InvalidLengthForBrand, LuhnValidationError, NotDigitError
from pydantic.types import PaymentCardBrand, PaymentCardNumber

VALID_AMEX = '370000000000002'
VALID_MC = '5100000000000003'
VALID_VISA = '4000000000000002'
VALID_OTHER = '2000000000000000008'
LUHN_INVALID = '4000000000000000'
LEN_INVALID = '40000000000000006'

# Mock PaymentCardNumber to let us test just this one method
PCN = namedtuple('PaymentCardNumber', ['card_number', 'brand'])
PCN.__len__ = lambda v: len(v.card_number)


class PaymentCard(BaseModel):
    card_number: PaymentCardNumber


def test_validate_digits():
    digits = '12345'
    assert PaymentCardNumber.validate_digits(digits) == digits
    with pytest.raises(NotDigitError):
        PaymentCardNumber.validate_digits('hello')


def test_validate_luhn_check_digit():
    assert PaymentCardNumber.validate_luhn_check_digit(VALID_VISA) == VALID_VISA
    with pytest.raises(LuhnValidationError):
        PaymentCardNumber.validate_luhn_check_digit(LUHN_INVALID)


@pytest.mark.parametrize(
    'card_number, brand, exception',
    [
        (VALID_VISA, PaymentCardBrand.visa, False),
        (VALID_MC, PaymentCardBrand.mastercard, False),
        (VALID_AMEX, PaymentCardBrand.amex, False),
        (VALID_OTHER, PaymentCardBrand.other, False),
        (LEN_INVALID, PaymentCardBrand.visa, True),
    ],
)
def test_length_for_brand(card_number: str, brand: PaymentCardBrand, exception: bool):
    pcn = PCN(card_number, brand)
    if exception:
        with pytest.raises(InvalidLengthForBrand):
            PaymentCardNumber.validate_length_for_brand(pcn)
    else:
        assert PaymentCardNumber.validate_length_for_brand(pcn) == pcn


@pytest.mark.parametrize(
    'card_number, brand',
    [
        (VALID_AMEX, PaymentCardBrand.amex),
        (VALID_MC, PaymentCardBrand.mastercard),
        (VALID_VISA, PaymentCardBrand.visa),
        (VALID_OTHER, PaymentCardBrand.other),
    ],
)
def test_get_brand(card_number: str, brand: PaymentCardBrand):
    assert PaymentCardNumber._get_brand(card_number) == brand


def test_valid():
    card = PaymentCard(card_number=VALID_VISA)
    assert str(card.card_number) == VALID_VISA
    assert card.card_number.masked == '400000******0002'


@pytest.mark.parametrize(
    'card_number, error_message',
    [
        (None, 'type_error.none.not_allowed'),
        ('1' * 11, 'value_error.any_str.min_length'),
        ('1' * 20, 'value_error.any_str.max_length'),
        ('h' * 16, 'value_error.payment_card_number.digits'),
        (LUHN_INVALID, 'value_error.payment_card_number.luhn_check'),
        (LEN_INVALID, 'value_error.payment_card_number.invalid_length_for_brand'),
    ],
)
def test_error_types(card_number: Any, error_message: str):
    with pytest.raises(ValidationError, match=error_message):
        PaymentCard(card_number=card_number)
