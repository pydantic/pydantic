"""
json
JsonList
JsonDict
"""
from typing import Type

from pydantic.fields import str_validator


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
            raise ValueError(f'length less than minimum allowed length {cls.min_length}')

        if cls.curtail_length:
            if l > cls.curtail_length:
                value = value[:cls.curtail_length]
        elif cls.max_length and l > cls.max_length:
            raise ValueError(f'length greater than maximum allowed length {cls.max_length}')

        return value


def constr(*, min_length=0, max_length=2**16, curtail_length=None) -> Type[str]:
    # use kwargs then define conf in a dict to aid with IDE type hinting
    namespace = dict(
        min_length=min_length,
        max_length=max_length,
        curtail_length=curtail_length,
    )
    return type('ConstrainedStrValue', (ConstrainedStr,), namespace)

