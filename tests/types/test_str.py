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


class ConStringModel(BaseModel):
    v: Annotated[str, StringConstraints(max_length=10)] = 'foobar'


class StrModel(BaseModel):
    str_check: Annotated[str, annotated_types.Len(5, 10)]


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
    class Model(BaseModel):
        v: Annotated[str, StringConstraints(strip_whitespace=True, max_length=10)]

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_constrained_str_good():
    m = ConStringModel(v='short')
    assert m.v == 'short'


def test_constrained_str_default():
    m = ConStringModel()
    assert m.v == 'foobar'


@pytest.mark.parametrize(
    ('data', 'valid'),
    [('this is too long', False), ('⛄' * 11, False), ('not long90', True), ('⛄' * 10, True)],
)
def test_constrained_str_too_long(data, valid):
    if valid:
        assert ConStringModel(v=data).model_dump() == {'v': data}
    else:
        with pytest.raises(ValidationError) as exc_info:
            ConStringModel(v=data)
        # insert_assert(exc_info.value.errors(include_url=False))
        assert exc_info.value.errors(include_url=False) == [
            {
                'ctx': {'max_length': 10},
                'input': data,
                'loc': ('v',),
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
    class Model(BaseModel):
        v: Annotated[str, StringConstraints(to_upper=to_upper)]

    m = Model(v=value)
    assert m.v == result


@pytest.mark.parametrize(
    'to_lower, value, result',
    [
        (True, 'ABCD', 'abcd'),
        (False, 'ABCD', 'ABCD'),
    ],
)
def test_constrained_str_lower(to_lower, value, result):
    class Model(BaseModel):
        v: Annotated[str, StringConstraints(to_lower=to_lower)]

    m = Model(v=value)
    assert m.v == result


def test_constrained_str_max_length_0():
    class Model(BaseModel):
        v: Annotated[str, StringConstraints(max_length=0)]

    m = Model(v='')
    assert m.v == ''
    with pytest.raises(ValidationError) as exc_info:
        Model(v='qwe')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': ('v',),
            'msg': 'String should have at most 0 characters',
            'input': 'qwe',
            'ctx': {'max_length': 0},
        }
    ]


def test_string_too_long():
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x' * 150)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': ('str_check',),
            'msg': 'String should have at most 10 characters',
            'input': 'x' * 150,
            'ctx': {'max_length': 10},
        }
    ]


def test_string_too_short():
    with pytest.raises(ValidationError) as exc_info:
        StrModel(str_check='x')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_short',
            'loc': ('str_check',),
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

    class Model(BaseModel):
        v: StrictStr

    assert Model(v='foobar').v == 'foobar'

    assert Model.model_validate({'v': FruitEnum.banana}) == Model.model_construct(v=FruitEnum.banana)

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        Model(v=123)

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        Model(v=b'foobar')


def test_strict_str_max_length():
    class Model(BaseModel):
        u: StrictStr = Field(max_length=5)

    assert Model(u='foo').u == 'foo'

    with pytest.raises(ValidationError, match='Input should be a valid string'):
        Model(u=123)

    with pytest.raises(ValidationError, match=r'String should have at most 5 characters \[type=string_too_long,'):
        Model(u='1234567')


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [
        (True, '  123  ', '123'),
        (True, '  123\t\n', '123'),
        (False, '  123  ', '  123  '),
    ],
)
def test_str_strip_whitespace(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        model_config = ConfigDict(str_strip_whitespace=enabled)

    m = Model(str_check=str_check)
    assert m.str_check == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'ABCDEFG'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_str_to_upper(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        model_config = ConfigDict(str_to_upper=enabled)

    m = Model(str_check=str_check)

    assert m.str_check == result_str_check


@pytest.mark.parametrize(
    'enabled,str_check,result_str_check',
    [(True, 'ABCDefG', 'abcdefg'), (False, 'ABCDefG', 'ABCDefG')],
)
def test_str_to_lower(enabled, str_check, result_str_check):
    class Model(BaseModel):
        str_check: str

        model_config = ConfigDict(str_to_lower=enabled)

    m = Model(str_check=str_check)

    assert m.str_check == result_str_check


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
    class Model(BaseModel):
        v: Annotated[str, StringConstraints(ascii_only=True)]

    assert Model(v='hello').v == 'hello'
    with pytest.raises(ValidationError) as exc_info:
        Model(v='caf\xe9')
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'string_not_ascii',
        'loc': ('v',),
        'msg': 'String should contain only ASCII characters',
        'input': 'caf\xe9',
    }


def test_coerce_numbers_to_str_disabled_in_strict_mode() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(strict=True, coerce_numbers_to_str=True)
        value: str

    with pytest.raises(ValidationError, match='value'):
        Model.model_validate({'value': 42})
    with pytest.raises(ValidationError, match='value'):
        Model.model_validate_json('{"value": 42}')


@pytest.mark.parametrize('value_param', [True, False])
def test_coerce_numbers_to_str_raises_for_bool(value_param: bool) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)
        value: str

    with pytest.raises(ValidationError, match='value'):
        Model.model_validate({'value': value_param})
    with pytest.raises(ValidationError, match='value'):
        if value_param is True:
            Model.model_validate_json('{"value": true}')
        elif value_param is False:
            Model.model_validate_json('{"value": false}')

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
    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)
        value: str

    assert Model.model_validate({'value': number}).model_dump() == {'value': expected_str}


@pytest.mark.parametrize(
    ('number', 'expected_str'),
    [
        pytest.param('42', '42', id='42'),
        pytest.param('42.0', '42', id='42.0'),
        pytest.param('42.13', '42.13', id='42.13'),
    ],
)
def test_coerce_numbers_to_str_from_json(number: str, expected_str: str) -> None:
    class Model(BaseModel):
        model_config = ConfigDict(coerce_numbers_to_str=True)
        value: str

    assert Model.model_validate_json(f'{{"value": {number}}}').model_dump() == {'value': expected_str}


def test_python_re_respects_flags() -> None:
    class Model(BaseModel):
        a: Annotated[str, StringConstraints(pattern=re.compile(r'[A-Z]+', re.IGNORECASE))]

        model_config = ConfigDict(regex_engine='python-re')

    # allows lowercase letters, even though the pattern is uppercase only due to the IGNORECASE flag
    assert Model(a='abc').a == 'abc'
