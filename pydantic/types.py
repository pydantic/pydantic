import re
from typing import Optional, Type, Union

from .utils import import_string, make_dsn, validate_email
from .validators import str_validator

__all__ = [
    'NoneStr',
    'NoneBytes',
    'StrBytes',
    'NoneStrBytes',
    'ConstrainedStr',
    'constr',
    'EmailStr',
    'NameEmail',
    'Module',
    'DSN',
]

NoneStr = Optional[str]
NoneBytes = Optional[bytes]
StrBytes = Union[str, bytes]
NoneStrBytes = Optional[StrBytes]


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
    def validate(cls, value):
        l = len(value)
        if cls.min_length and l < cls.min_length:
            raise ValueError(f'length less than minimum allowed: {cls.min_length}')

        if cls.curtail_length:
            if l > cls.curtail_length:
                value = value[:cls.curtail_length]
        elif cls.max_length and l > cls.max_length:
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


def constr(*, min_length=0, max_length=2**16, curtail_length=None, regex=None) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        min_length=min_length,
        max_length=max_length,
        curtail_length=curtail_length,
        regex=regex and re.compile(regex)
    )
    return type('ConstrainedStrValue', (ConstrainedStr,), namespace)


class Module:
    validate_always = True

    @classmethod
    def get_validators(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return import_string(value)


class DSN(str):
    prefix = 'db_'
    validate_always = True

    @classmethod
    def get_validators(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value, model, **kwarg):
        if value:
            return value
        d = model.__values__
        kwargs = {f: d.get(cls.prefix + f) for f in ('driver', 'user', 'password', 'host', 'port', 'name', 'query')}
        if kwargs['driver'] is None:
            raise ValueError(f'"{cls.prefix}driver" field may not be missing or None')
        return make_dsn(**kwargs)


# TODO, JsonEither, JsonList, JsonDict
