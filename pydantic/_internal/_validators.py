"""
Validator functions for standard library types.

Import of this module is deferred since it contains imports of many standard library modules.
"""

from __future__ import annotations as _annotations

import re
import typing
from collections import OrderedDict, defaultdict, deque
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Any
from uuid import UUID

from pydantic_core import PydanticCustomError, core_schema


def mapping_validator(
    __input_value: typing.Mapping[Any, Any],
    validator: core_schema.ValidatorFunctionWrapHandler,
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


def construct_counter(__input_value: typing.Mapping[Any, Any]) -> typing.Counter[Any]:
    """
    Validator for `Counter` types, if required `isinstance(v, Counter)` has already been called.
    """
    return typing.Counter(__input_value)


def sequence_validator(
    __input_value: typing.Sequence[Any],
    validator: core_schema.ValidatorFunctionWrapHandler,
) -> typing.Sequence[Any]:
    """
    Validator for `Sequence` types, isinstance(v, Sequence) has already been called.
    """
    value_type = type(__input_value)

    # We don't accept any plain string as a sequence
    # Relevant issue: https://github.com/pydantic/pydantic/issues/5595
    if issubclass(value_type, (str, bytes)):
        raise PydanticCustomError(
            'sequence_str',
            "'{type_name}' instances are not allowed as a Sequence value",
            {'type_name': value_type.__name__},
        )

    v_list = validator(__input_value)

    # the rest of the logic is just re-creating the original type from `v_list`
    if value_type == list:
        return v_list
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


def uuid_validator(__input_value: str | bytes) -> UUID:
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


def pattern_either_validator(__input_value: Any) -> typing.Pattern[Any]:
    if isinstance(__input_value, typing.Pattern):
        return __input_value  # type: ignore
    elif isinstance(__input_value, (str, bytes)):
        # todo strict mode
        return compile_pattern(__input_value)  # type: ignore
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_str_validator(__input_value: Any) -> typing.Pattern[str]:
    if isinstance(__input_value, typing.Pattern):
        if isinstance(__input_value.pattern, str):  # type: ignore
            return __input_value  # type: ignore
        else:
            raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    elif isinstance(__input_value, str):
        return compile_pattern(__input_value)
    elif isinstance(__input_value, bytes):
        raise PydanticCustomError('pattern_str_type', 'Input should be a string pattern')
    else:
        raise PydanticCustomError('pattern_type', 'Input should be a valid pattern')


def pattern_bytes_validator(__input_value: Any) -> Any:
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


def deque_any_validator(__input_value: Any, validator: core_schema.ValidatorFunctionWrapHandler) -> deque[Any]:
    if isinstance(__input_value, deque):
        return __input_value
    else:
        return deque(validator(__input_value))


def deque_typed_validator(__input_value: Any, validator: core_schema.ValidatorFunctionWrapHandler) -> deque[Any]:
    if isinstance(__input_value, deque):
        return deque(validator(__input_value), maxlen=__input_value.maxlen)
    else:
        return deque(validator(__input_value))


def ordered_dict_any_validator(
    __input_value: Any, validator: core_schema.ValidatorFunctionWrapHandler
) -> OrderedDict[Any, Any]:
    if isinstance(__input_value, OrderedDict):
        return __input_value
    else:
        return OrderedDict(validator(__input_value))


def ordered_dict_typed_validator(__input_value: list[Any]) -> OrderedDict[Any, Any]:
    return OrderedDict(__input_value)


def ip_v4_address_validator(__input_value: Any) -> IPv4Address:
    if isinstance(__input_value, IPv4Address):
        return __input_value

    try:
        return IPv4Address(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_address', 'Input is not a valid IPv4 address')


def ip_v6_address_validator(__input_value: Any) -> IPv6Address:
    if isinstance(__input_value, IPv6Address):
        return __input_value

    try:
        return IPv6Address(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_address', 'Input is not a valid IPv6 address')


def ip_v4_network_validator(__input_value: Any) -> IPv4Network:
    """
    Assume IPv4Network initialised with a default `strict` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv4Network
    """
    if isinstance(__input_value, IPv4Network):
        return __input_value

    try:
        return IPv4Network(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_network', 'Input is not a valid IPv4 network')


def ip_v6_network_validator(__input_value: Any) -> IPv6Network:
    """
    Assume IPv6Network initialised with a default `strict` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv6Network
    """
    if isinstance(__input_value, IPv6Network):
        return __input_value

    try:
        return IPv6Network(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_network', 'Input is not a valid IPv6 network')


def ip_v4_interface_validator(__input_value: Any) -> IPv4Interface:
    if isinstance(__input_value, IPv4Interface):
        return __input_value

    try:
        return IPv4Interface(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v4_interface', 'Input is not a valid IPv4 interface')


def ip_v6_interface_validator(__input_value: Any) -> IPv6Interface:
    if isinstance(__input_value, IPv6Interface):
        return __input_value

    try:
        return IPv6Interface(__input_value)
    except ValueError:
        raise PydanticCustomError('ip_v6_interface', 'Input is not a valid IPv6 interface')
