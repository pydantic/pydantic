from decimal import Decimal

import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_decimal():
    v = SchemaSerializer(core_schema.decimal_schema())
    assert v.to_python(Decimal('123.456')) == Decimal('123.456')

    assert v.to_python(Decimal('123.456'), mode='json') == '123.456'
    assert v.to_json(Decimal('123.456')) == b'"123.456"'

    assert v.to_python(Decimal('123456789123456789123456789.123456789123456789123456789')) == Decimal(
        '123456789123456789123456789.123456789123456789123456789'
    )
    assert (
        v.to_json(Decimal('123456789123456789123456789.123456789123456789123456789'))
        == b'"123456789123456789123456789.123456789123456789123456789"'
    )

    with pytest.warns(UserWarning, match='Expected `decimal` but got `int` - serialized value may not be as expected'):
        assert v.to_python(123, mode='json') == 123

    with pytest.warns(UserWarning, match='Expected `decimal` but got `int` - serialized value may not be as expected'):
        assert v.to_json(123) == b'123'


def test_decimal_key():
    v = SchemaSerializer(core_schema.dict_schema(core_schema.decimal_schema(), core_schema.decimal_schema()))
    assert v.to_python({Decimal('123.456'): Decimal('123.456')}) == {Decimal('123.456'): Decimal('123.456')}
    assert v.to_python({Decimal('123.456'): Decimal('123.456')}, mode='json') == {'123.456': '123.456'}
    assert v.to_json({Decimal('123.456'): Decimal('123.456')}) == b'{"123.456":"123.456"}'


@pytest.mark.parametrize(
    'value,expected',
    [
        (Decimal('123.456'), '123.456'),
        (Decimal('Infinity'), 'Infinity'),
        (Decimal('-Infinity'), '-Infinity'),
        (Decimal('NaN'), 'NaN'),
    ],
)
def test_decimal_json(value, expected):
    v = SchemaSerializer(core_schema.decimal_schema())
    assert v.to_python(value, mode='json') == expected
    assert v.to_json(value).decode() == f'"{expected}"'


def test_any_decimal_key():
    v = SchemaSerializer(core_schema.dict_schema())
    input_value = {Decimal('123.456'): 1}

    assert v.to_python(input_value, mode='json') == {'123.456': 1}
    assert v.to_json(input_value) == b'{"123.456":1}'
