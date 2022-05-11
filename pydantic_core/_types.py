from __future__ import annotations

import sys
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
    extra: Literal['allow', 'forbid', 'ignore']


class DictSchema(TypedDict, total=False):
    type: Required[Literal['dict']]
    keys: Schema  # default: AnySchema
    values: Schema  # default: AnySchema
    min_items: int
    max_items: int


class FloatSchema(TypedDict, total=False):
    type: Required[Literal['float']]
    multiple_of: float
    le: float
    ge: float
    lt: float
    gt: float
    strict: bool
    default: float


# TODO: function could be typed based on mode
class FunctionSchema(TypedDict):
    type: Literal['function']
    mode: Literal['before', 'after', 'plain', 'wrap']
    function: Callable[..., Any]
    schema: NotRequired[Schema]


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
    items: Schema  # default: AnySchema
    min_items: int
    max_items: int


class LiteralSchema(TypedDict):
    type: Literal['literal']
    expected: Sequence[Any]


class ModelClassSchema(TypedDict):
    type: Literal['model-class']
    class_type: type
    model: ModelSchema


class ModelSchema(TypedDict):
    type: Literal['model']
    fields: Dict[str, Schema]
    name: NotRequired[str]
    extra_validator: NotRequired[Schema]
    config: NotRequired[ConfigSchema]


class NoneSchema(TypedDict):
    type: Literal['none']


class OptionalSchema(TypedDict):
    type: Literal['optional']
    schema: Schema
    strict: NotRequired[bool]


class RecursiveReferenceSchema(TypedDict):
    type: Literal['recursive-ref']
    name: str


class RecursiveContainerSchema(TypedDict):
    type: Literal['recursive-container']
    name: str
    schema: Schema


class SetSchema(TypedDict):
    type: Literal['set']
    items: Schema
    min_items: NotRequired[int]
    max_items: NotRequired[int]
    strict: NotRequired[bool]


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


# pydantic allows types to be defined via a simple string instead of dict with just `type`, e.g.
# 'int' is equivalent to {'type': 'int'}
BareType = Literal[
    'any',
    'bool',
    'dict',
    'float',
    'function',
    'int',
    'list',
    'model',
    'model-class',
    'none',
    'optional',
    'recursive-container',
    'recursive-reference',
    'set',
    'str',
    'union',
]

Schema = Union[
    BareType,
    AnySchema,
    BoolSchema,
    DictSchema,
    FloatSchema,
    FunctionSchema,
    IntSchema,
    ListSchema,
    LiteralSchema,
    ModelSchema,
    ModelClassSchema,
    NoneSchema,
    OptionalSchema,
    RecursiveContainerSchema,
    RecursiveReferenceSchema,
    SetSchema,
    StringSchema,
    UnionSchema,
]
