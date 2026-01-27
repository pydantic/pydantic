from __future__ import annotations

import json
import re
from fractions import Fraction
from typing import Any

import pytest
from dirty_equals import IsStr

from pydantic_core import SchemaError, SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson, plain_repr


class FractionSubclass(Fraction):
    pass


@pytest.mark.parametrize(
    'constraint',
    ['le', 'lt', 'ge', 'gt'],
)
def test_constraints_schema_validation_error(constraint: str) -> None:
    with pytest.raises(SchemaError, match=f"'{constraint}' must be coercible to a Fraction instance"):
        SchemaValidator(cs.fraction_schema(**{constraint: 'bad_value'}))


def test_constraints_schema_validation() -> None:
    val = SchemaValidator(cs.fraction_schema(gt='1'))
    with pytest.raises(ValidationError):
        val.validate_python('0')


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
        (
            Fraction('123456789123456789123456789.123456789123456789123456789'),
            Fraction('123456789123456789123456789.123456789123456789123456789'),
        ),
        (FractionSubclass('42.0'), Fraction(42)),
        (FractionSubclass('42.5'), Fraction('42.5')),
        (FractionSubclass('1e10'), Fraction('1E10')),
        (
            True,
            Err(
                'Fraction input should be an integer, float, string or Fraction object [type=fraction_type, input_value=True, input_type=bool]'
            ),
        ),
        (
            False,
            Err(
                'Fraction input should be an integer, float, string or Fraction object [type=fraction_type, input_value=False, input_type=bool]'
            ),
        ),
        ('wrong', Err('Input should be a valid fraction [type=fraction_parsing')),
        (
            [1, 2],
            Err(
                'Fraction input should be an integer, float, string or Fraction object [type=fraction_type, input_value=[1, 2], input_type=list]'
            ),
        ),
    ],
)
def test_fraction(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'fraction'})
    # Fraction types are not JSON serializable
    if v.validator_type == 'json' and isinstance(input_value, Fraction):
        input_value = str(input_value)
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, Fraction)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (Fraction(0), Fraction(0)),
        (Fraction(1), Fraction(1)),
        (Fraction(42), Fraction(42)),
        (Fraction('42.0'), Fraction('42.0')),
        (Fraction('42.5'), Fraction('42.5')),
        (
            42.0,
            Err('Input should be an instance of Fraction [type=is_instance_of, input_value=42.0, input_type=float]'),
        ),
        ('42', Err("Input should be an instance of Fraction [type=is_instance_of, input_value='42', input_type=str]")),
        (42, Err('Input should be an instance of Fraction [type=is_instance_of, input_value=42, input_type=int]')),
        (True, Err('Input should be an instance of Fraction [type=is_instance_of, input_value=True, input_type=bool]')),
    ],
    ids=repr,
)
def test_fraction_strict_py(input_value, expected):
    v = SchemaValidator(cs.fraction_schema(strict=True))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, Fraction)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (0, Fraction(0)),
        (1, Fraction(1)),
        (42, Fraction(42)),
        ('42.0', Fraction('42.0')),
        ('42.5', Fraction('42.5')),
        (42.0, Fraction('42.0')),
        ('42', Fraction('42')),
        (
            True,
            Err(
                'Fraction input should be an integer, float, string or Fraction object [type=fraction_type, input_value=True, input_type=bool]'
            ),
        ),
    ],
    ids=repr,
)
def test_fraction_strict_json(input_value, expected):
    v = SchemaValidator(cs.fraction_schema(strict=True))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_json(json.dumps(input_value))
    else:
        output = v.validate_json(json.dumps(input_value))
        assert output == expected
        assert isinstance(output, Fraction)


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, 0, Fraction(0)),
        ({}, '123.456', Fraction('123.456')),
        ({'ge': 0}, 0, Fraction(0)),
        (
            {'ge': 0},
            -0.1,
            Err(
                'Input should be greater than or equal to 0 '
                '[type=greater_than_equal, input_value=-0.1, input_type=float]'
            ),
        ),
        ({'gt': 0}, 0.1, Fraction('0.1')),
        ({'gt': 0}, 0, Err('Input should be greater than 0 [type=greater_than, input_value=0, input_type=int]')),
        ({'le': 0}, 0, Fraction(0)),
        ({'le': 0}, -1, Fraction(-1)),
        ({'le': 0}, 0.1, Err('Input should be less than or equal to 0')),
        ({'lt': 0}, 0, Err('Input should be less than 0')),
        ({'lt': 0.123456}, 1, Err('Input should be less than 1929/15625')),
        ({'lt': 0.123456}, '0.1', Fraction('0.1')),
    ],
)
def test_fraction_kwargs(py_and_json: PyAndJson, kwargs: dict[str, Any], input_value, expected):
    v = py_and_json({'type': 'fraction', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert isinstance(output, Fraction)


def test_union_fraction_py():
    v = SchemaValidator(cs.union_schema(choices=[cs.fraction_schema(strict=True), cs.fraction_schema(gt=0)]))
    assert v.validate_python('14') == 14
    assert v.validate_python(Fraction(5)) == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('-5')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': ('fraction',),
            'msg': 'Input should be an instance of Fraction',
            'input': '-5',
            'ctx': {'class': 'Fraction'},
        },
        {
            'type': 'greater_than',
            'loc': ('fraction',),
            'msg': 'Input should be greater than 0',
            'input': '-5',
            'ctx': {'gt': Fraction(0)},
        },
    ]


def test_union_fraction_json():
    v = SchemaValidator(cs.union_schema(choices=[cs.fraction_schema(strict=True), cs.fraction_schema(gt=0)]))
    assert v.validate_json(json.dumps('14')) == 14
    assert v.validate_json(json.dumps('5')) == 5


def test_union_fraction_simple(py_and_json: PyAndJson):
    v = py_and_json({'type': 'union', 'choices': [{'type': 'fraction'}, {'type': 'list'}]})
    assert v.validate_test('5') == 5
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('xxx')

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'fraction_parsing', 'loc': ('fraction',), 'msg': 'Input should be a valid fraction', 'input': 'xxx'},
        {
            'type': 'list_type',
            'loc': ('list[any]',),
            'msg': IsStr(regex='Input should be a valid (list|array)'),
            'input': 'xxx',
        },
    ]


def test_fraction_repr():
    v = SchemaValidator(cs.fraction_schema())
    assert plain_repr(v).startswith(
        'SchemaValidator(title="fraction",validator=Fraction(FractionValidator{strict:false'
    )
    v = SchemaValidator(cs.fraction_schema(strict=True))
    assert plain_repr(v).startswith('SchemaValidator(title="fraction",validator=Fraction(FractionValidator{strict:true')


@pytest.mark.parametrize(
    'input_value,expected', [(Fraction('1.23'), Fraction('1.23')), (Fraction('1'), Fraction('1.0'))]
)
def test_fraction_not_json(input_value, expected):
    v = SchemaValidator(cs.fraction_schema())
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, Fraction)


def test_fraction_key(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'fraction'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'1': 1, '2': 2}) == {Fraction('1'): 1, Fraction('2'): 2}
    assert v.validate_test({'1.5': 1, '2.4': 2}) == {Fraction('1.5'): 1, Fraction('2.4'): 2}
    if v.validator_type == 'python':
        with pytest.raises(ValidationError, match='Input should be an instance of Fraction'):
            v.validate_test({'1.5': 1, '2.5': 2}, strict=True)
    else:
        assert v.validate_test({'1.5': 1, '2.4': 2}, strict=True) == {Fraction('1.5'): 1, Fraction('2.4'): 2}


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('NaN', Err("Input should be a valid fraction [type=fraction_parsing, input_value='NaN', input_type=str]")),
        ('0.7', Fraction('0.7')),
        (
            'pika',
            Err("Input should be a valid fraction [type=fraction_parsing, input_value='pika', input_type=str]"),
        ),
    ],
)
def test_non_finite_json_values(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'fraction'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        # lower e, minus
        ('1.0e-12', Fraction('1e-12')),
        ('1e-12', Fraction('1e-12')),
        ('12e-1', Fraction('12e-1')),
        # upper E, minus
        ('1.0E-12', Fraction('1e-12')),
        ('1E-12', Fraction('1e-12')),
        ('12E-1', Fraction('12e-1')),
        # lower E, plus
        ('1.0e+12', Fraction(' 1e12')),
        ('1e+12', Fraction(' 1e12')),
        ('12e+1', Fraction(' 12e1')),
        # upper E, plus
        ('1.0E+12', Fraction(' 1e12')),
        ('1E+12', Fraction(' 1e12')),
        ('12E+1', Fraction(' 12e1')),
        # lower E, unsigned
        ('1.0e12', Fraction(' 1e12')),
        ('1e12', Fraction(' 1e12')),
        ('12e1', Fraction(' 12e1')),
        # upper E, unsigned
        ('1.0E12', Fraction(' 1e12')),
        ('1E12', Fraction(' 1e12')),
        ('12E1', Fraction(' 12e1')),
    ],
)
def test_validate_scientific_notation_from_json(input_value, expected):
    v = SchemaValidator(cs.fraction_schema())
    assert v.validate_json(input_value) == expected


def test_str_validation_w_strict() -> None:
    s = SchemaValidator(cs.fraction_schema(strict=True))

    with pytest.raises(ValidationError):
        assert s.validate_python('1.23')


def test_str_validation_w_lax() -> None:
    s = SchemaValidator(cs.fraction_schema(strict=False))

    assert s.validate_python('1.23') == Fraction('1.23')


def test_union_with_str_prefers_str() -> None:
    s = SchemaValidator(cs.union_schema([cs.fraction_schema(), cs.str_schema()]))

    assert s.validate_python('1.23') == '1.23'
    assert s.validate_python(1.23) == Fraction('1.23')
