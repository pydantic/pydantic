import re
import sys
from collections import OrderedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, DecimalException
from enum import Enum, IntEnum
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Pattern,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

from . import errors
from .datetime_parse import parse_date, parse_datetime, parse_duration, parse_time
from .utils import (
    AnyCallable,
    AnyType,
    ForwardRef,
    almost_equal_floats,
    change_exception,
    display_as_type,
    is_callable_type,
    is_literal_type,
    sequence_like,
)

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


def str_validator(v: Any) -> Optional[str]:
    if isinstance(v, str):
        if isinstance(v, Enum):
            return v.value
        else:
            return v
    elif v is None:
        return None
    elif isinstance(v, (float, int, Decimal)):
        # is there anything else we want to add here? If you think so, create an issue.
        return str(v)
    elif isinstance(v, (bytes, bytearray)):
        return v.decode()
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
    if isinstance(v, int) and not isinstance(v, bool):
        return v

    with change_exception(errors.IntegerError, TypeError, ValueError):
        return int(v)


def float_validator(v: Any) -> float:
    if isinstance(v, float):
        return v

    with change_exception(errors.FloatError, TypeError, ValueError):
        return float(v)


def number_multiple_validator(v: 'Number', field: 'Field') -> 'Number':
    field_type: ConstrainedNumber = field.type_  # type: ignore
    if field_type.multiple_of is not None:
        mod = float(v) / float(field_type.multiple_of) % 1
        if not almost_equal_floats(mod, 0.0) and not almost_equal_floats(mod, 1.0):
            raise errors.NumberNotMultipleError(multiple_of=field_type.multiple_of)
    return v


def number_size_validator(v: 'Number', field: 'Field') -> 'Number':
    field_type: ConstrainedNumber = field.type_  # type: ignore
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
        raise errors.WrongConstantError(given=v, permitted=[field.default])

    return v


def anystr_length_validator(v: 'StrBytes', field: 'Field', config: 'BaseConfig') -> 'StrBytes':
    v_len = len(v)

    min_length = config.min_anystr_length
    if min_length is not None and v_len < min_length:
        raise errors.AnyStrMinLengthError(limit_value=min_length)

    max_length = config.max_anystr_length
    if max_length is not None and v_len > max_length:
        raise errors.AnyStrMaxLengthError(limit_value=max_length)

    return v


def anystr_strip_whitespace(v: 'StrBytes', field: 'Field', config: 'BaseConfig') -> 'StrBytes':
    return v.strip()


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
    try:
        enum_v = field.type_(v)
    except ValueError:
        # field.type_ should be an enum, so will be iterable
        raise errors.EnumError(enum_values=list(field.type_))  # type: ignore
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


def make_literal_validator(type_: Any) -> Callable[[Any], Any]:
    if sys.version_info >= (3, 7):
        permitted_choices = type_.__args__
    else:
        permitted_choices = type_.__values__
    allowed_choices_set = set(permitted_choices)

    def literal_validator(v: Any) -> Any:
        if v not in allowed_choices_set:
            raise errors.WrongConstantError(given=v, permitted=permitted_choices)
        return v

    return literal_validator


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


class IfConfig:
    def __init__(self, validator: AnyCallable, *config_attr_names: str) -> None:
        self.validator = validator
        self.config_attr_names = config_attr_names

    def check(self, config: Type['BaseConfig']) -> bool:
        return any(getattr(config, name) not in {None, False} for name in self.config_attr_names)


pattern_validators = [not_none_validator, str_validator, pattern_validator]
# order is important here, for example: bool is a subclass of int so has to come first, datetime before date same,
# IPv4Interface before IPv4Address, etc
_VALIDATORS: List[Tuple[AnyType, List[Any]]] = [
    (IntEnum, [int_validator, enum_validator]),
    (Enum, [enum_validator]),
    (
        str,
        [
            not_none_validator,
            str_validator,
            IfConfig(anystr_strip_whitespace, 'anystr_strip_whitespace'),
            IfConfig(anystr_length_validator, 'min_anystr_length', 'max_anystr_length'),
        ],
    ),
    (
        bytes,
        [
            not_none_validator,
            bytes_validator,
            IfConfig(anystr_strip_whitespace, 'anystr_strip_whitespace'),
            IfConfig(anystr_length_validator, 'min_anystr_length', 'max_anystr_length'),
        ],
    ),
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


def find_validators(  # noqa: C901 (ignore complexity)
    type_: AnyType, config: Type['BaseConfig']
) -> Generator[AnyCallable, None, None]:
    if type_ is Any:
        return
    type_type = type(type_)
    if type_type == ForwardRef or type_type == TypeVar:
        return
    if type_ is Pattern:
        yield from pattern_validators
        return
    if is_callable_type(type_):
        yield callable_validator
        return
    if is_literal_type(type_):
        yield make_literal_validator(type_)
        return

    supertype = _find_supertype(type_)
    if supertype is not None:
        type_ = supertype

    for val_type, validators in _VALIDATORS:
        try:
            if issubclass(type_, val_type):
                for v in validators:
                    if isinstance(v, IfConfig):
                        if v.check(config):
                            yield v.validator
                    else:
                        yield v
                return
        except TypeError as e:
            raise RuntimeError(f'error checking inheritance of {type_!r} (type: {display_as_type(type_)})') from e

    if config.arbitrary_types_allowed:
        yield make_arbitrary_type_validator(type_)
    else:
        raise RuntimeError(
            f'no validator found for {type_} see `keep_untouched` or `arbitrary_types_allowed` in Config'
        )


def _find_supertype(type_: AnyType) -> Optional[AnyType]:
    if not _is_new_type(type_):
        return None

    supertype = type_.__supertype__
    if _is_new_type(supertype):
        supertype = _find_supertype(supertype)

    return supertype


def _is_new_type(type_: AnyType) -> bool:
    return hasattr(type_, '__name__') and hasattr(type_, '__supertype__')
