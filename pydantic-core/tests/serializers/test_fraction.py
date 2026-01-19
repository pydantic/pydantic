from fractions import Fraction

import pytest

from pydantic_core import SchemaSerializer, core_schema

import sys


# skip if python is lower than 3.12
@pytest.mark.skipif(sys.version_info < (3, 12), reason="Fraction string parsing is only available in Python 3.12+")
def test_fraction_string():
    v = SchemaSerializer(core_schema.fraction_schema())
    assert v.to_python(Fraction('3 / 4')) == Fraction(3, 4)


def test_fraction():
    v = SchemaSerializer(core_schema.fraction_schema())
    assert v.to_python(Fraction(3, 4)) == Fraction(3, 4)

    # check correct casting to int when denominator is 1
    assert v.to_python(Fraction(10, 10), mode='json') == '1'
    assert v.to_python(Fraction(1, 10), mode='json') == '1/10'

    assert v.to_json(Fraction(3, 4)) == b'"3/4"'


def test_fraction_key():
    v = SchemaSerializer(core_schema.dict_schema(core_schema.fraction_schema(), core_schema.fraction_schema()))
    assert v.to_python({Fraction(3, 4): Fraction(1, 10)}) == {Fraction(3, 4): Fraction(1, 10)}
    assert v.to_python({Fraction(3, 4): Fraction(1, 10)}, mode='json') == {'3/4': '1/10'}
    assert v.to_json({Fraction(3, 4): Fraction(1, 10)}) == b'{"3/4":"1/10"}'


@pytest.mark.parametrize(
    'value,expected',
    [
        (Fraction(3, 4), '3/4'),
        (Fraction(1, 10), '1/10'),
        (Fraction(10, 1), '10'),
        (Fraction(-5, 2), '-5/2'),
    ],
)
def test_fraction_json(value, expected):
    v = SchemaSerializer(core_schema.fraction_schema())
    assert v.to_python(value, mode='json') == expected
    assert v.to_json(value).decode() == f'"{expected}"'


def test_any_fraction_key():
    v = SchemaSerializer(core_schema.dict_schema())
    input_value = {Fraction(3, 4): 1}

    assert v.to_python(input_value, mode='json') == {'3/4': 1}
    assert v.to_json(input_value) == b'{"3/4":1}'
