import re
from decimal import Decimal
from enum import Enum
from numbers import Number
from typing import Annotated

import annotated_types
import pytest

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    StringConstraints,
    TypeAdapter,
    ValidationError,
)
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pytest.mark.parametrize(
    'value,expected',
    [
        pytest.param('s', 's', id='s_str'),
        pytest.param('  s  ', 's', id='s_str_stripped'),
        (' leading', 'leading'),
        ('trailing ', 'trailing'),
        pytest.param(b's', 's', id='s_bytes'),
        pytest.param(b'  s  ', 's', id='s_bytes_stripped'),
        (bytearray(b's' * 5), 'sssss'),
        (1, ValidationError),
        pytest.param('x' * 11, ValidationError, id='too_long_str'),
        pytest.param(b'x' * 11, ValidationError, id='too_long_bytes'),
        (b'\x81', ValidationError),
        (bytearray(b'\x81' * 5), ValidationError),
    ],
)
def test_str_validation(value, expected):
    ta = TypeAdapter(Annotated[str, StringConstraints(strip_whitespace=True, max_length=10)])

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_constrained_str_good():
    ta = TypeAdapter(Annotated[str, StringConstraints(max_length=10)])

    assert ta.validate_python('short') == 'short'


def test_constrained_str_default():
    class Model(BaseModel):
        v: Annotated[str, StringConstraints(max_length=10)] = 'foobar'

    m = Model()
    assert m.v == 'foobar'


@pytest.mark.parametrize(
    ('data', 'valid'),
    [('this is too long', False), ('⛄' * 11, False), ('not long90', True), ('⛄' * 10, True)],
)
def test_constrained_str_too_long(data, valid):
    ta = TypeAdapter(Annotated[str, StringConstraints(max_length=10)])

    if valid:
        assert ta.validate_python(data) == data
    else:
        with pytest.raises(ValidationError) as exc_info:
            ta.validate_python(data)
        # insert_assert(exc_info.value.errors(include_url=False))
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'max_length': 10},
                'input': data,
                'loc': (),
                'msg': 'String should have at most 10 characters',
                'type': 'string_too_long',
            }
        ]


@pytest.mark.parametrize(
    'to_upper, value, result',
    [
        (True, 'abcd', 'ABCD'),
        (False, 'aBcD', 'aBcD'),
    ],
)
def test_constrained_str_upper(to_upper, value, result):
    ta = TypeAdapter(Annotated[str, StringConstraints(to_upper=to_upper)])

    assert ta.validate_python(value) == result


@pytest.mark.parametrize(
    'to_lower, value, result',
    [
        (True, 'ABCD', 'abcd'),
        (False, 'ABCD', 'ABCD'),
    ],
)
def test_constrained_str_lower(to_lower, value, result):
    ta = TypeAdapter(Annotated[str, StringConstraints(to_lower=to_lower)])

    assert ta.validate_python(value) == result


def test_constrained_str_max_length_0():
    ta = TypeAdapter(Annotated[str, StringConstraints(max_length=0)])

    assert ta.validate_python('') == ''
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('qwe')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': (),
            'msg': 'String should have at most 0 characters',
            'input': 'qwe',
            'ctx': {'max_length': 0},
        }
    ]


def test_string_too_long():
    ta = TypeAdapter(Annotated[str, annotated_types.Len(5, 10)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('x' * 150)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': (),
            'msg': 'String should have at most 10 characters',
            'input': 'x' * 150,
            'ctx': {'max_length': 10},
        }
    ]


def test_string_too_short():
    ta = TypeAdapter(Annotated[str, annotated_types.Len(5, 10)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('x')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_short',
            'loc': (),
            'msg': 'String should have at least 5 characters',
            'input': 'x',
            'ctx': {'min_length': 5},
        }
    ]


def test_strict_str():
    class FruitEnum(str, Enum):
        """A subclass of a string"""

        pear = 'pear'
        banana = 'banana'

    ta = TypeAdapter(StrictStr)

    assert ta.validate_python('foobar') == 'foobar'

    assert ta.validate_python(FruitEnum.banana) == FruitEnum.banana

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        ta.validate_python(123)

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        ta.validate_python(b'foobar')


def test_strict_str_max_length():
    ta = TypeAdapter(Annotated[StrictStr, Field(max_length=5)])

    assert ta.validate_python('foo') == 'foo'

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        ta.validate_python(123)

    with pytest.raises(ValidationError, match=r'String should have at most 5 characters \[type=string_too_long,'):
        ta.validate_python('1234567')


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [
        (True, '  123  ', '123'),
        (True, '  123\t\n', '123'),
        (False, '  123  ', '  123  '),
    ],
)
def test_str_strip_whitespace(enabled, str_check, result_str_check):
    ta = TypeAdapter(str, config=ConfigDict(str_strip_whitespace=enabled))

    assert ta.validate_python(str_check) == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'ABCDEFG'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_str_to_upper(enabled, str_check, result_str_check):
    ta = TypeAdapter(str, config=ConfigDict(str_to_upper=enabled))

    assert ta.validate_python(str_check) == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'abcdefg'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_str_to_lower(enabled, str_check, result_str_check):
    ta = TypeAdapter(str, config=ConfigDict(str_to_lower=enabled))

    assert ta.validate_python(str_check) == result_str_check


def test_string_constraints() -> None:
    ta = TypeAdapter(
        Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True), AfterValidator(lambda x: x * 2)]
    )
    assert ta.validate_python(' ABC ') == 'abcabc'


def test_string_constraints_strict() -> None:
    ta = TypeAdapter(Annotated[str, StringConstraints(strict=False)])
    assert ta.validate_python(b'123') == '123'

    ta = TypeAdapter(Annotated[str, StringConstraints(strict=True)])
    with pytest.raises(ValidationError):
        ta.validate_python(b'123')


def test_string_constraints_ascii_only() -> None:
    ta = TypeAdapter(Annotated[str, StringConstraints(ascii_only=True)])

    assert ta.validate_python('hello') == 'hello'
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('caf\xe9')
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'string_not_ascii',
        'loc': (),
        'msg': 'String should contain only ASCII characters',
        'input': 'caf\xe9',
    }


def test_coerce_numbers_to_str_disabled_in_strict_mode() -> None:
    ta = TypeAdapter(str, config=ConfigDict(strict=True, coerce_numbers_to_str=True))

    with pytest.raises(ValidationError):
        ta.validate_python(42)
    with pytest.raises(ValidationError):
        ta.validate_json('42')


@pytest.mark.parametrize('value_param', [True, False])
def test_coerce_numbers_to_str_raises_for_bool(value_param: bool) -> None:
    ta = TypeAdapter(str, config=ConfigDict(coerce_numbers_to_str=True))

    with pytest.raises(ValidationError):
        ta.validate_python(value_param)
    with pytest.raises(ValidationError):
        if value_param is True:
            ta.validate_json('true')
        elif value_param is False:
            ta.validate_json('false')

    @pydantic_dataclass(config=ConfigDict(coerce_numbers_to_str=True))
    class Model:
        value: str

    with pytest.raises(ValidationError, match='value'):
        Model(value=value_param)


@pytest.mark.parametrize(
    ('number', 'expected_str'),
    [
        pytest.param(42, '42', id='42'),
        pytest.param(42.0, '42.0', id='42.0'),
        pytest.param(Decimal('42.0'), '42.0', id="Decimal('42.0')"),
    ],
)
def test_coerce_numbers_to_str(number: Number, expected_str: str) -> None:
    ta = TypeAdapter(str, config=ConfigDict(coerce_numbers_to_str=True))

    assert ta.validate_python(number) == expected_str


@pytest.mark.parametrize(
    ('number', 'expected_str'),
    [
        pytest.param('42', '42', id='42'),
        pytest.param('42.0', '42', id='42.0'),
        pytest.param('42.13', '42.13', id='42.13'),
    ],
)
def test_coerce_numbers_to_str_from_json(number: str, expected_str: str) -> None:
    ta = TypeAdapter(str, config=ConfigDict(coerce_numbers_to_str=True))

    assert ta.validate_json(number) == expected_str


def test_python_re_respects_flags() -> None:
    ta = TypeAdapter(
        Annotated[str, StringConstraints(pattern=re.compile(r'[A-Z]+', re.IGNORECASE))],
        config=ConfigDict(regex_engine='python-re'),
    )

    # allows lowercase letters, even though the pattern is uppercase only due to the IGNORECASE flag
    assert ta.validate_python('abc') == 'abc'


def test_str_validate_json():
    ta = TypeAdapter(str)

    assert ta.validate_json('"foobar"') == 'foobar'
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        ta.validate_json('false')
    with pytest.raises(ValidationError, match=r'Input should be a valid string \[type=string_type,'):
        ta.validate_json('123')
