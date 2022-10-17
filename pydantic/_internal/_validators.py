"""
Validator functions for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""

from __future__ import annotations as _annotations

import re
import typing
from collections import OrderedDict, deque
from decimal import Decimal, DecimalException
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic_core import PydanticCustomError, PydanticKindError, core_schema

from . import _fields


def import_string(value: Any, **_kwargs: Any) -> Any:
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


class DecimalValidator(_fields.CustomValidator):
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

    def __pydantic_update_schema__(self, _schema: core_schema.CoreSchema, **kwargs: Any) -> None:
        self._update_attrs(kwargs)

        self.check_digits = self.max_digits is not None or self.decimal_places is not None
        if self.check_digits and self.allow_inf_nan:
            raise ValueError('allow_inf_nan=True cannot be used with max_digits or decimal_places')

    def __call__(self, value: int | float | str, **_kwargs: Any) -> Decimal:  # noqa: C901 (ignore complexity)
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


def deque_any_validator(v: Any, *, validator: core_schema.CallableValidator, **_kwargs) -> deque:
    if isinstance(v, deque):
        return v
    else:
        return deque(validator(v))


def deque_typed_validator(v: list[Any], **kwargs) -> deque:
    return deque(v)


def ordered_dict_any_validator(v: Any, *, validator: core_schema.CallableValidator, **_kwargs) -> OrderedDict:
    if isinstance(v, OrderedDict):
        return v
    else:
        return OrderedDict(validator(v))


def ordered_dict_typed_validator(v: list[Any], **kwargs) -> OrderedDict:
    return OrderedDict(v)


def ip_v4_address_validator(v: Any, **_kwargs) -> IPv4Address:
    if isinstance(v, IPv4Address):
        return v

    try:
        return IPv4Address(v)
    except ValueError:
        raise PydanticCustomError('ip_v4_address', 'Input is not a valid IPv4 address')


def ip_v6_address_validator(v: Any, **_kwargs) -> IPv6Address:
    if isinstance(v, IPv6Address):
        return v

    try:
        return IPv6Address(v)
    except ValueError:
        raise PydanticCustomError('ip_v6_address', 'Input is not a valid IPv6 address')


def ip_v4_network_validator(v: Any, **_kwargs) -> IPv4Network:
    """
    Assume IPv4Network initialised with a default ``strict`` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv4Network
    """
    if isinstance(v, IPv4Network):
        return v

    try:
        return IPv4Network(v)
    except ValueError:
        raise PydanticCustomError('ip_v4_network', 'Input is not a valid IPv4 network')


def ip_v6_network_validator(v: Any, **_kwargs) -> IPv6Network:
    """
    Assume IPv6Network initialised with a default ``strict`` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv6Network
    """
    if isinstance(v, IPv6Network):
        return v

    try:
        return IPv6Network(v)
    except ValueError:
        raise PydanticCustomError('ip_v6_network', 'Input is not a valid IPv6 network')


def ip_v4_interface_validator(v: Any, **_kwargs) -> IPv4Interface:
    if isinstance(v, IPv4Interface):
        return v

    try:
        return IPv4Interface(v)
    except ValueError:
        raise PydanticCustomError('ip_v4_interface', 'Input is not a valid IPv4 interface')


def ip_v6_interface_validator(v: Any, **_kwargs) -> IPv6Interface:
    if isinstance(v, IPv6Interface):
        return v

    try:
        return IPv6Interface(v)
    except ValueError:
        raise PydanticCustomError('ip_v6_interface', 'Input is not a valid IPv6 interface')
