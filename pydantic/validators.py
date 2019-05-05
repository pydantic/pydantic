import re
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum, IntEnum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Pattern, Set, Tuple, Type, TypeVar, Union, cast
from uuid import UUID

from . import errors
from .datetime_parse import parse_date, parse_datetime, parse_duration, parse_time
from .utils import AnyCallable, AnyType, ForwardRef, change_exception, display_as_type, is_callable_type, sequence_like

if TYPE_CHECKING:  # pragma: no cover
    from .fields import Field
    from .main import BaseConfig
    from .types import ConstrainedDecimal, ConstrainedFloat, ConstrainedInt

    ConstrainedNumber = Union[ConstrainedDecimal, ConstrainedFloat, ConstrainedInt]
    AnyOrderedDict = OrderedDict[Any, Any]
    Number = Union[int, float, Decimal]
    StrBytes = Union[str, bytes]

NoneType = type(None)


def not_none_validator(v: Any) -> Any:
    if v is None:
        raise errors.NoneIsNotAllowedError()
    return v


def is_none_validator(v: Any) -> None:
    if v is not None:
        raise errors.NoneIsAllowedError()


def str_validator(v: Any) -> str:
    if isinstance(v, (str, NoneType)):  # type: ignore
        return v
    elif isinstance(v, (bytes, bytearray)):
        return v.decode()
    elif isinstance(v, (float, int, Decimal)):
        # is there anything else we want to add here? If you think so, create an issue.
        return str(v)
    else:
        raise errors.StrError()


def bytes_validator(v: Any) -> bytes:
    if isinstance(v, bytes):
        return v
    elif isinstance(v, bytearray):
        return bytes(v)
    elif isinstance(v, str):
        return v.encode()
    elif isinstance(v, (float, int, Decimal)):
        return str(v).encode()
    else:
        raise errors.BytesError()


BOOL_STRINGS = {'1', 'TRUE', 'ON', 'YES'}


def bool_validator(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, bytes):
        v = v.decode()
    if isinstance(v, str):
        return v.upper() in BOOL_STRINGS
    return bool(v)


def int_validator(v: Any) -> int:
    if not isinstance(v, bool) and isinstance(v, int):
        return v

    with change_exception(errors.IntegerError, TypeError, ValueError):
        return int(v)


def float_validator(v: Any) -> float:
    if isinstance(v, float):
        return v

    with change_exception(errors.FloatError, TypeError, ValueError):
        return float(v)


def number_multiple_validator(v: 'Number', field: 'Field') -> 'Number':
    field_type = cast('ConstrainedNumber', field.type_)
    if field_type.multiple_of is not None and v % field_type.multiple_of != 0:  # type: ignore
        raise errors.NumberNotMultipleError(multiple_of=field_type.multiple_of)

    return v


def number_size_validator(v: 'Number', field: 'Field') -> 'Number':
    field_type = cast('ConstrainedNumber', field.type_)
    if field_type.gt is not None and not v > field_type.gt:
        raise errors.NumberNotGtError(limit_value=field_type.gt)
    elif field_type.ge is not None and not v >= field_type.ge:
        raise errors.NumberNotGeError(limit_value=field_type.ge)

    if field_type.lt is not None and not v < field_type.lt:
        raise errors.NumberNotLtError(limit_value=field_type.lt)
    if field_type.le is not None and not v <= field_type.le:
        raise errors.NumberNotLeError(limit_value=field_type.le)

    return v


def constant_validator(v: 'Any', field: 'Field') -> 'Any':
    """Validate ``const`` fields.

    The value provided for a ``const`` field must be equal to the default value
    of the field. This is to support the keyword of the same name in JSON
    Schema.
    """
    if v != field.default:
        raise errors.WrongConstantError(given=v, const=field.default)

    return v


def anystr_length_validator(v: 'StrBytes', field: 'Field', config: 'BaseConfig') -> 'StrBytes':
    v_len = len(v)

    min_length = getattr(field.type_, 'min_length', config.min_anystr_length)
    if min_length is not None and v_len < min_length:
        raise errors.AnyStrMinLengthError(limit_value=min_length)

    max_length = getattr(field.type_, 'max_length', config.max_anystr_length)
    if max_length is not None and v_len > max_length:
        raise errors.AnyStrMaxLengthError(limit_value=max_length)

    return v


def anystr_strip_whitespace(v: 'StrBytes', field: 'Field', config: 'BaseConfig') -> 'StrBytes':
    strip_whitespace = getattr(field.type_, 'strip_whitespace', config.anystr_strip_whitespace)
    if strip_whitespace:
        v = v.strip()

    return v


def ordered_dict_validator(v: Any) -> 'AnyOrderedDict':
    if isinstance(v, OrderedDict):
        return v

    with change_exception(errors.DictError, TypeError, ValueError):
        return OrderedDict(v)


def dict_validator(v: Any) -> Dict[Any, Any]:
    if isinstance(v, dict):
        return v

    with change_exception(errors.DictError, TypeError, ValueError):
        return dict(v)


def list_validator(v: Any) -> List[Any]:
    if isinstance(v, list):
        return v
    elif sequence_like(v):
        return list(v)
    else:
        raise errors.ListError()


def tuple_validator(v: Any) -> Tuple[Any, ...]:
    if isinstance(v, tuple):
        return v
    elif sequence_like(v):
        return tuple(v)
    else:
        raise errors.TupleError()


def set_validator(v: Any) -> Set[Any]:
    if isinstance(v, set):
        return v
    elif sequence_like(v):
        return set(v)
    else:
        raise errors.SetError()


def enum_validator(v: Any, field: 'Field', config: 'BaseConfig') -> Enum:
    with change_exception(errors.EnumError, ValueError):
        enum_v = field.type_(v)

    return enum_v.value if config.use_enum_values else enum_v


def uuid_validator(v: Any, field: 'Field') -> UUID:
    with change_exception(errors.UUIDError, ValueError):
        if isinstance(v, str):
            v = UUID(v)
        elif isinstance(v, (bytes, bytearray)):
            v = UUID(v.decode())

    if not isinstance(v, UUID):
        raise errors.UUIDError()

    required_version = getattr(field.type_, '_required_version', None)
    if required_version and v.version != required_version:
        raise errors.UUIDVersionError(required_version=required_version)

    return v


def decimal_validator(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    elif isinstance(v, (bytes, bytearray)):
        v = v.decode()

    v = str(v).strip()

    with change_exception(errors.DecimalError, DecimalException):
        v = Decimal(v)

    if not v.is_finite():
        raise errors.DecimalIsNotFiniteError()

    return v


def ip_v4_address_validator(v: Any) -> IPv4Address:
    if isinstance(v, IPv4Address):
        return v

    with change_exception(errors.IPv4AddressError, ValueError):
        return IPv4Address(v)


def ip_v6_address_validator(v: Any) -> IPv6Address:
    if isinstance(v, IPv6Address):
        return v

    with change_exception(errors.IPv6AddressError, ValueError):
        return IPv6Address(v)


def ip_v4_network_validator(v: Any) -> IPv4Network:
    """
    Assume IPv4Network initialised with a default ``strict`` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv4Network
    """
    if isinstance(v, IPv4Network):
        return v

    with change_exception(errors.IPv4NetworkError, ValueError):
        return IPv4Network(v)


def ip_v6_network_validator(v: Any) -> IPv6Network:
    """
    Assume IPv6Network initialised with a default ``strict`` argument

    See more:
    https://docs.python.org/library/ipaddress.html#ipaddress.IPv6Network
    """
    if isinstance(v, IPv6Network):
        return v

    with change_exception(errors.IPv6NetworkError, ValueError):
        return IPv6Network(v)


def ip_v4_interface_validator(v: Any) -> IPv4Interface:
    if isinstance(v, IPv4Interface):
        return v

    with change_exception(errors.IPv4InterfaceError, ValueError):
        return IPv4Interface(v)


def ip_v6_interface_validator(v: Any) -> IPv6Interface:
    if isinstance(v, IPv6Interface):
        return v

    with change_exception(errors.IPv6InterfaceError, ValueError):
        return IPv6Interface(v)


def path_validator(v: Any) -> Path:
    if isinstance(v, Path):
        return v

    with change_exception(errors.PathError, TypeError):
        return Path(v)


def path_exists_validator(v: Any) -> Path:
    if not v.exists():
        raise errors.PathNotExistsError(path=v)

    return v


def callable_validator(v: Any) -> AnyCallable:
    """
    Perform a simple check if the value is callable.

    Note: complete matching of argument type hints and return types is not performed
    """
    if callable(v):
        return v

    raise errors.CallableError(value=v)


T = TypeVar('T')


def make_arbitrary_type_validator(type_: Type[T]) -> Callable[[T], T]:
    def arbitrary_type_validator(v: Any) -> T:
        if isinstance(v, type_):
            return v
        raise errors.ArbitraryTypeError(expected_arbitrary_type=type_)

    return arbitrary_type_validator


def pattern_validator(v: Any) -> Pattern[str]:
    with change_exception(errors.PatternError, re.error):
        return re.compile(v)


pattern_validators = [not_none_validator, str_validator, pattern_validator]
# order is important here, for example: bool is a subclass of int so has to come first, datetime before date same,
# IPv4Interface before IPv4Address, etc
_VALIDATORS: List[Tuple[AnyType, List[AnyCallable]]] = [
    (IntEnum, [int_validator, enum_validator]),
    (Enum, [enum_validator]),
    (str, [not_none_validator, str_validator, anystr_strip_whitespace, anystr_length_validator]),
    (bytes, [not_none_validator, bytes_validator, anystr_strip_whitespace, anystr_length_validator]),
    (bool, [bool_validator]),
    (int, [int_validator]),
    (float, [float_validator]),
    (NoneType, [is_none_validator]),  # type: ignore
    (Path, [path_validator]),
    (datetime, [parse_datetime]),
    (date, [parse_date]),
    (time, [parse_time]),
    (timedelta, [parse_duration]),
    (OrderedDict, [ordered_dict_validator]),
    (dict, [dict_validator]),
    (list, [list_validator]),
    (tuple, [tuple_validator]),
    (set, [set_validator]),
    (UUID, [not_none_validator, uuid_validator]),
    (Decimal, [not_none_validator, decimal_validator]),
    (IPv4Interface, [not_none_validator, ip_v4_interface_validator]),
    (IPv6Interface, [not_none_validator, ip_v6_interface_validator]),
    (IPv4Address, [not_none_validator, ip_v4_address_validator]),
    (IPv6Address, [not_none_validator, ip_v6_address_validator]),
    (IPv4Network, [not_none_validator, ip_v4_network_validator]),
    (IPv6Network, [not_none_validator, ip_v6_network_validator]),
]


def find_validators(type_: AnyType, arbitrary_types_allowed: bool = False) -> List[AnyCallable]:
    if type_ is Any or type(type_) == ForwardRef:
        return []
    if type_ is Pattern:
        return pattern_validators
    if is_callable_type(type_):
        return [callable_validator]

    supertype = _find_supertype(type_)
    if supertype is not None:
        type_ = supertype

    for val_type, validators in _VALIDATORS:
        try:
            if issubclass(type_, val_type):
                return validators
        except TypeError as e:
            raise RuntimeError(f'error checking inheritance of {type_!r} (type: {display_as_type(type_)})') from e

    if arbitrary_types_allowed:
        return [make_arbitrary_type_validator(type_)]
    else:
        raise RuntimeError(f'no validator found for {type_}')


def _find_supertype(type_: AnyType) -> Optional[AnyType]:
    if not _is_new_type(type_):
        return None

    supertype = type_.__supertype__
    if _is_new_type(supertype):
        supertype = _find_supertype(supertype)

    return supertype


def _is_new_type(type_: AnyType) -> bool:
    return hasattr(type_, '__name__') and hasattr(type_, '__supertype__')
