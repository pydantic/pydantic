import re
from decimal import Decimal
from fractions import Fraction

import pytest

from pydantic_core import SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('1/2', Fraction(1, 2)),
        ('0.5', Fraction(1, 2)),
        (1, Fraction(1)),
        (0.5, Fraction(1, 2)),
    ],
)
def test_fraction_basic(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'fraction'})
    assert v.validate_test(input_value) == expected


def test_fraction_instance_input():
    v = SchemaValidator(cs.fraction_schema())
    assert v.validate_python(Fraction(2, 3)) == Fraction(2, 3)


@pytest.mark.parametrize(
    'multiple_of,input_value,error',
    [
        # Non-dyadic float multiples (the precision bug)
        (0.01, '1.00', None),
        (0.01, '10.50', None),
        (0.01, '0.01', None),
        (0.01, '3/100', None),
        (0.01, 1, None),
        (0.01, '1/3', Err('Input should be a multiple of')),
        (0.01, '0.001', Err('Input should be a multiple of')),
        (0.1, '1/2', None),
        (0.1, '3/10', None),
        (0.1, '1', None),
        (0.1, '1/3', Err('Input should be a multiple of')),
        (0.5, '1', None),
        (0.5, '1/2', None),
        (0.5, '1/3', Err('Input should be a multiple of')),
        # Exact Fraction multiples
        (Fraction(1, 100), '1.00', None),
        (Fraction(1, 10), '3/10', None),
        (Fraction(1, 10), '1/3', Err('Input should be a multiple of')),
        (1, '2', None),
        (1, '1/2', Err('Input should be a multiple of')),
    ],
    ids=repr,
)
def test_fraction_multiple_of(multiple_of, input_value, error: Err | None):
    v = SchemaValidator(cs.fraction_schema(multiple_of=multiple_of))
    if error:
        with pytest.raises(
            ValidationError, match=re.escape(error.message) if error.message.startswith('Input') else error.message
        ):
            v.validate_python(input_value)
    else:
        result = v.validate_python(input_value)
        assert isinstance(result, Fraction)
        # value should equal the rational interpretation of the input
        assert result == Fraction(input_value) if not isinstance(input_value, Fraction) else input_value


def test_fraction_multiple_of_float_coercion():
    """Float constraint 0.01 must become Fraction(1, 100), not the binary expansion."""
    v = SchemaValidator(cs.fraction_schema(multiple_of=0.01))
    assert v.validate_python('1') == Fraction(1)
    assert v.validate_python(Fraction(3, 100)) == Fraction(3, 100)


def test_fraction_multiple_of_with_bounds():
    v = SchemaValidator(cs.fraction_schema(multiple_of=0.01, ge=0, le=100))
    assert v.validate_python('10.50') == Fraction('10.50')
    with pytest.raises(ValidationError):
        v.validate_python('-0.01')
    with pytest.raises(ValidationError):
        v.validate_python('1/3')


def test_fraction_multiple_of_json():
    v = SchemaValidator(cs.fraction_schema(multiple_of=0.01))
    assert v.validate_json('"10.50"') == Fraction('10.50')
    assert v.validate_json('1') == Fraction(1)
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"1/3"')
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'multiple_of'


def test_fraction_multiple_of_from_decimal_constraint():
    v = SchemaValidator(cs.fraction_schema(multiple_of=Decimal('0.01')))
    assert v.validate_python('1.00') == Fraction(1)
