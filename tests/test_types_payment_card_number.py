from collections import namedtuple
from typing import Any

import pytest

from pydantic import BaseModel, ValidationError
from pydantic.types import PaymentCardBrand, PaymentCardNumber

VALID_AMEX = '370000000000002'
VALID_MC = '5100000000000003'
VALID_VISA = '4000000000000002'
VALID_OTHER = '2000000000000000008'
LUHN_INVALID = '4000000000000000'
LEN_INVALID = '40000000000000006'


class PaymentCard(BaseModel):
    card_number: PaymentCardNumber


def test_validate_digits():
    digits = '12345'
    assert PaymentCardNumber.validate_digits(digits) == digits
    with pytest.raises(ValueError):
        PaymentCardNumber.validate_digits('hello')


def test_validate_luhn_check_digit():
    assert PaymentCardNumber.validate_luhn_check_digit(VALID_VISA) == VALID_VISA
    with pytest.raises(ValueError):
        PaymentCardNumber.validate_luhn_check_digit(LUHN_INVALID)


def test_length_for_brand():
    # Mock PaymentCardNumber to let us test just this one method
    PCN = namedtuple('PaymentCardNumber', ['card_number', 'brand'])
    PCN.__len__ = lambda v: len(v.card_number)

    pcn = PCN(VALID_VISA, PaymentCardBrand.visa)
    assert PaymentCardNumber.validate_length_for_brand(pcn) == pcn

    pcn = PCN(VALID_MC, PaymentCardBrand.mastercard)
    assert PaymentCardNumber.validate_length_for_brand(pcn) == pcn

    pcn = PCN(VALID_AMEX, PaymentCardBrand.amex)
    assert PaymentCardNumber.validate_length_for_brand(pcn) == pcn

    pcn = PCN(VALID_OTHER, PaymentCardBrand.other)
    assert PaymentCardNumber.validate_length_for_brand(pcn) == pcn

    pcn = PCN(LEN_INVALID, PaymentCardBrand.visa)
    with pytest.raises(ValueError):
        PaymentCardNumber.validate_length_for_brand(pcn)


def test_get_brand():
    assert PaymentCardNumber.get_brand(VALID_AMEX) == PaymentCardBrand.amex
    assert PaymentCardNumber.get_brand(VALID_MC) == PaymentCardBrand.mastercard
    assert PaymentCardNumber.get_brand(VALID_VISA) == PaymentCardBrand.visa
    assert PaymentCardNumber.get_brand(VALID_OTHER) == PaymentCardBrand.other


def test_valid():
    card = PaymentCard(card_number=VALID_VISA)
    assert str(card.card_number) == VALID_VISA
    assert card.card_number.masked == '400000******0002'


def get_error_type(card_number: Any):
    with pytest.raises(ValidationError) as exc_info:
        PaymentCard(card_number=card_number)
    return exc_info.value.errors()[0]['type']


def test_error_types():
    assert get_error_type(None) == 'type_error.none.not_allowed'
    assert get_error_type('1' * 11) == 'value_error.any_str.min_length'
    assert get_error_type('1' * 20) == 'value_error.any_str.max_length'
    assert get_error_type('h' * 16) == 'value_error.payment_card_number.digits'
    assert get_error_type(LUHN_INVALID) == 'value_error.payment_card_number.luhn_check'
    assert get_error_type(LEN_INVALID) == 'value_error.payment_card_number.invalid_length_for_brand'
