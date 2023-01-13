from __future__ import annotations as _annotations

import sys
from datetime import date, datetime, time, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

if sys.version_info < (3, 11):
    from typing_extensions import Protocol, Required, TypeAlias
else:
    from typing import Protocol, Required, TypeAlias

if sys.version_info < (3, 9):
    from typing_extensions import Literal, TypedDict
else:
    from typing import Literal, TypedDict


def dict_not_none(**kwargs: Any) -> Any:
    return {k: v for k, v in kwargs.items() if v is not None}


class CoreConfig(TypedDict, total=False):
    title: str
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
    # the config options are used to customise serialization to JSON
    ser_json_timedelta: Literal['iso8601', 'float']  # default: 'iso8601'
    ser_json_bytes: Literal['utf8', 'base64']  # default: 'utf8'


IncExCall: TypeAlias = 'set[int | str] | dict[int | str, IncExCall] | None'


class SerializeFunction(Protocol):  # pragma: no cover
    def __call__(self, __input_value: Any, *, format: str, include: IncExCall | None, exclude: IncExCall | None) -> Any:
        ...


ExpectedSerializationTypes = Literal[
    'none',
    'int',
    'bool',
    'float',
    'str',
    'bytes',
    'bytearray',
    'list',
    'tuple',
    'set',
    'frozenset',
    'dict',
    'datetime',
    'date',
    'time',
    'timedelta',
    'url',
    'multi_host_url',
    'json',
]


class AltTypeSerSchema(TypedDict, total=False):
    type: Required[ExpectedSerializationTypes]


class FunctionSerSchema(TypedDict, total=False):
    type: Required[Literal['function']]
    function: Required[SerializeFunction]
    return_type: ExpectedSerializationTypes


class FormatSerSchema(TypedDict, total=False):
    type: Required[Literal['format']]
    formatting_string: Required[str]


class NewClassSerSchema(TypedDict, total=False):
    type: Required[Literal['new-class']]
    schema: Required[CoreSchema]


SerSchema = Union[AltTypeSerSchema, FunctionSerSchema, FormatSerSchema, NewClassSerSchema]


class AnySchema(TypedDict, total=False):
    type: Required[Literal['any']]
    ref: str
    extra: Any
    serialization: SerSchema


def any_schema(*, ref: str | None = None, extra: Any = None, serialization: SerSchema | None = None) -> AnySchema:
    return dict_not_none(type='any', ref=ref, extra=extra, serialization=serialization)


class NoneSchema(TypedDict, total=False):
    type: Required[Literal['none']]
    ref: str
    extra: Any
    serialization: SerSchema


def none_schema(*, ref: str | None = None, extra: Any = None, serialization: SerSchema | None = None) -> NoneSchema:
    return dict_not_none(type='none', ref=ref, extra=extra, serialization=serialization)


class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def bool_schema(
    strict: bool | None = None, ref: str | None = None, extra: Any = None, serialization: SerSchema | None = None
) -> BoolSchema:
    return dict_not_none(type='bool', strict=strict, ref=ref, extra=extra, serialization=serialization)


class IntSchema(TypedDict, total=False):
    type: Required[Literal['int']]
    multiple_of: int
    le: int
    ge: int
    lt: int
    gt: int
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def int_schema(
    *,
    multiple_of: int | None = None,
    le: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    gt: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> IntSchema:
    return dict_not_none(
        type='int',
        multiple_of=multiple_of,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


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
    extra: Any
    serialization: SerSchema


def float_schema(
    *,
    allow_inf_nan: bool | None = None,
    multiple_of: float | None = None,
    le: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    gt: float | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> FloatSchema:
    return dict_not_none(
        type='float',
        allow_inf_nan=allow_inf_nan,
        multiple_of=multiple_of,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


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
    extra: Any
    serialization: SerSchema


def string_schema(
    *,
    pattern: str | None = None,
    max_length: int | None = None,
    min_length: int | None = None,
    strip_whitespace: bool | None = None,
    to_lower: bool | None = None,
    to_upper: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> StringSchema:
    return dict_not_none(
        type='str',
        pattern=pattern,
        max_length=max_length,
        min_length=min_length,
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        to_upper=to_upper,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class BytesSchema(TypedDict, total=False):
    type: Required[Literal['bytes']]
    max_length: int
    min_length: int
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def bytes_schema(
    *,
    max_length: int | None = None,
    min_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> BytesSchema:
    return dict_not_none(
        type='bytes',
        max_length=max_length,
        min_length=min_length,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class DateSchema(TypedDict, total=False):
    type: Required[Literal['date']]
    strict: bool
    le: date
    ge: date
    lt: date
    gt: date
    now_op: Literal['past', 'future']
    # defaults to current local utc offset from `time.localtime().tm_gmtoff`
    # value is restricted to -86_400 < offset < 86_400 by bounds in generate_self_schema.py
    now_utc_offset: int
    ref: str
    extra: Any
    serialization: SerSchema


def date_schema(
    *,
    strict: bool | None = None,
    le: date | None = None,
    ge: date | None = None,
    lt: date | None = None,
    gt: date | None = None,
    ref: str | None = None,
    now_op: Literal['past', 'future'] | None = None,
    now_utc_offset: int | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> DateSchema:
    return dict_not_none(
        type='date',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        now_op=now_op,
        now_utc_offset=now_utc_offset,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class TimeSchema(TypedDict, total=False):
    type: Required[Literal['time']]
    strict: bool
    le: time
    ge: time
    lt: time
    gt: time
    ref: str
    extra: Any
    serialization: SerSchema


def time_schema(
    *,
    strict: bool | None = None,
    le: time | None = None,
    ge: time | None = None,
    lt: time | None = None,
    gt: time | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> TimeSchema:
    return dict_not_none(
        type='time', strict=strict, le=le, ge=ge, lt=lt, gt=gt, ref=ref, extra=extra, serialization=serialization
    )


class DatetimeSchema(TypedDict, total=False):
    type: Required[Literal['datetime']]
    strict: bool
    le: datetime
    ge: datetime
    lt: datetime
    gt: datetime
    now_op: Literal['past', 'future']
    tz_constraint: Literal['aware', 'naive']
    # defaults to current local utc offset from `time.localtime().tm_gmtoff`
    # value is restricted to -86_400 < offset < 86_400 by bounds in generate_self_schema.py
    now_utc_offset: int
    ref: str
    extra: Any
    serialization: SerSchema


def datetime_schema(
    *,
    strict: bool | None = None,
    le: datetime | None = None,
    ge: datetime | None = None,
    lt: datetime | None = None,
    gt: datetime | None = None,
    now_op: Literal['past', 'future'] | None = None,
    tz_constraint: Literal['aware', 'naive'] | None = None,
    now_utc_offset: int | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> DatetimeSchema:
    return dict_not_none(
        type='datetime',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        now_op=now_op,
        tz_constraint=tz_constraint,
        now_utc_offset=now_utc_offset,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class TimedeltaSchema(TypedDict, total=False):
    type: Required[Literal['timedelta']]
    strict: bool
    le: timedelta
    ge: timedelta
    lt: timedelta
    gt: timedelta
    ref: str
    extra: Any
    serialization: SerSchema


def timedelta_schema(
    *,
    strict: bool | None = None,
    le: timedelta | None = None,
    ge: timedelta | None = None,
    lt: timedelta | None = None,
    gt: timedelta | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> TimedeltaSchema:
    return dict_not_none(
        type='timedelta', strict=strict, le=le, ge=ge, lt=lt, gt=gt, ref=ref, extra=extra, serialization=serialization
    )


class LiteralSchema(TypedDict, total=False):
    type: Required[Literal['literal']]
    expected: Required[List[Any]]
    ref: str
    extra: Any
    serialization: SerSchema


def literal_schema(
    *expected: Any, ref: str | None = None, extra: Any = None, serialization: SerSchema | None = None
) -> LiteralSchema:
    return dict_not_none(type='literal', expected=expected, ref=ref, extra=extra, serialization=serialization)


# must match input/parse_json.rs::JsonType::try_from
JsonType = Literal['null', 'bool', 'int', 'float', 'str', 'list', 'dict']


class IsInstanceSchema(TypedDict, total=False):
    type: Required[Literal['is-instance']]
    cls: Required[Any]
    cls_repr: str
    json_types: Set[JsonType]
    json_function: Callable[[Any], Any]
    ref: str
    extra: Any
    serialization: SerSchema


def is_instance_schema(
    cls: Any,
    *,
    json_types: Set[JsonType] | None = None,
    json_function: Callable[[Any], Any] | None = None,
    cls_repr: str | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> IsInstanceSchema:
    return dict_not_none(
        type='is-instance',
        cls=cls,
        json_types=json_types,
        json_function=json_function,
        cls_repr=cls_repr,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class IsSubclassSchema(TypedDict, total=False):
    type: Required[Literal['is-subclass']]
    cls: Required[Type[Any]]
    cls_repr: str
    ref: str
    extra: Any
    serialization: SerSchema


def is_subclass_schema(
    cls: Type[Any],
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> IsInstanceSchema:
    return dict_not_none(
        type='is-subclass', cls=cls, cls_repr=cls_repr, ref=ref, extra=extra, serialization=serialization
    )


class CallableSchema(TypedDict, total=False):
    type: Required[Literal['callable']]
    ref: str
    extra: Any
    serialization: SerSchema


def callable_schema(
    *, ref: str | None = None, extra: Any = None, serialization: SerSchema | None = None
) -> CallableSchema:
    return dict_not_none(type='callable', ref=ref, extra=extra, serialization=serialization)


class IncExSeqSerSchema(TypedDict, total=False):
    type: Required[Literal['include-exclude-sequence']]
    include: Set[int]
    exclude: Set[int]


def filter_seq_schema(*, include: Set[int] | None = None, exclude: Set[int] | None = None) -> IncExSeqSerSchema:
    return dict_not_none(type='include-exclude-sequence', include=include, exclude=exclude)


IncExSeqOrElseSerSchema = Union[IncExSeqSerSchema, SerSchema]


class ListSchema(TypedDict, total=False):
    type: Required[Literal['list']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    strict: bool
    allow_any_iter: bool
    ref: str
    extra: Any
    serialization: IncExSeqOrElseSerSchema


def list_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    allow_any_iter: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> ListSchema:
    return dict_not_none(
        type='list',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        allow_any_iter=allow_any_iter,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class TuplePositionalSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    mode: Required[Literal['positional']]
    items_schema: Required[List[CoreSchema]]
    extra_schema: CoreSchema
    strict: bool
    ref: str
    extra: Any
    serialization: IncExSeqOrElseSerSchema


def tuple_positional_schema(
    *items_schema: CoreSchema,
    extra_schema: CoreSchema | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TuplePositionalSchema:
    return dict_not_none(
        type='tuple',
        mode='positional',
        items_schema=items_schema,
        extra_schema=extra_schema,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class TupleVariableSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    mode: Literal['variable']
    items_schema: CoreSchema
    min_length: int
    max_length: int
    strict: bool
    ref: str
    extra: Any
    serialization: IncExSeqOrElseSerSchema


def tuple_variable_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleVariableSchema:
    return dict_not_none(
        type='tuple',
        mode='variable',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class SetSchema(TypedDict, total=False):
    type: Required[Literal['set']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    generator_max_length: int
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def set_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    generator_max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> SetSchema:
    return dict_not_none(
        type='set',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        generator_max_length=generator_max_length,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class FrozenSetSchema(TypedDict, total=False):
    type: Required[Literal['frozenset']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    generator_max_length: int
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def frozenset_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    generator_max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> FrozenSetSchema:
    return dict_not_none(
        type='frozenset',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        generator_max_length=generator_max_length,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class GeneratorSchema(TypedDict, total=False):
    type: Required[Literal['generator']]
    items_schema: CoreSchema
    max_length: int
    ref: str
    extra: Any
    serialization: IncExSeqOrElseSerSchema


def generator_schema(
    items_schema: CoreSchema | None = None,
    *,
    max_length: int | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> GeneratorSchema:
    return dict_not_none(
        type='generator',
        items_schema=items_schema,
        max_length=max_length,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


IncExDict = Set[Union[int, str]]


class IncExDictSerSchema(TypedDict, total=False):
    type: Required[Literal['include-exclude-dict']]
    include: IncExDict
    exclude: IncExDict


def filter_dict_schema(*, include: IncExDict | None = None, exclude: IncExDict | None = None) -> IncExDictSerSchema:
    return dict_not_none(type='include-exclude-dict', include=include, exclude=exclude)


IncExDictOrElseSerSchema = Union[IncExDictSerSchema, SerSchema]


class DictSchema(TypedDict, total=False):
    type: Required[Literal['dict']]
    keys_schema: CoreSchema  # default: AnySchema
    values_schema: CoreSchema  # default: AnySchema
    min_length: int
    max_length: int
    strict: bool
    ref: str
    extra: Any
    serialization: IncExDictOrElseSerSchema


def dict_schema(
    keys_schema: CoreSchema | None = None,
    values_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> DictSchema:
    return dict_not_none(
        type='dict',
        keys_schema=keys_schema,
        values_schema=values_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class ValidatorFunction(Protocol):
    def __call__(
        self, __input_value: Any, *, data: Any, config: CoreConfig | None, context: Any, **future_kwargs: Any
    ) -> Any:  # pragma: no cover
        ...


class FunctionSchema(TypedDict, total=False):
    type: Required[Literal['function']]
    mode: Required[Literal['before', 'after']]
    function: Required[ValidatorFunction]
    schema: Required[CoreSchema]
    ref: str
    extra: Any
    serialization: SerSchema


def function_before_schema(
    function: ValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> FunctionSchema:
    return dict_not_none(
        type='function',
        mode='before',
        function=function,
        schema=schema,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


def function_after_schema(
    schema: CoreSchema,
    function: ValidatorFunction,
    *,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> FunctionSchema:
    return dict_not_none(
        type='function',
        mode='after',
        function=function,
        schema=schema,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class CallableValidator(Protocol):
    def __call__(self, input_value: Any, outer_location: str | int | None = None) -> Any:  # pragma: no cover
        ...


class WrapValidatorFunction(Protocol):
    def __call__(
        self,
        __input_value: Any,
        *,
        validator: CallableValidator,
        data: Any,
        config: CoreConfig | None,
        context: Any,
        **future_kwargs: Any,
    ) -> Any:  # pragma: no cover
        ...


class FunctionWrapSchema(TypedDict, total=False):
    type: Required[Literal['function']]
    mode: Required[Literal['wrap']]
    function: Required[WrapValidatorFunction]
    schema: Required[CoreSchema]
    ref: str
    extra: Any
    serialization: SerSchema


def function_wrap_schema(
    function: WrapValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> FunctionWrapSchema:
    return dict_not_none(
        type='function',
        mode='wrap',
        function=function,
        schema=schema,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class FunctionPlainSchema(TypedDict, total=False):
    type: Required[Literal['function']]
    mode: Required[Literal['plain']]
    function: Required[ValidatorFunction]
    ref: str
    extra: Any
    serialization: SerSchema


def function_plain_schema(
    function: ValidatorFunction, *, ref: str | None = None, extra: Any = None, serialization: SerSchema | None = None
) -> FunctionPlainSchema:
    return dict_not_none(
        type='function', mode='plain', function=function, ref=ref, extra=extra, serialization=serialization
    )


class WithDefaultSchema(TypedDict, total=False):
    type: Required[Literal['default']]
    schema: Required[CoreSchema]
    default: Any
    default_factory: Callable[[], Any]
    on_error: Literal['raise', 'omit', 'default']  # default: 'raise'
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


Omitted = object()


def with_default_schema(
    schema: CoreSchema,
    *,
    default: Any = Omitted,
    default_factory: Callable[[], Any] | None = None,
    on_error: Literal['raise', 'omit', 'default'] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> WithDefaultSchema:
    s = dict_not_none(
        type='default',
        schema=schema,
        default_factory=default_factory,
        on_error=on_error,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )
    if default is not Omitted:
        s['default'] = default
    return s


class NullableSchema(TypedDict, total=False):
    type: Required[Literal['nullable']]
    schema: Required[CoreSchema]
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def nullable_schema(
    schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> NullableSchema:
    return dict_not_none(
        type='nullable', schema=schema, strict=strict, ref=ref, extra=extra, serialization=serialization
    )


class UnionSchema(TypedDict, total=False):
    type: Required[Literal['union']]
    choices: Required[List[CoreSchema]]
    custom_error_type: str
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def union_schema(
    *choices: CoreSchema,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, str | int] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> UnionSchema:
    return dict_not_none(
        type='union',
        choices=choices,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class TaggedUnionSchema(TypedDict, total=False):
    type: Required[Literal['tagged-union']]
    choices: Required[Dict[str, Union[str, CoreSchema]]]
    discriminator: Required[
        Union[str, List[Union[str, int]], List[List[Union[str, int]]], Callable[[Any], Optional[str]]]
    ]
    custom_error_type: str
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def tagged_union_schema(
    choices: Dict[str, str | CoreSchema],
    discriminator: str | list[str | int] | list[list[str | int]] | Callable[[Any], str | None],
    *,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, int | str | float] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> TaggedUnionSchema:
    return dict_not_none(
        type='tagged-union',
        choices=choices,
        discriminator=discriminator,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class ChainSchema(TypedDict, total=False):
    type: Required[Literal['chain']]
    steps: Required[List[CoreSchema]]
    ref: str
    extra: Any
    serialization: SerSchema


def chain_schema(
    *steps: CoreSchema, ref: str | None = None, extra: Any = None, serialization: SerSchema | None = None
) -> ChainSchema:
    return dict_not_none(type='chain', steps=steps, ref=ref, extra=extra, serialization=serialization)


class LaxOrStrictSchema(TypedDict, total=False):
    type: Required[Literal['lax-or-strict']]
    lax_schema: Required[CoreSchema]
    strict_schema: Required[CoreSchema]
    strict: bool
    ref: str
    extra: Any


def lax_or_strict_schema(
    lax_schema: CoreSchema,
    strict_schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
) -> LaxOrStrictSchema:
    return dict_not_none(
        type='lax-or-strict', lax_schema=lax_schema, strict_schema=strict_schema, strict=strict, ref=ref, extra=extra
    )


class TypedDictField(TypedDict, total=False):
    schema: Required[CoreSchema]
    required: bool
    validation_alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]
    serialization_alias: str
    serialization_exclude: bool  # default: False
    frozen: bool


def typed_dict_field(
    schema: CoreSchema,
    *,
    required: bool | None = None,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    frozen: bool | None = None,
) -> TypedDictField:
    return dict_not_none(
        schema=schema,
        required=required,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        frozen=frozen,
    )


class TypedDictSchema(TypedDict, total=False):
    type: Required[Literal['typed-dict']]
    fields: Required[Dict[str, TypedDictField]]
    strict: bool
    extra_validator: CoreSchema
    return_fields_set: bool
    # all these values can be set via config, equivalent fields have `typed_dict_` prefix
    extra_behavior: Literal['allow', 'forbid', 'ignore']
    total: bool  # default: True
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    from_attributes: bool
    ref: str
    extra: Any
    serialization: SerSchema


def typed_dict_schema(
    fields: Dict[str, TypedDictField],
    *,
    strict: bool | None = None,
    extra_validator: CoreSchema | None = None,
    return_fields_set: bool | None = None,
    extra_behavior: Literal['allow', 'forbid', 'ignore'] | None = None,
    total: bool | None = None,
    populate_by_name: bool | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> TypedDictSchema:
    return dict_not_none(
        type='typed-dict',
        fields=fields,
        strict=strict,
        extra_validator=extra_validator,
        return_fields_set=return_fields_set,
        extra_behavior=extra_behavior,
        total=total,
        populate_by_name=populate_by_name,
        from_attributes=from_attributes,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class NewClassSchema(TypedDict, total=False):
    type: Required[Literal['new-class']]
    cls: Required[Type[Any]]
    schema: Required[CoreSchema]
    call_after_init: str
    strict: bool
    config: CoreConfig
    ref: str
    extra: Any
    serialization: SerSchema


def new_class_schema(
    cls: Type[Any],
    schema: CoreSchema,
    *,
    call_after_init: str | None = None,
    strict: bool | None = None,
    config: CoreConfig | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> NewClassSchema:
    return dict_not_none(
        type='new-class',
        cls=cls,
        schema=schema,
        call_after_init=call_after_init,
        strict=strict,
        config=config,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class ArgumentsParameter(TypedDict, total=False):
    name: Required[str]
    schema: Required[CoreSchema]
    mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only']  # default positional_or_keyword
    alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]


def arguments_parameter(
    name: str,
    schema: CoreSchema,
    *,
    mode: Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None = None,
    alias: str | list[str | int] | list[list[str | int]] | None = None,
) -> ArgumentsParameter:
    return dict_not_none(name=name, schema=schema, mode=mode, alias=alias)


class ArgumentsSchema(TypedDict, total=False):
    type: Required[Literal['arguments']]
    arguments_schema: Required[List[ArgumentsParameter]]
    populate_by_name: bool
    var_args_schema: CoreSchema
    var_kwargs_schema: CoreSchema
    ref: str
    extra: Any
    serialization: SerSchema


def arguments_schema(
    *arguments: ArgumentsParameter,
    populate_by_name: bool | None = None,
    var_args_schema: CoreSchema | None = None,
    var_kwargs_schema: CoreSchema | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> ArgumentsSchema:
    return dict_not_none(
        type='arguments',
        arguments_schema=arguments,
        populate_by_name=populate_by_name,
        var_args_schema=var_args_schema,
        var_kwargs_schema=var_kwargs_schema,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class CallSchema(TypedDict, total=False):
    type: Required[Literal['call']]
    arguments_schema: Required[CoreSchema]
    function: Required[Callable[..., Any]]
    return_schema: CoreSchema
    ref: str
    extra: Any
    serialization: SerSchema


def call_schema(
    arguments: CoreSchema,
    function: Callable[..., Any],
    *,
    return_schema: CoreSchema | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> CallSchema:
    return dict_not_none(
        type='call',
        arguments_schema=arguments,
        function=function,
        return_schema=return_schema,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class RecursiveReferenceSchema(TypedDict, total=False):
    type: Required[Literal['recursive-ref']]
    schema_ref: Required[str]


def recursive_reference_schema(schema_ref: str) -> RecursiveReferenceSchema:
    return {'type': 'recursive-ref', 'schema_ref': schema_ref}


class CustomErrorSchema(TypedDict, total=False):
    type: Required[Literal['custom_error']]
    schema: Required[CoreSchema]
    custom_error_type: Required[str]
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    ref: str
    extra: Any
    serialization: SerSchema


def custom_error_schema(
    schema: CoreSchema,
    custom_error_type: str,
    *,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, str | int | float] | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> CustomErrorSchema:
    return dict_not_none(
        type='custom_error',
        schema=schema,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class JsonSchema(TypedDict, total=False):
    type: Required[Literal['json']]
    schema: CoreSchema
    ref: str
    extra: Any
    serialization: SerSchema


def json_schema(
    schema: CoreSchema | None = None,
    *,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> JsonSchema:
    return dict_not_none(type='json', schema=schema, ref=ref, extra=extra, serialization=serialization)


class UrlSchema(TypedDict, total=False):
    type: Required[Literal['url']]
    max_length: int
    allowed_schemes: List[str]
    host_required: bool  # default False
    default_host: str
    default_port: int
    default_path: str
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> UrlSchema:
    return dict_not_none(
        type='url',
        max_length=max_length,
        allowed_schemes=allowed_schemes,
        host_required=host_required,
        default_host=default_host,
        default_port=default_port,
        default_path=default_path,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


class MultiHostUrlSchema(TypedDict, total=False):
    type: Required[Literal['multi-host-url']]
    max_length: int
    allowed_schemes: List[str]
    host_required: bool  # default False
    default_host: str
    default_port: int
    default_path: str
    strict: bool
    ref: str
    extra: Any
    serialization: SerSchema


def multi_host_url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    extra: Any = None,
    serialization: SerSchema | None = None,
) -> MultiHostUrlSchema:
    return dict_not_none(
        type='multi-host-url',
        max_length=max_length,
        allowed_schemes=allowed_schemes,
        host_required=host_required,
        default_host=default_host,
        default_port=default_port,
        default_path=default_path,
        strict=strict,
        ref=ref,
        extra=extra,
        serialization=serialization,
    )


CoreSchema = Union[
    AnySchema,
    NoneSchema,
    BoolSchema,
    IntSchema,
    FloatSchema,
    StringSchema,
    BytesSchema,
    DateSchema,
    TimeSchema,
    DatetimeSchema,
    TimedeltaSchema,
    LiteralSchema,
    IsInstanceSchema,
    IsSubclassSchema,
    CallableSchema,
    ListSchema,
    TuplePositionalSchema,
    TupleVariableSchema,
    SetSchema,
    FrozenSetSchema,
    GeneratorSchema,
    DictSchema,
    FunctionSchema,
    FunctionWrapSchema,
    FunctionPlainSchema,
    WithDefaultSchema,
    NullableSchema,
    UnionSchema,
    TaggedUnionSchema,
    ChainSchema,
    LaxOrStrictSchema,
    TypedDictSchema,
    NewClassSchema,
    ArgumentsSchema,
    CallSchema,
    RecursiveReferenceSchema,
    CustomErrorSchema,
    JsonSchema,
    UrlSchema,
    MultiHostUrlSchema,
]

# used in _pydantic_core.pyi::PydanticKnownError
# to update this, call `pytest -k test_all_errors` and copy the output
ErrorType = Literal[
    'json_invalid',
    'json_type',
    'recursion_loop',
    'dict_attributes_type',
    'missing',
    'frozen',
    'extra_forbidden',
    'invalid_key',
    'get_attribute_error',
    'model_class_type',
    'none_required',
    'bool',
    'greater_than',
    'greater_than_equal',
    'less_than',
    'less_than_equal',
    'multiple_of',
    'finite_number',
    'too_short',
    'too_long',
    'iterable_type',
    'iteration_error',
    'string_type',
    'string_sub_type',
    'string_unicode',
    'string_too_short',
    'string_too_long',
    'string_pattern_mismatch',
    'dict_type',
    'mapping_type',
    'list_type',
    'tuple_type',
    'set_type',
    'bool_type',
    'bool_parsing',
    'int_type',
    'int_parsing',
    'int_from_float',
    'float_type',
    'float_parsing',
    'bytes_type',
    'bytes_too_short',
    'bytes_too_long',
    'value_error',
    'assertion_error',
    'literal_error',
    'date_type',
    'date_parsing',
    'date_from_datetime_parsing',
    'date_from_datetime_inexact',
    'date_past',
    'date_future',
    'time_type',
    'time_parsing',
    'datetime_type',
    'datetime_parsing',
    'datetime_object_invalid',
    'datetime_past',
    'datetime_future',
    'datetime_aware',
    'datetime_naive',
    'time_delta_type',
    'time_delta_parsing',
    'frozen_set_type',
    'is_instance_of',
    'is_subclass_of',
    'callable_type',
    'union_tag_invalid',
    'union_tag_not_found',
    'arguments_type',
    'positional_arguments_type',
    'keyword_arguments_type',
    'unexpected_keyword_argument',
    'missing_keyword_argument',
    'unexpected_positional_argument',
    'missing_positional_argument',
    'multiple_argument_values',
    'url_type',
    'url_parsing',
    'url_syntax_violation',
    'url_too_long',
    'url_scheme',
]
