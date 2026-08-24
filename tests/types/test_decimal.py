from decimal import Decimal
from typing import Annotated

import pytest
from pydantic_core import SchemaError

from pydantic import AllowInfNan, BaseModel, Field, TypeAdapter, ValidationError

pos_int_values = 'Inf', '+Inf', 'Infinity', '+Infinity'
neg_int_values = '-Inf', '-Infinity'
nan_values = 'NaN', '-NaN', '+NaN', 'sNaN', '-sNaN', '+sNaN'
non_finite_values = nan_values + pos_int_values + neg_int_values
# dirty_equals.AnyThing() doesn't work with Decimal on PyPy, hence this hack
ANY_THING = object()


@pytest.mark.parametrize(
    'value,expected',
    [
        (42.24, Decimal('42.24')),
        pytest.param('42.24', Decimal('42.24'), id='42.24_str'),
        pytest.param(b'42.24', ValidationError, id='42.24_bytes'),
        ('  42.24  ', Decimal('42.24')),
        (Decimal('42.24'), Decimal('42.24')),
        ('not a valid decimal', ValidationError),
        ('NaN', ValidationError),
    ],
)
def test_decimal_coercions(value, expected):
    ta = TypeAdapter(Annotated[Decimal, AllowInfNan(False)])

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_decimal():
    ta = TypeAdapter(Decimal)

    v = ta.validate_python('1.234')
    assert v == Decimal('1.234')
    assert isinstance(v, Decimal)


def test_decimal_constraint_coerced() -> None:
    ta = TypeAdapter(Annotated[Decimal, Field(gt=2)])

    with pytest.raises(ValidationError):
        ta.validate_python(Decimal(0))


def test_decimal_allow_inf():
    ta = TypeAdapter(Annotated[Decimal, AllowInfNan(True)])

    assert ta.validate_python('inf') == Decimal('inf')
    assert ta.validate_python(Decimal('inf')) == Decimal('inf')


def test_decimal_dont_allow_inf():
    ta = TypeAdapter(Decimal)

    with pytest.raises(ValidationError, match=r'Input should be a finite number \[type=finite_number'):
        ta.validate_python('inf')
    with pytest.raises(ValidationError, match=r'Input should be a finite number \[type=finite_number'):
        ta.validate_python(Decimal('inf'))


def test_decimal_strict():
    ta = TypeAdapter(Decimal)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1.23, strict=True)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': (),
            'msg': 'Input should be an instance of Decimal',
            'input': 1.23,
            'ctx': {'class': 'Decimal'},
        }
    ]

    v = Decimal(1.23)
    assert ta.validate_python(v, strict=True) == v

    assert ta.validate_json('"1.23"', strict=True) == Decimal('1.23')


def test_decimal_precision() -> None:
    ta = TypeAdapter(Decimal)

    num = f'{1234567890 * 100}.{1234567890 * 100}'

    expected = Decimal(num)
    assert ta.validate_python(num) == expected
    assert ta.validate_json(f'"{num}"') == expected


def test_decimal_float_precision() -> None:
    """https://github.com/pydantic/pydantic/issues/6807"""
    ta = TypeAdapter(Decimal)
    assert ta.validate_json('1.1') == Decimal('1.1')
    assert ta.validate_python(1.1) == Decimal('1.1')
    assert ta.validate_json('"1.1"') == Decimal('1.1')
    assert ta.validate_python('1.1') == Decimal('1.1')
    assert ta.validate_json('1') == Decimal('1')
    assert ta.validate_python(1) == Decimal('1')


@pytest.mark.parametrize(
    'type_args,value,result',
    [
        (dict(gt=Decimal('42.24')), Decimal('43'), Decimal('43')),
        (
            dict(gt=Decimal('42.24')),
            Decimal('42'),
            [
                {
                    'type': 'greater_than',
                    'loc': ('foo',),
                    'msg': 'Input should be greater than 42.24',
                    'input': Decimal('42'),
                    'ctx': {'gt': Decimal('42.24')},
                }
            ],
        ),
        (dict(lt=Decimal('42.24')), Decimal('42'), Decimal('42')),
        (
            dict(lt=Decimal('42.24')),
            Decimal('43'),
            [
                {
                    'type': 'less_than',
                    'loc': ('foo',),
                    'msg': 'Input should be less than 42.24',
                    'input': Decimal('43'),
                    'ctx': {
                        'lt': Decimal('42.24'),
                    },
                },
            ],
        ),
        (dict(ge=Decimal('42.24')), Decimal('43'), Decimal('43')),
        (dict(ge=Decimal('42.24')), Decimal('42.24'), Decimal('42.24')),
        (
            dict(ge=Decimal('42.24')),
            Decimal('42'),
            [
                {
                    'type': 'greater_than_equal',
                    'loc': ('foo',),
                    'msg': 'Input should be greater than or equal to 42.24',
                    'input': Decimal('42'),
                    'ctx': {
                        'ge': Decimal('42.24'),
                    },
                }
            ],
        ),
        (dict(le=Decimal('42.24')), Decimal('42'), Decimal('42')),
        (dict(le=Decimal('42.24')), Decimal('42.24'), Decimal('42.24')),
        (
            dict(le=Decimal('42.24')),
            Decimal('43'),
            [
                {
                    'type': 'less_than_equal',
                    'loc': ('foo',),
                    'msg': 'Input should be less than or equal to 42.24',
                    'input': Decimal('43'),
                    'ctx': {
                        'le': Decimal('42.24'),
                    },
                }
            ],
        ),
        (dict(max_digits=2, decimal_places=2), Decimal('0.99'), Decimal('0.99')),
        pytest.param(
            dict(max_digits=2, decimal_places=1),
            Decimal('0.99'),
            [
                {
                    'type': 'decimal_max_places',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 1 decimal place',
                    'input': Decimal('0.99'),
                    'ctx': {
                        'decimal_places': 1,
                    },
                }
            ],
        ),
        (
            dict(max_digits=3, decimal_places=1),
            Decimal('999'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 2 digits before the decimal point',
                    'type': 'decimal_whole_digits',
                    'input': Decimal('999'),
                    'ctx': {'whole_digits': 2},
                }
            ],
        ),
        (dict(max_digits=4, decimal_places=1), Decimal('999'), Decimal('999')),
        (dict(max_digits=20, decimal_places=2), Decimal('742403889818000000'), Decimal('742403889818000000')),
        (dict(max_digits=20, decimal_places=2), Decimal('7.42403889818E+17'), Decimal('7.42403889818E+17')),
        (dict(max_digits=6, decimal_places=2), Decimal('000000000001111.700000'), Decimal('000000000001111.700000')),
        (
            dict(max_digits=6, decimal_places=2),
            Decimal('0000000000011111.700000'),
            [
                {
                    'type': 'decimal_whole_digits',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 4 digits before the decimal point',
                    'input': Decimal('11111.700000'),
                    'ctx': {'whole_digits': 4},
                }
            ],
        ),
        (
            dict(max_digits=20, decimal_places=2),
            Decimal('7424742403889818000000'),
            [
                {
                    'type': 'decimal_max_digits',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 20 digits in total',
                    'input': Decimal('7424742403889818000000'),
                    'ctx': {
                        'max_digits': 20,
                    },
                },
            ],
        ),
        (dict(max_digits=5, decimal_places=2), Decimal('7304E-1'), Decimal('7304E-1')),
        (
            dict(max_digits=5, decimal_places=2),
            Decimal('7304E-3'),
            [
                {
                    'type': 'decimal_max_places',
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 2 decimal places',
                    'input': Decimal('7.304'),
                    'ctx': {'decimal_places': 2},
                }
            ],
        ),
        (dict(max_digits=5, decimal_places=5), Decimal('70E-5'), Decimal('70E-5')),
        (
            dict(max_digits=4, decimal_places=4),
            Decimal('70E-6'),
            [
                {
                    'loc': ('foo',),
                    'msg': 'Decimal input should have no more than 4 digits in total',
                    'type': 'decimal_max_digits',
                    'input': Decimal('0.00007'),
                    'ctx': {'max_digits': 4},
                }
            ],
        ),
        *[
            (
                dict(decimal_places=2, max_digits=10, allow_inf_nan=False),
                value,
                [
                    {
                        'loc': ('foo',),
                        'msg': 'Input should be a finite number',
                        'type': 'finite_number',
                        'input': value,
                    }
                ],
            )
            for value in non_finite_values
        ],
        *[
            (
                dict(decimal_places=2, max_digits=10, allow_inf_nan=False),
                Decimal(value),
                [
                    {
                        'loc': ('foo',),
                        'msg': 'Input should be a finite number',
                        'type': 'finite_number',
                        'input': ANY_THING,
                    }
                ],
            )
            for value in non_finite_values
        ],
        (
            dict(multiple_of=Decimal('5')),
            Decimal('42'),
            [
                {
                    'type': 'multiple_of',
                    'loc': ('foo',),
                    'msg': 'Input should be a multiple of 5',
                    'input': Decimal('42'),
                    'ctx': {'multiple_of': Decimal('5')},
                }
            ],
        ),
    ],
)
@pytest.mark.parametrize('mode', ['Field', 'annotated', 'optional'])
def test_decimal_validation(mode, type_args, value, result):
    if mode == 'Field':

        class Model(BaseModel):
            foo: Decimal = Field(**type_args)

    elif mode == 'optional':

        class Model(BaseModel):
            foo: Decimal | None = Field(**type_args)

    else:

        class Model(BaseModel):
            foo: Annotated[Decimal, Field(**type_args)]

    if not isinstance(result, Decimal):
        with pytest.raises(ValidationError) as exc_info:
            m = Model(foo=value)
            print(f'unexpected result: {m!r}')
        # debug(exc_info.value.errors(include_url=False))
        # dirty_equals.AnyThing() doesn't work with Decimal on PyPy, hence this hack
        errors = exc_info.value.errors(include_url=False)
        if result[0].get('input') is ANY_THING:
            for e in errors:
                e['input'] = ANY_THING
        assert errors == result
        # assert exc_info.value.json().startswith('[')
    else:
        assert Model(foo=value).foo == result


@pytest.mark.parametrize(
    'value,result',
    [
        (Decimal('42'), 'unchanged'),
        *[(v, 'is_nan') for v in nan_values],
        *[(v, 'is_pos_inf') for v in pos_int_values],
        *[(v, 'is_neg_inf') for v in neg_int_values],
    ],
)
def test_decimal_not_finite(value, result):
    ta = TypeAdapter(Annotated[Decimal, AllowInfNan(True)])

    v = ta.validate_python(value)
    if result == 'unchanged':
        assert v == value
    elif result == 'is_nan':
        assert v.is_nan(), v
    elif result == 'is_pos_inf':
        assert v.is_infinite() and v > 0, v
    else:
        assert result == 'is_neg_inf'
        assert v.is_infinite() and v < 0, v


def test_decimal_invalid():
    with pytest.raises(SchemaError, match='allow_inf_nan=True cannot be used with max_digits or decimal_places'):
        TypeAdapter(Annotated[Decimal, Field(allow_inf_nan=True, max_digits=4)])
