from collections import namedtuple
from typing import Any

import pytest

from pydantic import BaseModel, ValidationError
from pydantic.errors import InvalidLengthForBrand, LuhnValidationError, NotDigitError
from pydantic.types import PaymentCardBrand, PaymentCardNumber

VALID_AMEX = '370000000000002'
VALID_MC = '5100000000000003'
VALID_VISA_13 = '4050000000001'
VALID_VISA_16 = '4050000000000001'
VALID_VISA_19 = '4050000000000000001'
VALID_OTHER = '2000000000000000008'
LUHN_INVALID = '4000000000000000'
LEN_INVALID = '40000000000000006'


# Mock PaymentCardNumber
PCN = namedtuple('PaymentCardNumber', ['card_number', 'brand'])
PCN.__len__ = lambda v: len(v.card_number)


class PaymentCard(BaseModel):
    card_number: PaymentCardNumber


def test_validate_digits():
    digits = '12345'
    assert PaymentCardNumber.validate_digits(digits) == digits
    with pytest.raises(NotDigitError):
        PaymentCardNumber.validate_digits('hello')


@pytest.mark.parametrize(
    'card_number, valid',
    [
        ('0', True),
        ('00', True),
        ('18', True),
        ('0000000000000000', True),
        ('4242424242424240', False),
        ('4242424242424241', False),
        ('4242424242424242', True),
        ('4242424242424243', False),
        ('4242424242424244', False),
        ('4242424242424245', False),
        ('4242424242424246', False),
        ('4242424242424247', False),
        ('4242424242424248', False),
        ('4242424242424249', False),
        ('42424242424242426', True),
        ('424242424242424267', True),
        ('4242424242424242675', True),
        ('5164581347216566', True),
        ('4345351087414150', True),
        ('343728738009846', True),
        ('5164581347216567', False),
        ('4345351087414151', False),
        ('343728738009847', False),
        ('000000018', True),
        ('99999999999999999999', True),
        ('99999999999999999999999999999999999999999999999999999999999999999997', True),
    ],
)
def test_validate_luhn_check_digit(card_number: str, valid: bool):
    if valid:
        assert PaymentCardNumber.validate_luhn_check_digit(card_number) == card_number
    else:
        with pytest.raises(LuhnValidationError):
            PaymentCardNumber.validate_luhn_check_digit(card_number)


@pytest.mark.parametrize(
    'card_number, brand, valid',
    [
        (VALID_VISA_13, PaymentCardBrand.visa, True),
        (VALID_VISA_16, PaymentCardBrand.visa, True),
        (VALID_VISA_19, PaymentCardBrand.visa, True),
        (VALID_MC, PaymentCardBrand.mastercard, True),
        (VALID_AMEX, PaymentCardBrand.amex, True),
        (VALID_OTHER, PaymentCardBrand.other, True),
        (LEN_INVALID, PaymentCardBrand.visa, False),
        (VALID_AMEX, PaymentCardBrand.mastercard, False),
    ],
)
def test_length_for_brand(card_number: str, brand: PaymentCardBrand, valid: bool):
    pcn = PCN(card_number, brand)
    if valid:
        assert PaymentCardNumber.validate_length_for_brand(pcn) == pcn
    else:
        with pytest.raises(InvalidLengthForBrand):
            PaymentCardNumber.validate_length_for_brand(pcn)


@pytest.mark.parametrize(
    'card_number, brand',
    [
        (VALID_AMEX, PaymentCardBrand.amex),
        (VALID_MC, PaymentCardBrand.mastercard),
        (VALID_VISA_16, PaymentCardBrand.visa),
        (VALID_OTHER, PaymentCardBrand.other),
    ],
)
def test_get_brand(card_number: str, brand: PaymentCardBrand):
    assert PaymentCardNumber._get_brand(card_number) == brand


def test_valid():
    card = PaymentCard(card_number=VALID_VISA_16)
    assert str(card.card_number) == VALID_VISA_16
    assert card.card_number.masked == '405000******0001'


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
    with pytest.raises(ValidationError, match=error_message) as exc_info:
        PaymentCard(card_number=card_number)
    assert exc_info.value.json().startswith('[')


def test_payment_card_brand():
    b = PaymentCardBrand.visa
    assert str(b) == 'Visa'
    assert b is PaymentCardBrand.visa
    assert b == PaymentCardBrand.visa
    assert b in {PaymentCardBrand.visa, PaymentCardBrand.mastercard}

    b = 'Visa'
    assert b is not PaymentCardBrand.visa
    assert b == PaymentCardBrand.visa
    assert b in {PaymentCardBrand.visa, PaymentCardBrand.mastercard}

    b = PaymentCardBrand.amex
    assert b is not PaymentCardBrand.visa
    assert b != PaymentCardBrand.visa
    assert b not in {PaymentCardBrand.visa, PaymentCardBrand.mastercard}
