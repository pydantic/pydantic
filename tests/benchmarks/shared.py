from collections import deque
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum, IntEnum
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)
from pathlib import Path
from re import Pattern
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    FrozenSet,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)
from uuid import UUID, uuid4, uuid5

from typing_extensions import Literal, TypedDict

from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    Base64Bytes,
    Base64Str,
    Base64UrlBytes,
    Base64UrlStr,
    BaseModel,
    ByteSize,
    DirectoryPath,
    FilePath,
    FiniteFloat,
    FutureDate,
    ImportString,
    Json,
    JsonValue,
    NegativeFloat,
    NegativeInt,
    NewPath,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    OnErrorOmit,
    PastDate,
    PastDatetime,
    PositiveFloat,
    PositiveInt,
    Secret,
    SecretBytes,
    SecretStr,
    StrictBool,
)


class SimpleModel(BaseModel):
    field1: str
    field2: int
    field3: float


class NestedModel(BaseModel):
    field1: str
    field2: List[int]
    field3: Dict[str, float]


class OuterModel(BaseModel):
    nested: NestedModel
    optional_nested: Optional[NestedModel]


class ComplexModel(BaseModel):
    field1: Union[str, int, float]
    field2: List[Dict[str, Union[int, float]]]
    field3: Optional[List[Union[str, int]]]


class Color(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'


class ToolEnum(IntEnum):
    spanner = 1
    wrench = 2
    screwdriver = 3


class Point(NamedTuple):
    x: int
    y: int


class User(TypedDict):
    name: str
    id: int


class Foo:
    pass


StdLibTypes = [
    deque,  # collections.deque
    Deque[str],  # typing.Deque
    Deque[int],  # typing.Deque
    Deque[float],  # typing.Deque
    Deque[bytes],  # typing.Deque
    str,  # str
    int,  # int
    float,  # float
    complex,  # complex
    bool,  # bool
    bytes,  # bytes
    date,  # datetime.date
    datetime,  # datetime.datetime
    time,  # datetime.time
    timedelta,  # datetime.timedelta
    Decimal,  # decimal.Decimal
    Color,  # enum
    ToolEnum,  # int enum
    IPv4Address,  # ipaddress.IPv4Address
    IPv6Address,  # ipaddress.IPv6Address
    IPv4Interface,  # ipaddress.IPv4Interface
    IPv6Interface,  # ipaddress.IPv6Interface
    IPv4Network,  # ipaddress.IPv4Network
    IPv6Network,  # ipaddress.IPv6Network
    Path,  # pathlib.Path
    Pattern,  # typing.Pattern
    UUID,  # uuid.UUID
    uuid4,  # uuid.uuid4
    uuid5,  # uuid.uuid5
    Point,  # named tuple
    list,  # built-in list
    List[int],  # typing.List
    List[str],  # typing.List
    List[bytes],  # typing.List
    List[float],  # typing.List
    dict,  # built-in dict
    Dict[str, float],  # typing.Dict
    Dict[str, bytes],  # typing.Dict
    Dict[str, int],  # typing.Dict
    Dict[str, str],  # typing.Dict
    User,  # TypedDict
    tuple,  # tuple
    Tuple[int, str, float],  # typing.Tuple
    set,  # built-in set
    Set[int],  # typing.Set
    Set[str],  # typing.Set
    frozenset,  # built-in frozenset
    FrozenSet[int],  # typing.FrozenSet
    FrozenSet[str],  # typing.FrozenSet
    Optional[int],  # typing.Optional
    Optional[str],  # typing.Optional
    Optional[float],  # typing.Optional
    Optional[bytes],  # typing.Optional
    Optional[bool],  # typing.Optional
    Sequence[int],  # typing.Sequence
    Sequence[str],  # typing.Sequence
    Sequence[bytes],  # typing.Sequence
    Sequence[float],  # typing.Sequence
    Iterable[int],  # typing.Iterable
    Iterable[str],  # typing.Iterable
    Iterable[bytes],  # typing.Iterable
    Iterable[float],  # typing.Iterable
    Callable[[int], int],  # typing.Callable
    Callable[[str], str],  # typing.Callable
    Literal['apple', 'pumpkin'],  #
    Type[Foo],  # typing.Type
    Any,  # typing.Any
]

PydanticTypes = [
    StrictBool,
    PositiveInt,
    PositiveFloat,
    NegativeInt,
    NegativeFloat,
    NonNegativeInt,
    NonPositiveInt,
    NonNegativeFloat,
    NonPositiveFloat,
    FiniteFloat,
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    FilePath,
    DirectoryPath,
    NewPath,
    Base64Bytes,
    Base64Str,
    Base64UrlBytes,
    Base64UrlStr,
    JsonValue,
    OnErrorOmit,
    ImportString,
    Json[Any],
    Json[List[int]],
    Json[List[str]],
    Json[List[bytes]],
    Json[List[float]],
    Json[List[Any]],
    Secret[bool],
    Secret[int],
    Secret[float],
    Secret[str],
    Secret[bytes],
    SecretStr,
    SecretBytes,
    ByteSize,
    PastDate,
    FutureDate,
    PastDatetime,
]


class DeferredModel(BaseModel):
    model_config = {'defer_build': True}


def rebuild_model(model: Type[BaseModel]) -> None:
    model.model_rebuild(force=True, _types_namespace={})
