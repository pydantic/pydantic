from __future__ import annotations

import sys
from datetime import date, datetime, time, timedelta
from typing import Any, Callable, Dict, List, Optional, Type, Union

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required
else:
    from typing import NotRequired, Required

if sys.version_info < (3, 9):
    from typing_extensions import Literal, TypedDict
else:
    from typing import Literal, TypedDict


class CoreConfig(TypedDict, total=False):
    strict: bool
    # higher priority configs take precedence of over lower, if priority matches the two configs are merged, default 0
    config_choose_priority: int
    # if configs are merged, which should take precedence, default 0, default means child takes precedence
    config_merge_priority: int
    # settings related to typed_dicts only
    typed_dict_extra_behavior: Literal['allow', 'forbid', 'ignore']
    typed_dict_total: bool  # default: True
    # used on typed-dicts and tagged union keys
    from_attributes: bool
    revalidate_models: bool
    # used on typed-dicts and arguments
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    # fields related to string fields only
    str_max_length: int
    str_min_length: int
    str_strip_whitespace: bool
    str_to_lower: bool
    str_to_upper: bool
    # fields related to float fields only
    allow_inf_nan: bool  # default: True


class AnySchema(TypedDict):
    type: Literal['any']


class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str


class DictSchema(TypedDict, total=False):
    type: Required[Literal['dict']]
    keys_schema: CoreSchemaCombined  # default: AnySchema
    values_schema: CoreSchemaCombined  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool
    ref: str


class FloatSchema(TypedDict, total=False):
    type: Required[Literal['float']]
    allow_inf_nan: bool  # whether 'NaN', '+inf', '-inf' should be forbidden. default: True
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
    schema: CoreSchemaCombined
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
    items_schema: CoreSchemaCombined  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool
    ref: str


class LiteralSchema(TypedDict):
    type: Literal['literal']
    expected: List[Any]
    ref: NotRequired[str]


class NewClassSchema(TypedDict):
    type: Literal['new-class']
    class_type: type
    schema: CoreSchemaCombined
    call_after_init: NotRequired[str]
    strict: NotRequired[bool]
    ref: NotRequired[str]
    config: NotRequired[CoreConfig]


class TypedDictField(TypedDict, total=False):
    schema: Required[CoreSchemaCombined]
    required: bool
    alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]
    frozen: bool


class TypedDictSchema(TypedDict, total=False):
    type: Required[Literal['typed-dict']]
    fields: Required[Dict[str, TypedDictField]]
    strict: bool
    extra_validator: CoreSchemaCombined
    return_fields_set: bool
    ref: str
    # all these values can be set via config, equivalent fields have `typed_dict_` prefix
    extra_behavior: Literal['allow', 'forbid', 'ignore']
    total: bool  # default: True
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    from_attributes: bool


class NoneSchema(TypedDict):
    type: Literal['none']
    ref: NotRequired[str]


class NullableSchema(TypedDict, total=False):
    type: Required[Literal['nullable']]
    schema: Required[CoreSchemaCombined]
    strict: bool
    ref: str


class RecursiveReferenceSchema(TypedDict):
    type: Literal['recursive-ref']
    schema_ref: str


class SetSchema(TypedDict, total=False):
    type: Required[Literal['set']]
    items_schema: CoreSchemaCombined  # default: AnySchema
    min_items: int
    max_items: int
    strict: bool
    ref: str


class FrozenSetSchema(TypedDict, total=False):
    type: Required[Literal['frozenset']]
    items_schema: CoreSchemaCombined  # default: AnySchema
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
    choices: Required[List[CoreSchemaCombined]]
    strict: bool
    ref: str


class TaggedUnionSchema(TypedDict):
    type: Literal['tagged-union']
    choices: Dict[str, CoreSchemaCombined]
    discriminator: Union[str, List[Union[str, int]], List[List[Union[str, int]]], Callable[[Any], Optional[str]]]
    strict: NotRequired[bool]
    ref: NotRequired[str]


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


class TimedeltaSchema(TypedDict, total=False):
    type: Required[Literal['timedelta']]
    strict: bool
    le: timedelta
    ge: timedelta
    lt: timedelta
    gt: timedelta
    ref: str


class TuplePositionalSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    mode: Required[Literal['positional']]
    items_schema: Required[List[CoreSchemaCombined]]
    extra_schema: CoreSchemaCombined
    strict: bool
    ref: str


class TupleVariableSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    mode: Literal['variable']
    items_schema: CoreSchemaCombined
    min_items: int
    max_items: int
    strict: bool
    ref: str


class IsInstanceSchema(TypedDict):
    type: Literal['is-instance']
    class_: Type[Any]


class CallableSchema(TypedDict):
    type: Literal['callable']


class Parameter(TypedDict, total=False):
    name: Required[str]
    mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only']  # default positional_or_keyword
    schema: Required[CoreSchemaCombined]
    alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]


class ArgumentsSchema(TypedDict, total=False):
    type: Required[Literal['arguments']]
    arguments_schema: Required[List[Parameter]]
    populate_by_name: bool
    var_args_schema: CoreSchemaCombined
    var_kwargs_schema: CoreSchemaCombined
    ref: str


class CallSchema(TypedDict):
    type: Literal['call']
    function: Callable[..., Any]
    arguments_schema: CoreSchemaCombined
    return_schema: NotRequired[CoreSchemaCombined]
    ref: NotRequired[str]


class WithDefaultSchema(TypedDict, total=False):
    type: Required[Literal['default']]
    schema: Required[CoreSchemaCombined]
    default: Any
    default_factory: Callable[[], Any]
    on_error: Literal['raise', 'omit', 'default']  # default: 'raise'
    strict: bool
    ref: str


# pydantic allows types to be defined via a simple string instead of dict with just `type`, e.g.
# 'int' is equivalent to {'type': 'int'}, this only applies to schema types which do not have other required fields
CoreSchemaStrings = Literal[
    'any',
    'none',
    'str',
    'bytes',
    'dict',
    'int',
    'bool',
    'float',
    'dict',
    'list',
    'tuple',
    'set',
    'frozenset',
    'date',
    'time',
    'datetime',
    'timedelta',
    'callable',
]

CoreSchema = Union[
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
    NewClassSchema,
    NoneSchema,
    NullableSchema,
    RecursiveReferenceSchema,
    SetSchema,
    FrozenSetSchema,
    StringSchema,
    TuplePositionalSchema,
    TupleVariableSchema,
    UnionSchema,
    TaggedUnionSchema,
    DateSchema,
    TimeSchema,
    DatetimeSchema,
    TimedeltaSchema,
    IsInstanceSchema,
    CallableSchema,
    ArgumentsSchema,
    CallSchema,
    WithDefaultSchema,
]

CoreSchemaCombined = Union[
    CoreSchemaStrings,
    # Contents of `CoreSchema` copied here to avoid pyright error
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
    NewClassSchema,
    NoneSchema,
    NullableSchema,
    RecursiveReferenceSchema,
    SetSchema,
    FrozenSetSchema,
    StringSchema,
    TuplePositionalSchema,
    TupleVariableSchema,
    UnionSchema,
    TaggedUnionSchema,
    DateSchema,
    TimeSchema,
    DatetimeSchema,
    TimedeltaSchema,
    IsInstanceSchema,
    CallableSchema,
    ArgumentsSchema,
    CallSchema,
    WithDefaultSchema,
]
