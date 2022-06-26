from __future__ import annotations

import sys
from datetime import date, datetime, time
from typing import Any, Callable, Dict, List, Sequence, Union

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required
else:
    from typing import NotRequired

if sys.version_info < (3, 8):
    from typing_extensions import Literal, TypedDict
else:
    from typing import Literal, TypedDict


class AnySchema(TypedDict):
    type: Literal['any']


class BoolSchema(TypedDict):
    type: Literal['bool']
    strict: NotRequired[bool]


class ConfigSchema(TypedDict, total=False):
    strict: bool
    extra_behavior: Literal['allow', 'forbid', 'ignore']
    model_full: bool  # default: True
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    from_attributes: bool


class DictSchema(TypedDict, total=False):
    type: Required[Literal['dict']]
    keys_schema: Schema  # default: AnySchema
    values_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool


class FloatSchema(TypedDict, total=False):
    type: Required[Literal['float']]
    multiple_of: float
    le: float
    ge: float
    lt: float
    gt: float
    strict: bool
    default: float


class FunctionSchema(TypedDict):
    type: Literal['function']
    mode: Literal['before', 'after', 'wrap']
    function: Callable[..., Any]
    schema: Schema


class FunctionPlainSchema(TypedDict):
    type: Literal['function']
    mode: Literal['plain']
    function: Callable[..., Any]


class IntSchema(TypedDict, total=False):
    type: Required[Literal['int']]
    multiple_of: int
    le: int
    ge: int
    lt: int
    gt: int
    strict: bool


class ListSchema(TypedDict, total=False):
    type: Required[Literal['list']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool


class LiteralSchema(TypedDict):
    type: Literal['literal']
    expected: Sequence[Any]


class ModelClassSchema(TypedDict):
    type: Literal['model-class']
    class_type: type
    schema: TypedDictSchema


class TypedDictField(TypedDict, total=False):
    schema: Required[Schema]
    required: bool
    default: Any
    alias: str
    aliases: List[List[Union[str, int]]]


class TypedDictSchema(TypedDict):
    type: Literal['typed-dict']
    fields: Dict[str, TypedDictField]
    extra_validator: NotRequired[Schema]
    config: NotRequired[ConfigSchema]
    return_fields_set: NotRequired[bool]


class NoneSchema(TypedDict):
    type: Literal['none']


class NullableSchema(TypedDict):
    type: Literal['nullable']
    schema: Schema
    strict: NotRequired[bool]


class RecursiveReferenceSchema(TypedDict):
    type: Literal['recursive-ref']
    name: str


class RecursiveContainerSchema(TypedDict):
    type: Literal['recursive-container']
    name: str
    schema: Schema


class SetSchema(TypedDict, total=False):
    type: Required[Literal['set']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool


class FrozenSetSchema(TypedDict, total=False):
    type: Required[Literal['frozenset']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool


class StringSchema(TypedDict, total=False):
    type: Required[Literal['str']]
    pattern: str
    max_length: int
    min_length: int
    strip_whitespace: bool
    to_lower: bool
    to_upper: bool
    strict: bool


class UnionSchema(TypedDict):
    type: Literal['union']
    choices: List[Schema]
    strict: NotRequired[bool]
    default: NotRequired[Any]


class BytesSchema(TypedDict, total=False):
    type: Required[Literal['bytes']]
    max_length: int
    min_length: int
    strict: bool


class DateSchema(TypedDict, total=False):
    type: Required[Literal['date']]
    strict: bool
    le: date
    ge: date
    lt: date
    gt: date
    default: date


class TimeSchema(TypedDict, total=False):
    type: Required[Literal['time']]
    strict: bool
    le: time
    ge: time
    lt: time
    gt: time
    default: time


class DatetimeSchema(TypedDict, total=False):
    type: Required[Literal['datetime']]
    strict: bool
    le: datetime
    ge: datetime
    lt: datetime
    gt: datetime
    default: datetime


class TupleFixLenSchema(TypedDict):
    type: Literal['tuple-fix-len']
    items_schema: List[Schema]
    strict: NotRequired[bool]


class TupleVarLenSchema(TypedDict, total=False):
    type: Required[Literal['tuple-var-len']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool


# pydantic allows types to be defined via a simple string instead of dict with just `type`, e.g.
# 'int' is equivalent to {'type': 'int'}
BareType = Literal[
    'any',
    'bool',
    'bytes',
    'dict',
    'float',
    'function',
    'int',
    'list',
    'model',
    'model-class',
    'none',
    'nullable',
    'recursive-container',
    'recursive-reference',
    'set',
    'str',
    # tuple-fix-len cannot be created without more typing information
    'tuple-var-len',
    'union',
]

Schema = Union[
    BareType,
    AnySchema,
    BoolSchema,
    BytesSchema,
    DictSchema,
    FloatSchema,
    FunctionSchema,
    FunctionPlainSchema,
    IntSchema,
    ListSchema,
    LiteralSchema,
    TypedDictSchema,
    ModelClassSchema,
    NoneSchema,
    NullableSchema,
    RecursiveContainerSchema,
    RecursiveReferenceSchema,
    SetSchema,
    FrozenSetSchema,
    StringSchema,
    TupleFixLenSchema,
    TupleVarLenSchema,
    UnionSchema,
    DateSchema,
    TimeSchema,
    DatetimeSchema,
]
