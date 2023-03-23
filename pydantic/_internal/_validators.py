"""
Validator functions for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""

from __future__ import annotations as _annotations

import re
import typing
from collections import OrderedDict, defaultdict, deque
from decimal import Decimal, DecimalException
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic_core import PydanticCustomError, PydanticKnownError, core_schema

from . import _fields


def mapping_validator(
    __input_value: typing.Mapping[Any, Any],
    validator: core_schema.ValidatorFunctionWrapHandler,
    info: core_schema.ValidationInfo,
) -> typing.Mapping[Any, Any]:
    """
    Validator for `Mapping` types, if required `isinstance(v, Mapping)` has already been called.
    """
    v_dict = validator(__input_value)
    value_type = type(__input_value)

    # the rest of the logic is just re-creating the original type from `v_dict`
    if value_type == dict:
        return v_dict
    elif issubclass(value_type, defaultdict):
        default_factory = __input_value.default_factory  # type: ignore[attr-defined]
        return value_type(default_factory, v_dict)
    else:
        # best guess at how to re-create the original type, more custom construction logic might be required
        return value_type(v_dict)  # type: ignore[call-arg]


def construct_counter(__input_value: typing.Mapping[Any, Any], _: core_schema.ValidationInfo) -> typing.Counter[Any]:
    """
    Validator for `Counter` types, if required `isinstance(v, Counter)` has already been called.
    """
    return typing.Counter(__input_value)


def sequence_validator(
    __input_value: typing.Sequence[Any],
    validator: core_schema.ValidatorFunctionWrapHandler,
    _: core_schema.ValidationInfo,
) -> typing.Sequence[Any]:
    """
    Validator for `Sequence` types, isinstance(v, Sequence) has already been called.
    """
    value_type = type(__input_value)
    v_list = validator(__input_value)

    # the rest of the logic is just re-creating the original type from `v_list`
    if value_type == list:
        return v_list
    elif issubclass(value_type, str):
        try:
            return ''.join(v_list)
        except TypeError:
            # can happen if you pass a string like '123' to `Sequence[int]`
            raise PydanticKnownError('string_type')
    elif issubclass(value_type, bytes):
        try:
            return b''.join(v_list)
        except TypeError:
            # can happen if you pass a string like '123' to `Sequence[int]`
            raise PydanticKnownError('bytes_type')
    elif issubclass(value_type, range):
        # return the list as we probably can't re-create the range
        return v_list
    else:
        # best guess at how to re-create the original type, more custom construction logic might be required
        return value_type(v_list)  # type: ignore[call-arg]


def import_string(value: Any) -> Any:
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

    def json_schema_override_schema(self) -> core_schema.CoreSchema:
        """
        This function is used to produce an "override schema" for generating the JSON schema of fields of type Decimal.

        The purpose of an override schema is to use the pre-existing approach to producing a JSON schema from a
        CoreSchema, where we know we want to use a different CoreSchema for the purposes of JSON schema generation.
        (Generally because we know what we want and an appropriately simplified CoreSchema will produce it.)
        """
        return core_schema.float_schema(
            allow_inf_nan=self.allow_inf_nan,
            multiple_of=None if self.multiple_of is None else float(self.multiple_of),
            le=None if self.le is None else float(self.le),
            ge=None if self.ge is None else float(self.ge),
            lt=None if self.lt is None else float(self.lt),
            gt=None if self.gt is None else float(self.gt),
        )

    def __pydantic_update_schema__(self, schema: core_schema.CoreSchema, **kwargs: Any) -> None:
        self._update_attrs(kwargs)

        self.check_digits = self.max_digits is not None or self.decimal_places is not None
        if self.check_digits and self.allow_inf_nan:
            raise ValueError('allow_inf_nan=True cannot be used with max_digits or decimal_places')

    def __call__(  # noqa: C901 (ignore complexity)
        self, __input_value: int | float | str, _: core_schema.ValidationInfo
    ) -> Decimal:
        if isinstance(__input_value, Decimal):
            value = __input_value
        else:
            try:
                value = Decimal(str(__input_value))
            except DecimalException:
                raise PydanticCustomError('decimal_parsing', 'Input should be a valid decimal')

        if not self.allow_inf_nan or self.check_digits:
            _1, digit_tuple, exponent = value.as_tuple()
            if not self.allow_inf_nan and exponent in {'F', 'n', 'N'}:
                raise PydanticKnownError('finite_number')

            if self.check_digits:
                if isinstance(exponent, str):
                    raise PydanticKnownError('finite_number')
                elif exponent >= 0:
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
            raise PydanticKnownError('greater_than', {'gt': self.gt})
        elif self.ge is not None and not value >= self.ge:
            raise PydanticKnownError('greater_than_equal', {'ge': self.ge})

        if self.lt is not None and not value < self.lt:
            raise PydanticKnownError('less_than', {'lt': self.lt})
        if self.le is not None and not value <= self.le:
            raise PydanticKnownError('less_than_equal', {'le': self.le})

        return value

    def __repr__(self) -> str:
        slots = [(k, getattr(self, k)) for k in self.__slots__]
        s = ', '.join(f'{k}={v!r}' for k, v in slots if v is not None)
        return f'DecimalValidator({s})'


def uuid_validator(__input_value: str | bytes, _: core_schema.ValidationInfo) -> UUID:
    try:
        if isinstance(__input_value, str):
            return UUID(__input_value)
        else:
            try:
                return UUID(__input_value.decode())
            except ValueError:
                # 16 bytes in big-endian order as the bytes argument fail
                # the above check
                return UUID(bytes=__input_value)
    except ValueError:
        raise PydanticCustomError('uuid_parsing', 'Input should be a valid UUID, unable to parse string as an UUID')


def path_validator(__input_value: str, _: core_schema.ValidationInfo) -> Path:
    try:
        return Path(__input_value)
    except TypeError:
        raise PydanticCustomError('path_type', 'Input is not a valid path')


def pattern_either_validator(__input_value: Any, _: core_schema.ValidationInfo) -> typing.Pattern[Any]:
    if isinstance(__input_value, typing.Pattern):
        return __input_value
    elif isinstance(__input_value, (str, bytes)):
        # todo strict mode
        return compile_pattern(__input_value)
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_str_validator(__input_value: Any, _: core_schema.ValidationInfo) -> typing.Pattern[str]:
    if isinstance(__input_value, typing.Pattern):
        if isinstance(__input_value.pattern, str):
            return __input_value
        else:
            raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    elif isinstance(__input_value, str):
        return compile_pattern(__input_value)
    elif isinstance(__input_value, bytes):
        raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_bytes_validator(__input_value: Any, _: core_schema.ValidationInfo) -> Any:
    if isinstance(__input_value, typing.Pattern):
        if isinstance(__input_value.pattern, bytes):
            return __input_value
        else:
            raise PydanticCustomError('pattern_bytes_type', 'Input should be a bytes pattern')
    elif isinstance(__input_value, bytes):
        return compile_pattern(__input_value)
    elif isinstance(__input_value, str):
        raise PydanticCustomError('pattern_bytes_type', 'Input should be a bytes pattern')
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


PatternType = typing.TypeVar('PatternType', str, bytes)


def compile_pattern(pattern: PatternType) -> typing.Pattern[PatternType]:
    try:
        return re.compile(pattern)
    except re.error:
        raise PydanticCustomError('pattern_regex', 'Input should be a valid regular expression')


def deque_any_validator(
    __input_value: Any, validator: core_schema.ValidatorFunctionWrapHandler, _: core_schema.ValidationInfo
) -> deque[Any]:
    if isinstance(__input_value, deque):
        return __input_value
    else:
        return deque(validator(__input_value))


def deque_typed_validator(__input_value: list[Any], _: core_schema.ValidationInfo) -> deque[Any]:
    return deque(__input_value)


def ordered_dict_any_validator(
    __input_value: Any, validator: core_schema.ValidatorFunctionWrapHandler, _: core_schema.ValidationInfo
) -> OrderedDict[Any, Any]:
    if isinstance(__input_value, OrderedDict):
        return __input_value
    else:
        return OrderedDict(validator(__input_value))


def ordered_dict_typed_validator(__input_value: list[Any], _: core_schema.ValidationInfo) -> OrderedDict[Any, Any]:
    return OrderedDict(__input_value)


def ip_v4_address_validator(__input_value: Any, _: core_schema.ValidationInfo) -> IPv4Address:
    if isinstance(__input_value, IPv4Address):
        return __input_value

    try:
        return IPv4Address(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_address', 'Input is not a valid IPv4 address')


def ip_v6_address_validator(__input_value: Any, _: core_schema.ValidationInfo) -> IPv6Address:
    if isinstance(__input_value, IPv6Address):
        return __input_value

    try:
        return IPv6Address(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_address', 'Input is not a valid IPv6 address')


def ip_v4_network_validator(__input_value: Any, _: core_schema.ValidationInfo) -> IPv4Network:
    """
    Assume IPv4Network initialised with a default ``strict`` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv4Network
    """
    if isinstance(__input_value, IPv4Network):
        return __input_value

    try:
        return IPv4Network(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_network', 'Input is not a valid IPv4 network')


def ip_v6_network_validator(__input_value: Any, _: core_schema.ValidationInfo) -> IPv6Network:
    """
    Assume IPv6Network initialised with a default ``strict`` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv6Network
    """
    if isinstance(__input_value, IPv6Network):
        return __input_value

    try:
        return IPv6Network(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_network', 'Input is not a valid IPv6 network')


def ip_v4_interface_validator(__input_value: Any, _: core_schema.ValidationInfo) -> IPv4Interface:
    if isinstance(__input_value, IPv4Interface):
        return __input_value

    try:
        return IPv4Interface(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_interface', 'Input is not a valid IPv4 interface')


def ip_v6_interface_validator(__input_value: Any, _: core_schema.ValidationInfo) -> IPv6Interface:
    if isinstance(__input_value, IPv6Interface):
        return __input_value

    try:
        return IPv6Interface(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_interface', 'Input is not a valid IPv6 interface')
