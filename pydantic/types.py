import re
from decimal import Decimal
from typing import Optional, Pattern, Type, Union
from uuid import UUID

from .utils import import_string, make_dsn, validate_email
from .validators import (anystr_length_validator, anystr_strip_whitespace, decimal_validator, not_none_validator,
                         number_size_validator, str_validator)

try:
    import email_validator
except ImportError:
    email_validator = None

__all__ = [
    'NoneStr',
    'NoneBytes',
    'StrBytes',
    'NoneStrBytes',
    'StrictStr',
    'ConstrainedStr',
    'constr',
    'EmailStr',
    'NameEmail',
    'PyObject',
    'DSN',
    'ConstrainedInt',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'ConstrainedFloat',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'ConstrainedDecimal',
    'condecimal',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
]

NoneStr = Optional[str]
NoneBytes = Optional[bytes]
StrBytes = Union[str, bytes]
NoneStrBytes = Optional[StrBytes]


class StrictStr(str):
    @classmethod
    def get_validators(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError(f'strict string: str expected not {type(v)}')
        return v


class ConstrainedStr(str):
    strip_whitespace = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    curtail_length: Optional[int] = None
    regex: Optional[Pattern] = None

    @classmethod
    def get_validators(cls):
        yield not_none_validator
        yield str_validator
        yield anystr_strip_whitespace
        yield anystr_length_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if cls.curtail_length and len(value) > cls.curtail_length:
            value = value[:cls.curtail_length]

        if cls.regex:
            if not cls.regex.match(value):
                raise ValueError(f'string does not match regex "{cls.regex.pattern}"')

        return value


class EmailStr(str):
    @classmethod
    def get_validators(cls):
        # included here and below so the error happens straight away
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return validate_email(value)[1]


class NameEmail:
    __slots__ = 'name', 'email'

    def __init__(self, name, email):
        self.name = name
        self.email = email

    @classmethod
    def get_validators(cls):
        if email_validator is None:
            raise ImportError('email-validator is not installed, run `pip install pydantic[email]`')
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return cls(*validate_email(value))

    def __str__(self):
        return f'{self.name} <{self.email}>'

    def __repr__(self):
        return f'<NameEmail("{self}")>'


def constr(*, strip_whitespace=False, min_length=0, max_length=2**16, curtail_length=None, regex=None) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        curtail_length=curtail_length,
        regex=regex and re.compile(regex)
    )
    return type('ConstrainedStrValue', (ConstrainedStr,), namespace)


class PyObject:
    validate_always = True

    @classmethod
    def get_validators(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        try:
            return import_string(value)
        except ImportError as e:
            # errors must be TypeError or ValueError
            raise ValueError(str(e)) from e


class DSN(str):
    prefix = 'db_'
    fields = 'driver', 'user', 'password', 'host', 'port', 'name', 'query'
    validate_always = True

    @classmethod
    def get_validators(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value, values, **kwarg):
        if value:
            return value
        kwargs = {f: values.get(cls.prefix + f) for f in cls.fields}
        if kwargs['driver'] is None:
            raise ValueError(f'"{cls.prefix}driver" field may not be missing or None')
        return make_dsn(**kwargs)


class ConstrainedInt(int):
    gt: Optional[int] = None
    lt: Optional[int] = None

    @classmethod
    def get_validators(cls):
        yield int
        yield number_size_validator


def conint(*, gt=None, lt=None) -> Type[int]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, lt=lt)
    return type('ConstrainedIntValue', (ConstrainedInt,), namespace)


class PositiveInt(ConstrainedInt):
    gt = 0


class NegativeInt(ConstrainedInt):
    lt = 0


class ConstrainedFloat(float):
    gt: Union[None, int, float] = None
    lt: Union[None, int, float] = None

    @classmethod
    def get_validators(cls):
        yield float
        yield number_size_validator


def confloat(*, gt=None, lt=None) -> Type[float]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, lt=lt)
    return type('ConstrainedFloatValue', (ConstrainedFloat,), namespace)


class PositiveFloat(ConstrainedFloat):
    gt = 0


class NegativeFloat(ConstrainedFloat):
    lt = 0


class ConstrainedDecimal(Decimal):
    gt: Union[None, int, float, Decimal] = None
    lt: Union[None, int, float, Decimal] = None
    max_digits: Optional[int] = None
    decimal_places: Optional[int] = None

    @classmethod
    def get_validators(cls):
        yield not_none_validator
        yield decimal_validator
        yield number_size_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Decimal) -> Decimal:
        digit_tuple, exponent = value.as_tuple()[1:]
        if exponent in {'F', 'n', 'N'}:
            raise ValueError(f'value is not a valid decimal, got {value}')

        if exponent >= 0:
            # A positive exponent adds that many trailing zeros.
            digits = len(digit_tuple) + exponent
            decimals = 0
        else:
            # If the absolute value of the negative exponent is larger than the
            # number of digits, then it's the same as the number of digits,
            # because it'll consume all of the digits in digit_tuple and then
            # add abs(exponent) - len(digit_tuple) leading zeros after the
            # decimal point.
            if abs(exponent) > len(digit_tuple):
                digits = decimals = abs(exponent)
            else:
                digits = len(digit_tuple)
                decimals = abs(exponent)
        whole_digits = digits - decimals

        if cls.max_digits is not None and digits > cls.max_digits:
            raise ValueError(f'ensure that there are no more than {cls.max_digits} digits in total')

        if cls.decimal_places is not None and decimals > cls.decimal_places:
            raise ValueError(f'ensure that there are no more than {cls.decimal_places} decimal places')

        if cls.max_digits is not None and cls.decimal_places is not None:
            expected = cls.max_digits - cls.decimal_places
            if whole_digits > expected:
                raise ValueError(f'ensure that there are no more than {expected} digits before the decimal point')

        return value


def condecimal(*, gt=None, lt=None, max_digits=None, decimal_places=None) -> Type[Decimal]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        gt=gt,
        lt=lt,
        max_digits=max_digits,
        decimal_places=decimal_places
    )
    return type('ConstrainedDecimalValue', (ConstrainedDecimal,), namespace)


class UUID1(UUID):
    _required_version = 1


class UUID3(UUID):
    _required_version = 3


class UUID4(UUID):
    _required_version = 4


class UUID5(UUID):
    _required_version = 5


# TODO, JsonEither, JsonList, JsonDict
