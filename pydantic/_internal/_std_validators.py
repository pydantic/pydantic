from __future__ import annotations as _annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum, IntEnum
from pathlib import Path, PurePath
from typing import Any, Callable
from uuid import UUID

from pydantic_core import PydanticCustomError, PydanticErrorKind, core_schema

from ._fields import CustomValidator

__all__ = ('SCHEMA_LOOKUP',)


def name_as_schema(t: type[Any]) -> core_schema.CoreSchema:
    return {'type': t.__name__}


def enum_schema(enum_type: type[Enum]) -> core_schema.CoreSchema:
    def to_enum(v: Any, **_kwargs: Any) -> Enum:
        try:
            return enum_type(v)
        except ValueError:
            raise PydanticCustomError('enum', 'Input is not a valid enum member')

    literal_schema = core_schema.literal_schema(*[m.value for m in enum_type.__members__.values()])

    if issubclass(enum_type, IntEnum):
        return core_schema.chain_schema(
            core_schema.int_schema(), literal_schema, core_schema.function_plain_schema(to_enum)
        )
    elif issubclass(enum_type, str):
        return core_schema.chain_schema(
            core_schema.string_schema(), literal_schema, core_schema.function_plain_schema(to_enum)
        )
    else:
        return core_schema.function_after_schema(
            schema=literal_schema,
            function=to_enum,
        )


class DecimalValidator(CustomValidator):
    __slots__ = (
        'gt',
        'ge',
        'lt',
        'le',
        'max_digits',
        'decimal_places',
        'multiple_of',
        'allow_inf_nan',
        'check_digits',
        'strict',
    )

    def __init__(self) -> None:
        self.gt: int | Decimal | None = None
        self.ge: int | Decimal | None = None
        self.lt: int | Decimal | None = None
        self.le: int | Decimal | None = None
        self.max_digits: int | None = None
        self.decimal_places: int | None = None
        self.multiple_of: int | Decimal | None = None
        self.allow_inf_nan: bool = True
        self.check_digits: bool = False
        self.strict: bool = False

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in self.__slots__:
                raise TypeError(f'{self.__class__.__name__}.update() got an unexpected keyword argument {k!r}')
            setattr(self, k, v)

        self.check_digits = (
            self.max_digits is not None or self.decimal_places is not None or self.allow_inf_nan is False
        )

    def validate(self, value: int | float | str, **_kwargs: Any) -> Decimal:
        if not isinstance(value, Decimal):
            v = str(value)

            try:
                value = Decimal(v)
            except DecimalException:
                raise PydanticCustomError('decimal_parsing', 'Input should be a valid decimal')

        if self.check_digits:
            digit_tuple, exponent = value.as_tuple()[1:]
            if not self.allow_inf_nan and exponent in {'F', 'n', 'N'}:
                raise PydanticCustomError('decimal_finite_number', 'Input should be a finite number')

            if exponent >= 0:
                # A positive exponent adds that many trailing zeros.
                digits = len(digit_tuple) + exponent
                decimals = 0
            else:
                # If the absolute value of the negative exponent is larger than the
                # number of digits, then it's the same as the number of digits,
                # because it'll consume all the digits in digit_tuple and then
                # add abs(exponent) - len(digit_tuple) leading zeros after the
                # decimal point.
                if abs(exponent) > len(digit_tuple):
                    digits = decimals = abs(exponent)
                else:
                    digits = len(digit_tuple)
                    decimals = abs(exponent)
            whole_digits = digits - decimals

            if self.max_digits is not None and digits > self.max_digits:
                raise PydanticCustomError(
                    'decimal_max_digits',
                    'ensure that there are no more than {max_digits} digits in total',
                    {'max_digits': self.max_digits},
                )

            if self.decimal_places is not None and decimals > self.decimal_places:
                raise PydanticCustomError(
                    'decimal_max_places',
                    'ensure that there are no more than {decimal_places} decimal places',
                    {'decimal_places': self.decimal_places},
                )

            if self.max_digits is not None and self.decimal_places is not None:
                expected = self.max_digits - self.decimal_places
                if whole_digits > expected:
                    raise PydanticCustomError(
                        'decimal_whole_digits',
                        'ensure that there are no more than {whole_digits} digits before the decimal point',
                        {'whole_digits': whole_digits},
                    )

        if self.multiple_of is not None:
            mod = value / self.multiple_of % 1
            if mod != 0:
                raise PydanticCustomError(
                    'decimal_multiple_of',
                    'Input should be a multiple of {multiple_of}',
                    {'multiple_of': self.multiple_of},
                )

        if self.gt is not None and not value > self.gt:
            raise PydanticErrorKind('greater_than', {'gt': self.gt})
        elif self.ge is not None and not value >= self.ge:
            raise PydanticErrorKind('greater_than_equal', {'ge': self.ge})

        if self.lt is not None and not value < self.lt:
            raise PydanticErrorKind('less_than', {'lt': self.lt})
        if self.le is not None and not value <= self.le:
            raise PydanticErrorKind('less_than_equal', {'le': self.le})

        return value

    def __repr__(self) -> str:
        slots = [(k, getattr(self, k)) for k in self.__slots__]
        s = ', '.join(f'{k}={v!r}' for k, v in slots if v is not None)
        return f'DecimalValidator({s})'


def decimal_schema(_decimal_type: type[Decimal]) -> core_schema.FunctionSchema:
    decimal_validator = DecimalValidator()
    return core_schema.function_after_schema(
        decimal_validator.validate,
        core_schema.union_schema(
            core_schema.int_schema(),
            core_schema.float_schema(),
            core_schema.string_schema(strip_whitespace=True),
        ),
        validator_instance=decimal_validator,
    )


def uuid_validator(input_value: str | bytes, **_kwargs: Any) -> UUID:
    try:
        if isinstance(input_value, str):
            return UUID(input_value)
        else:
            try:
                return UUID(input_value.decode())
            except ValueError:
                # 16 bytes in big-endian order as the bytes argument fail
                # the above check
                return UUID(bytes=input_value)
    except ValueError:
        raise PydanticCustomError('uuid_parsing', 'Input should be a valid UUID, unable to parse string as an UUID')


def uuid_schema(uuid_type: type[UUID]) -> core_schema.UnionSchema:
    # TODO, is this actually faster than `function_after(union(is_instance, is_str, is_bytes))`?
    return core_schema.union_schema(
        core_schema.is_instance_schema(uuid_type),
        core_schema.function_after_schema(
            uuid_validator,
            core_schema.union_schema(
                core_schema.string_schema(),
                core_schema.bytes_schema(),
            ),
        ),
        custom_error_kind='uuid_type',
        custom_error_message='Input should be a valid UUID, string, or bytes',
        strict=True,
    )


def path_validator(v: str) -> Path:
    try:
        return Path(v)
    except TypeError:
        raise PydanticCustomError('path', 'Input is not a valid path')


def path_schema(path_type: type[PurePath]) -> core_schema.UnionSchema:
    # TODO, is this actually faster than `function_after(...)` as above?
    return core_schema.union_schema(
        core_schema.is_instance_schema(path_type),
        core_schema.function_after_schema(
            path_validator,
            core_schema.string_schema(),
        ),
        strict=True,
    )


SCHEMA_LOOKUP: dict[type[Any], Callable[[type[Any]], core_schema.CoreSchema]] = {
    date: name_as_schema,
    datetime: name_as_schema,
    time: name_as_schema,
    timedelta: name_as_schema,
    Enum: enum_schema,
    Decimal: decimal_schema,
    UUID: uuid_schema,
    PurePath: path_schema,
}
