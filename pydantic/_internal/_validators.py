from __future__ import annotations as _annotations

import re
import typing
from collections import deque
from decimal import Decimal, DecimalException
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic_core import PydanticCustomError, PydanticKindError, core_schema

from ._fields import CustomValidator

__all__ = ('import_string',)


def import_string(value: Any, **kwargs) -> Any:
    if isinstance(value, str):
        try:
            return _import_string_logic(value)
        except ImportError as e:
            raise PydanticCustomError('import_error', 'Invalid python path: {error}', {'error': str(e)})
    else:
        # otherwise we just return the value and let the next validator do the rest of the work
        return value


def _import_string_logic(dotted_path: str) -> Any:
    """
    Stolen approximately from django. Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import fails.
    """
    from importlib import import_module

    try:
        module_path, class_name = dotted_path.strip(' ').rsplit('.', 1)
    except ValueError as e:
        raise ImportError(f'"{dotted_path}" doesn\'t look like a module path') from e

    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute') from e


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
        self.allow_inf_nan: bool = False
        self.check_digits: bool = False
        self.strict: bool = False

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in self.__slots__:
                raise TypeError(f'{self.__class__.__name__}.update() got an unexpected keyword argument {k!r}')
            setattr(self, k, v)

        self.check_digits = self.max_digits is not None or self.decimal_places is not None
        if self.check_digits and self.allow_inf_nan:
            raise ValueError('allow_inf_nan=True cannot be used with max_digits or decimal_places')

    def validate(self, value: int | float | str, **_kwargs: Any) -> Decimal:
        if not isinstance(value, Decimal):
            v = str(value)

            try:
                value = Decimal(v)
            except DecimalException:
                raise PydanticCustomError('decimal_parsing', 'Input should be a valid decimal')

        if not self.allow_inf_nan or self.check_digits:
            _, digit_tuple, exponent = value.as_tuple()
            if not self.allow_inf_nan and exponent in {'F', 'n', 'N'}:
                raise PydanticKindError('finite_number')

            if self.check_digits:
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
                    whole_digits = digits - decimals
                    expected = self.max_digits - self.decimal_places
                    if whole_digits > expected:
                        raise PydanticCustomError(
                            'decimal_whole_digits',
                            'ensure that there are no more than {whole_digits} digits before the decimal point',
                            {'whole_digits': expected},
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
            raise PydanticKindError('greater_than', {'gt': self.gt})
        elif self.ge is not None and not value >= self.ge:
            raise PydanticKindError('greater_than_equal', {'ge': self.ge})

        if self.lt is not None and not value < self.lt:
            raise PydanticKindError('less_than', {'lt': self.lt})
        if self.le is not None and not value <= self.le:
            raise PydanticKindError('less_than_equal', {'le': self.le})

        return value

    def __repr__(self) -> str:
        slots = [(k, getattr(self, k)) for k in self.__slots__]
        s = ', '.join(f'{k}={v!r}' for k, v in slots if v is not None)
        return f'DecimalValidator({s})'


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


def path_validator(v: str, **kwargs) -> Path:
    try:
        return Path(v)
    except TypeError:
        raise PydanticCustomError('path_type', 'Input is not a valid path')


def pattern_either_validator(v, **kwargs):
    if isinstance(v, typing.Pattern):
        return v
    elif isinstance(v, (str, bytes)):
        # todo strict mode
        return compile_pattern(v)
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_str_validator(v, **kwargs):
    if isinstance(v, typing.Pattern):
        if isinstance(v.pattern, str):
            return v
        else:
            raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    elif isinstance(v, str):
        return compile_pattern(v)
    elif isinstance(v, bytes):
        raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_bytes_validator(v, **kwargs):
    if isinstance(v, typing.Pattern):
        if isinstance(v.pattern, bytes):
            return v
        else:
            raise PydanticCustomError('pattern_bytes_type', 'Input should be a bytes pattern')
    elif isinstance(v, bytes):
        return compile_pattern(v)
    elif isinstance(v, str):
        raise PydanticCustomError('pattern_bytes_type', 'Input should be a bytes pattern')
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def compile_pattern(pattern: str | bytes) -> typing.Pattern:
    try:
        return re.compile(pattern)
    except re.error:
        raise PydanticCustomError('pattern_regex', 'Input should be a valid regular expression')


def deque_any_validator(v: Any, validator: core_schema.CallableValidator, **kwargs) -> typing.Deque:
    if isinstance(v, deque):
        return v
    else:
        return deque(validator(v))


def deque_typed_validator(v: list[Any], **kwargs) -> typing.Deque:
    return deque(v)
