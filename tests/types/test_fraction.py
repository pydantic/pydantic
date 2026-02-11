from fractions import Fraction
from typing import Annotated

import annotated_types
import pytest

import numpy as np

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError


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
    class Model(BaseModel):
        v: Fraction

    m = Model(v=input_value)
    assert m.v == expected

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
    'json_str,error',
    [
        ('"not a number"', ValidationError),
        ('"1/0"', ZeroDivisionError),
        (np.inf, ValidationError),
        (np.nan, ValidationError),
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
        (np.inf),
        (np.nan),
    ],
)
def test_fraction_validation_error_strict(input_value):
    class Model(BaseModel):
        v: Fraction

        model_config = ConfigDict(strict=True)

    with pytest.raises(ValidationError):
        Model(v=input_value)

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
    'input_value,error',
    [
        ('not a number', ValidationError),
        ('1/0', ZeroDivisionError),
        (np.inf, OverflowError),
        (np.nan, ValidationError),
        ([1, 2], TypeError),
        ({}, TypeError),
        (None, TypeError),
    ],
)
def test_fraction_validation_error_non_strict(input_value, error):
    with pytest.raises(error):
        ta = TypeAdapter(Fraction)
        ta.validate_python(input_value, strict=False)


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
    assert ta.json_schema() == {'type': 'string', 'format': 'fraction'}
