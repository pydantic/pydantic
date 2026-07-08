from decimal import Decimal
from fractions import Fraction
from typing import Annotated

import annotated_types
import pytest

from pydantic import Field, TypeAdapter, ValidationError


class FractionSubclass(Fraction):
    pass


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, Fraction(0)),
        (1, Fraction(1)),
        (42, Fraction(42)),
        ('42', Fraction(42)),
        ('42.123', Fraction('42.123')),
        (42.0, Fraction(42)),
        (42.5, Fraction('42.5')),
        (Decimal('1.333'), Fraction('1.333')),
        (1e10, Fraction('1E10')),
        (Fraction('42.0'), Fraction(42)),
        (Fraction('42.5'), Fraction('42.5')),
        (Fraction('1e10'), Fraction('1E10')),
        ('1/3', Fraction(1, 3)),
        ('0/100', Fraction(0)),
        (Fraction('1/3'), Fraction(1, 3)),
        (Fraction('-47e-2'), Fraction(-47, 100)),
        (
            Fraction('123456789123456789123456789.123456789123456789123456789'),
            Fraction('123456789123456789123456789.123456789123456789123456789'),
        ),
        (FractionSubclass('42.0'), Fraction(42)),
        (FractionSubclass('42.5'), Fraction('42.5')),
        (FractionSubclass('1e10'), Fraction('1E10')),
        (True, Fraction(1)),
        (False, Fraction(0)),
    ],
)
def test_fraction(input_value, expected):
    ta = TypeAdapter(Fraction)
    assert ta.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'json_str,expected',
    [
        ('"1/3"', Fraction(1, 3)),
        ('"42.5"', Fraction('42.5')),
        ('"0"', Fraction(0)),
        ('42', Fraction(42)),
        ('42.5', Fraction('42.5')),
        ('"0/100"', Fraction(0)),
        ('"-47e-2"', Fraction(-47, 100)),
    ],
)
def test_fraction_validate_json(json_str, expected):
    ta = TypeAdapter(Fraction)
    assert ta.validate_json(json_str) == expected


@pytest.mark.parametrize(
    'str,expected',
    [
        ('1/3', Fraction(1, 3)),
        ('42.5', Fraction('42.5')),
        ('0', Fraction(0)),
        ('42', Fraction(42)),
        ('42.5', Fraction('42.5')),
        ('0/100', Fraction(0)),
        ('-47e-2', Fraction(-47, 100)),
    ],
)
def test_fraction_validate_strings(str, expected):
    ta = TypeAdapter(Fraction)
    assert ta.validate_strings(str) == expected


@pytest.mark.parametrize(
    'json_str,error',
    [
        ('"not a number"', ValidationError),
        ('"1/0"', ValidationError),
        (float('inf'), ValidationError),
        (float('nan'), ValidationError),
    ],
)
def test_fraction_validate_json_error(json_str, error):
    ta = TypeAdapter(Fraction)
    with pytest.raises(error):
        ta.validate_json(json_str)


@pytest.mark.parametrize(
    'input_value',
    [
        (0),
        (True),
        (False),
        ('not a number'),
        ('1/0'),
        ('1/3'),
        (1.333),
        (Decimal('1.333')),
        (float('inf')),
        (float('nan')),
    ],
)
def test_fraction_validation_error_strict(input_value):
    with pytest.raises(ValidationError):
        ta = TypeAdapter(Fraction)
        ta.validate_python(input_value, strict=True)


@pytest.mark.parametrize(
    'input_value',
    [
        Fraction(1, 3),
        Fraction(0),
        Fraction('42.5'),
        FractionSubclass('1/7'),
    ],
)
def test_fraction_strict_accepts_fraction(input_value):
    ta = TypeAdapter(Fraction)
    assert ta.validate_python(input_value, strict=True) == input_value


@pytest.mark.parametrize(
    ['input', 'error_type'],
    [
        ('wrong_format', 'fraction_parsing'),  # Raises `ValueError` internally
        ('1/0', 'fraction_parsing'),  # Raises `ZeroDivisionError` internally
        (float('inf'), 'fraction_parsing'),  # Raises `OverflowError` internally
        (float('nan'), 'fraction_parsing'),  # Raises `ValueError` internally
        (type, 'fraction_type'),  # Raises `TypeError` internally
    ],
)
def test_fraction_validation_error(input: object, error_type: str):

    ta = TypeAdapter(Fraction)

    with pytest.raises(ValidationError, check=lambda e: e.errors()[0]['type'] == error_type):
        ta.validate_python(input)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (Fraction(0), '0'),
        (Fraction(1), '1'),
        (Fraction(1, 3), '1/3'),
        (Fraction(-1, 2), '-1/2'),
        (Fraction('42.5'), '85/2'),
        (Fraction('123456789/1000000'), '123456789/1000000'),
    ],
)
def test_fraction_dump_python(input_value, expected):
    ta = TypeAdapter(Fraction)
    assert ta.dump_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (Fraction(0), b'"0"'),
        (Fraction(1), b'"1"'),
        (Fraction(1, 3), b'"1/3"'),
        (Fraction(-1, 2), b'"-1/2"'),
        (Fraction('42.5'), b'"85/2"'),
        (Fraction('123456789/1000000'), b'"123456789/1000000"'),
    ],
)
def test_fraction_dump_json(input_value, expected):
    ta = TypeAdapter(Fraction)
    assert ta.dump_json(input_value) == expected


@pytest.mark.parametrize(
    'constraint,input_value,expected',
    [
        (annotated_types.Gt(0), '1/3', Fraction(1, 3)),
        (annotated_types.Ge(0), 0, Fraction(0)),
        (annotated_types.Ge(0), '1/3', Fraction(1, 3)),
        (annotated_types.Lt(1), '1/3', Fraction(1, 3)),
        (annotated_types.Le(1), 1, Fraction(1)),
        (annotated_types.Le(1), '1/3', Fraction(1, 3)),
        # float bound
        (annotated_types.Gt(0.5), 1, Fraction(1)),
    ],
)
def test_fraction_constraints(constraint, input_value, expected):
    ta = TypeAdapter(Annotated[Fraction, constraint])
    assert ta.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'constraint,input_value',
    [
        (annotated_types.Gt(0), 0),
        (annotated_types.Gt(0), -1),
        (annotated_types.Ge(0), -1),
        (annotated_types.Lt(1), 1),
        (annotated_types.Lt(1), 2),
        (annotated_types.Le(1), 2),
        # float bound
        (annotated_types.Gt(0.5), '1/3'),
    ],
)
def test_fraction_constraints_error(constraint, input_value):
    ta = TypeAdapter(Annotated[Fraction, constraint])
    with pytest.raises(ValidationError):
        ta.validate_python(input_value)


def test_fraction_json_schema():
    ta = TypeAdapter(Fraction)
    assert ta.json_schema(mode='serialization') == {'type': 'string', 'format': 'fraction'}

    ta = TypeAdapter(Annotated[Fraction, Field(ge=Fraction(1))])

    assert ta.json_schema() == {'anyOf': [{'minimum': 1.0, 'type': 'number'}, {'format': 'fraction', 'type': 'string'}]}


@pytest.mark.parametrize(
    'multiple_of,input_value,expected',
    [
        # Float multiples that are not dyadic rationals — previously broken because
        # multiple_of fell through to Python `x % float` with float precision noise.
        (0.01, '1.00', Fraction(1)),
        (0.01, '10.50', Fraction('10.50')),
        (0.01, '0.01', Fraction(1, 100)),
        (0.01, '3/100', Fraction(3, 100)),
        (0.01, 1, Fraction(1)),
        (0.01, Fraction(1), Fraction(1)),
        (0.1, '1/2', Fraction(1, 2)),
        (0.1, '3/10', Fraction(3, 10)),
        (0.1, '1', Fraction(1)),
        (0.5, '1', Fraction(1)),
        (0.5, '1/2', Fraction(1, 2)),
        # Exact Fraction / int multiples
        (Fraction(1, 100), '1.00', Fraction(1)),
        (Fraction(1, 100), '10.50', Fraction('10.50')),
        (Fraction(1, 10), '3/10', Fraction(3, 10)),
        (1, '2', Fraction(2)),
        (1.0, '2', Fraction(2)),
        # annotated_types form
        (annotated_types.MultipleOf(0.01), '1.00', Fraction(1)),
        (annotated_types.MultipleOf(Fraction(1, 10)), '3/10', Fraction(3, 10)),
    ],
)
def test_fraction_multiple_of(multiple_of, input_value, expected):
    if isinstance(multiple_of, annotated_types.MultipleOf):
        ta = TypeAdapter(Annotated[Fraction, multiple_of])
    else:
        ta = TypeAdapter(Annotated[Fraction, Field(multiple_of=multiple_of)])
    assert ta.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'multiple_of,input_value',
    [
        (0.01, '1/3'),
        (0.01, '0.001'),
        (0.1, '1/3'),
        (Fraction(1, 10), '1/3'),
        (Fraction(1, 100), '1/1000'),
        (1, '1/2'),
        (annotated_types.MultipleOf(0.01), '1/3'),
    ],
)
def test_fraction_multiple_of_error(multiple_of, input_value):
    if isinstance(multiple_of, annotated_types.MultipleOf):
        ta = TypeAdapter(Annotated[Fraction, multiple_of])
    else:
        ta = TypeAdapter(Annotated[Fraction, Field(multiple_of=multiple_of)])
    with pytest.raises(ValidationError, check=lambda e: e.errors()[0]['type'] == 'multiple_of'):
        ta.validate_python(input_value)


def test_fraction_multiple_of_with_field_and_ge():
    """Money-style constraint: non-negative cents precision."""
    ta = TypeAdapter(Annotated[Fraction, Field(multiple_of=0.01, ge=0)])
    assert ta.validate_python('10.50') == Fraction('10.50')
    with pytest.raises(ValidationError):
        ta.validate_python('-0.01')
    with pytest.raises(ValidationError):
        ta.validate_python('1/3')


def test_fraction_multiple_of_json():
    ta = TypeAdapter(Annotated[Fraction, Field(multiple_of=0.01)])
    assert ta.validate_json('"10.50"') == Fraction('10.50')
    assert ta.validate_json('1') == Fraction(1)
    with pytest.raises(ValidationError, check=lambda e: e.errors()[0]['type'] == 'multiple_of'):
        ta.validate_json('"1/3"')
