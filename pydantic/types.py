import re
from typing import Optional, Type, Union

from .utils import import_string, make_dsn, validate_email
from .validators import str_validator

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
    min_length: int = None
    max_length: int = None
    curtail_length: int = None
    regex = None

    @classmethod
    def get_validators(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if value is None:
            raise TypeError('None is not an allow value')

        v_len = len(value)
        if cls.min_length is not None and v_len < cls.min_length:
            raise ValueError(f'length less than minimum allowed: {cls.min_length}')

        if cls.curtail_length:
            if v_len > cls.curtail_length:
                value = value[:cls.curtail_length]
        elif cls.max_length is not None and v_len > cls.max_length:
            raise ValueError(f'length greater than maximum allowed: {cls.max_length}')

        if cls.regex:
            if not cls.regex.match(value):
                raise ValueError(f'string does not match regex "{cls.regex.pattern}"')
        return value


class EmailStr(str):
    @classmethod
    def get_validators(cls):
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
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return cls(*validate_email(value))

    def __str__(self):
        return f'{self.name} <{self.email}>'

    def __repr__(self):
        return f'<NameEmail("{self}")>'


def constr(*, min_length=0, max_length=2**16, curtail_length=None, regex=None) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
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
    gt: int = None
    lt: int = None

    @classmethod
    def get_validators(cls):
        yield int
        yield cls.validate

    @classmethod
    def validate(cls, value: int) -> int:
        if cls.gt is not None and value <= cls.gt:
            raise ValueError(f'size less than minimum allowed: {cls.gt}')
        elif cls.lt is not None and value >= cls.lt:
            raise ValueError(f'size greater than maximum allowed: {cls.lt}')
        return value


def conint(*, gt=None, lt=None) -> Type[int]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(gt=gt, lt=lt)
    return type('ConstrainedIntValue', (ConstrainedInt,), namespace)


class PositiveInt(ConstrainedInt):
    gt = 0


class NegativeInt(ConstrainedInt):
    lt = 0


# TODO, JsonEither, JsonList, JsonDict
