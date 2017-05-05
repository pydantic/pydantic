from typing import Type

from .fields import str_validator
from .utils import import_string, make_dsn

__all__ = [
    'ConstrainedStr',
    'constr',
    'Module',
    'DSN',
]


class ConstrainedStr(str):
    min_length = None
    max_length = None
    curtail_length = None

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

        return value


def constr(*, min_length=0, max_length=2**16, curtail_length=None) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        min_length=min_length,
        max_length=max_length,
        curtail_length=curtail_length,
    )
    return type('ConstrainedStrValue', (ConstrainedStr,), namespace)


class Module:
    @classmethod
    def get_validators(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return import_string(value)


class DSN(str):
    prefix = 'db_'

    @classmethod
    def get_validators(cls):
        yield str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value, model):
        if value:
            return value
        d = model.__values__
        return make_dsn(**{f: d[cls.prefix + f] for f in ('name', 'password', 'host', 'port', 'user', 'driver')})


# TODO, JsonEither, JsonList, JsonDict
