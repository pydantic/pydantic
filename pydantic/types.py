import re
from typing import Optional, Pattern, Type, Union
from uuid import UUID

from .utils import import_string, make_dsn, validate_email
from .validators import (anystr_length_validator, anystr_strip_whitespace, not_none_validator, number_size_validator,
                         str_validator)

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


class UUID1(UUID):
    _required_version = 1


class UUID3(UUID):
    _required_version = 3


class UUID4(UUID):
    _required_version = 4


class UUID5(UUID):
    _required_version = 5


# TODO, JsonEither, JsonList, JsonDict
