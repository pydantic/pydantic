from __future__ import annotations

import sys
from datetime import date, datetime, time
from typing import Any, Callable, Dict, List, Type, Union

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required
else:
    from typing import NotRequired, Required

if sys.version_info < (3, 8):
    from typing_extensions import Literal, TypedDict
else:
    from typing import Literal, TypedDict


class AnySchema(TypedDict):
    type: Literal['any']


class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str


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
    ref: str


class FloatSchema(TypedDict, total=False):
    type: Required[Literal['float']]
    multiple_of: float
    le: float
    ge: float
    lt: float
    gt: float
    strict: bool
    ref: str


class FunctionSchema(TypedDict):
    type: Literal['function']
    mode: Literal['before', 'after', 'wrap']
    function: Callable[..., Any]
    schema: Schema
    ref: NotRequired[str]


class FunctionPlainSchema(TypedDict):
    type: Literal['function']
    mode: Literal['plain']
    function: Callable[..., Any]
    ref: NotRequired[str]


class IntSchema(TypedDict, total=False):
    type: Required[Literal['int']]
    multiple_of: int
    le: int
    ge: int
    lt: int
    gt: int
    strict: bool
    ref: str


class ListSchema(TypedDict, total=False):
    type: Required[Literal['list']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool
    ref: str


class LiteralSchema(TypedDict):
    type: Literal['literal']
    expected: List[Any]
    ref: NotRequired[str]


class ModelClassSchema(TypedDict):
    type: Literal['model-class']
    class_type: type
    schema: TypedDictSchema
    ref: NotRequired[str]


class TypedDictField(TypedDict, total=False):
    schema: Required[Schema]
    required: bool
    default: Any
    alias: str
    aliases: List[List[Union[str, int]]]


class TypedDictSchema(TypedDict, total=False):
    type: Required[Literal['typed-dict']]
    fields: Required[Dict[str, TypedDictField]]
    extra_validator: Schema
    config: ConfigSchema
    return_fields_set: bool
    ref: str


class NoneSchema(TypedDict):
    type: Literal['none']
    ref: NotRequired[str]


class NullableSchema(TypedDict, total=False):
    type: Required[Literal['nullable']]
    schema: Required[Schema]
    strict: bool
    ref: str


class RecursiveReferenceSchema(TypedDict):
    type: Literal['recursive-ref']
    schema_ref: str


class SetSchema(TypedDict, total=False):
    type: Required[Literal['set']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool
    ref: str


class FrozenSetSchema(TypedDict, total=False):
    type: Required[Literal['frozenset']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool
    ref: str


class StringSchema(TypedDict, total=False):
    type: Required[Literal['str']]
    pattern: str
    max_length: int
    min_length: int
    strip_whitespace: bool
    to_lower: bool
    to_upper: bool
    strict: bool
    ref: str


class UnionSchema(TypedDict, total=False):
    type: Required[Literal['union']]
    choices: Required[List[Schema]]
    strict: bool
    ref: str


class BytesSchema(TypedDict, total=False):
    type: Required[Literal['bytes']]
    max_length: int
    min_length: int
    strict: bool
    ref: str


class DateSchema(TypedDict, total=False):
    type: Required[Literal['date']]
    strict: bool
    le: date
    ge: date
    lt: date
    gt: date
    ref: str


class TimeSchema(TypedDict, total=False):
    type: Required[Literal['time']]
    strict: bool
    le: time
    ge: time
    lt: time
    gt: time
    ref: str


class DatetimeSchema(TypedDict, total=False):
    type: Required[Literal['datetime']]
    strict: bool
    le: datetime
    ge: datetime
    lt: datetime
    gt: datetime
    ref: str


class TupleFixLenSchema(TypedDict, total=False):
    type: Required[Literal['tuple-fix-len']]
    items_schema: Required[List[Schema]]
    strict: bool
    ref: str


class TupleVarLenSchema(TypedDict, total=False):
    type: Required[Literal['tuple-var-len']]
    items_schema: Schema  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool
    ref: str


class IsInstanceSchema(TypedDict):
    type: Literal['is-instance']
    class_: Type[Any]


class CallableSchema(TypedDict):
    type: Literal['callable']


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
    'callable',
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
    IsInstanceSchema,
    CallableSchema,
]
