from __future__ import annotations as _annotations

import sys
from datetime import date, datetime, time, timedelta
from typing import Any, Callable, Dict, List, Optional, Type, Union, overload

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Protocol, Required
else:
    from typing import NotRequired, Protocol, Required

if sys.version_info < (3, 9):
    from typing_extensions import Literal, TypedDict
else:
    from typing import Literal, TypedDict


def dict_not_none(**kwargs: Any) -> Any:
    return {k: v for k, v in kwargs.items() if v is not None}


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


def any_schema() -> AnySchema:
    return {'type': 'any'}


class NoneSchema(TypedDict):
    type: Literal['none']
    ref: NotRequired[str]


def none_schema(*, ref: str | None = None) -> NoneSchema:
    return dict_not_none(type='none', ref=ref)


class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str


def bool_schema(strict: bool | None = None, ref: str | None = None) -> BoolSchema:
    return dict_not_none(type='bool', strict=strict, ref=ref)


class IntSchema(TypedDict, total=False):
    type: Required[Literal['int']]
    multiple_of: int
    le: int
    ge: int
    lt: int
    gt: int
    strict: bool
    ref: str


def int_schema(
    *,
    multiple_of: int | None = None,
    le: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    gt: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> IntSchema:
    return dict_not_none(type='int', multiple_of=multiple_of, le=le, ge=ge, lt=lt, gt=gt, strict=strict, ref=ref)


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
    )


class BytesSchema(TypedDict, total=False):
    type: Required[Literal['bytes']]
    max_length: int
    min_length: int
    strict: bool
    ref: str


def bytes_schema(
    *, max_length: int | None = None, min_length: int | None = None, strict: bool | None = None, ref: str | None = None
) -> BytesSchema:
    return dict_not_none(type='bytes', max_length=max_length, min_length=min_length, strict=strict, ref=ref)


class DateSchema(TypedDict, total=False):
    type: Required[Literal['date']]
    strict: bool
    le: date
    ge: date
    lt: date
    gt: date
    ref: str


def date_schema(
    *,
    strict: bool | None = None,
    le: date | None = None,
    ge: date | None = None,
    lt: date | None = None,
    gt: date | None = None,
    ref: str | None = None,
) -> DateSchema:
    return dict_not_none(type='date', strict=strict, le=le, ge=ge, lt=lt, gt=gt, ref=ref)


class TimeSchema(TypedDict, total=False):
    type: Required[Literal['time']]
    strict: bool
    le: time
    ge: time
    lt: time
    gt: time
    ref: str


def time_schema(
    *,
    strict: bool | None = None,
    le: time | None = None,
    ge: time | None = None,
    lt: time | None = None,
    gt: time | None = None,
    ref: str | None = None,
) -> TimeSchema:
    return dict_not_none(type='time', strict=strict, le=le, ge=ge, lt=lt, gt=gt, ref=ref)


class DatetimeSchema(TypedDict, total=False):
    type: Required[Literal['datetime']]
    strict: bool
    le: datetime
    ge: datetime
    lt: datetime
    gt: datetime
    ref: str


def datetime_schema(
    *,
    strict: bool | None = None,
    le: datetime | None = None,
    ge: datetime | None = None,
    lt: datetime | None = None,
    gt: datetime | None = None,
    ref: str | None = None,
) -> DatetimeSchema:
    return dict_not_none(type='datetime', strict=strict, le=le, ge=ge, lt=lt, gt=gt, ref=ref)


class TimedeltaSchema(TypedDict, total=False):
    type: Required[Literal['timedelta']]
    strict: bool
    le: timedelta
    ge: timedelta
    lt: timedelta
    gt: timedelta
    ref: str


def timedelta_schema(
    *,
    strict: bool | None = None,
    le: timedelta | None = None,
    ge: timedelta | None = None,
    lt: timedelta | None = None,
    gt: timedelta | None = None,
    ref: str | None = None,
) -> TimedeltaSchema:
    return dict_not_none(type='timedelta', strict=strict, le=le, ge=ge, lt=lt, gt=gt, ref=ref)


class LiteralSchema(TypedDict):
    type: Literal['literal']
    expected: List[Any]
    ref: NotRequired[str]


def literal_schema(*expected: Any, ref: str | None = None) -> LiteralSchema:
    return dict_not_none(type='literal', expected=expected, ref=ref)


class IsInstanceSchema(TypedDict):
    type: Literal['is-instance']
    cls: Type[Any]


def is_instance_schema(cls: Type[Any]) -> IsInstanceSchema:
    return dict_not_none(type='is-instance', cls=cls)


class CallableSchema(TypedDict):
    type: Literal['callable']


def callable_schema() -> CallableSchema:
    return dict_not_none(type='callable')


class ListSchema(TypedDict, total=False):
    type: Required[Literal['list']]
    items_schema: CoreSchema  # default: AnySchema
    min_length: int
    max_length: int
    strict: bool
    ref: str


def list_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> ListSchema:
    return dict_not_none(
        type='list', items_schema=items_schema, min_length=min_length, max_length=max_length, strict=strict, ref=ref
    )


class TuplePositionalSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    mode: Required[Literal['positional']]
    items_schema: Required[List[CoreSchema]]
    extra_schema: CoreSchema
    strict: bool
    ref: str


def tuple_positional_schema(
    *items_schema: CoreSchema,
    extra_schema: CoreSchema | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> TuplePositionalSchema:
    return dict_not_none(
        type='tuple', mode='positional', items_schema=items_schema, extra_schema=extra_schema, strict=strict, ref=ref
    )


class TupleVariableSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    mode: Literal['variable']
    items_schema: CoreSchema
    min_length: int
    max_length: int
    strict: bool
    ref: str


def tuple_variable_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> TupleVariableSchema:
    return dict_not_none(
        type='tuple',
        mode='variable',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
    )


class SetSchema(TypedDict, total=False):
    type: Required[Literal['set']]
    items_schema: CoreSchema  # default: AnySchema
    min_length: int
    max_length: int
    strict: bool
    ref: str


def set_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> SetSchema:
    return dict_not_none(
        type='set', items_schema=items_schema, min_length=min_length, max_length=max_length, strict=strict, ref=ref
    )


class FrozenSetSchema(TypedDict, total=False):
    type: Required[Literal['frozenset']]
    items_schema: CoreSchema  # default: AnySchema
    min_length: int
    max_length: int
    strict: bool
    ref: str


def frozen_set_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> FrozenSetSchema:
    return dict_not_none(
        type='frozenset',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
    )


class DictSchema(TypedDict, total=False):
    type: Required[Literal['dict']]
    keys_schema: CoreSchema  # default: AnySchema
    values_schema: CoreSchema  # default: AnySchema
    min_length: int
    max_length: int
    strict: bool
    ref: str


def dict_schema(
    keys_schema: CoreSchema | None = None,
    values_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> DictSchema:
    return dict_not_none(
        type='dict',
        keys_schema=keys_schema,
        values_schema=values_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
    )


class ValidatorFunction(Protocol):
    def __call__(
        self, __input_value: Any, *, data: Any, config: CoreConfig | None, context: Any, **future_kwargs: Any
    ) -> Any:
        ...


class FunctionSchema(TypedDict):
    type: Literal['function']
    mode: Literal['before', 'after']
    function: ValidatorFunction
    schema: CoreSchema
    # validator_instance is used by pydantic for progressively preparing the function, ignored by pydantic-core
    validator_instance: NotRequired[Any]
    ref: NotRequired[str]


def function_before_schema(
    function: ValidatorFunction, schema: CoreSchema, *, validator_instance: Any | None = None, ref: str | None = None
) -> FunctionSchema:
    return dict_not_none(
        type='function', mode='before', function=function, schema=schema, validator_instance=validator_instance, ref=ref
    )


def function_after_schema(
    function: ValidatorFunction, schema: CoreSchema, *, validator_instance: Any | None = None, ref: str | None = None
) -> FunctionSchema:
    return dict_not_none(
        type='function', mode='after', function=function, schema=schema, validator_instance=validator_instance, ref=ref
    )


class CallableValidator(Protocol):
    def __call__(self, input_value: Any, outer_location: str | int | None = None) -> Any:
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
    ) -> Any:
        ...


class FunctionWrapSchema(TypedDict):
    type: Literal['function']
    mode: Literal['wrap']
    function: WrapValidatorFunction
    schema: CoreSchema
    # validator_instance is used by pydantic for progressively preparing the function, ignored by pydantic-core
    validator_instance: NotRequired[Any]
    ref: NotRequired[str]


def function_wrap_schema(
    function: WrapValidatorFunction,
    schema: CoreSchema,
    *,
    validator_instance: Any | None = None,
    ref: str | None = None,
) -> FunctionWrapSchema:
    return dict_not_none(
        type='function', mode='wrap', function=function, schema=schema, validator_instance=validator_instance, ref=ref
    )


class FunctionPlainSchema(TypedDict):
    type: Literal['function']
    mode: Literal['plain']
    function: ValidatorFunction
    # validator_instance is used by pydantic for progressively preparing the function, ignored by pydantic-core
    validator_instance: NotRequired[Any]
    ref: NotRequired[str]


def function_plain_schema(
    function: ValidatorFunction, *, validator_instance: Any | None = None, ref: str | None = None
) -> FunctionPlainSchema:
    return dict_not_none(
        type='function', mode='plain', function=function, validator_instance=validator_instance, ref=ref
    )


class WithDefaultSchema(TypedDict, total=False):
    type: Required[Literal['default']]
    schema: Required[CoreSchema]
    default: Any
    default_factory: Callable[[], Any]
    on_error: Literal['raise', 'omit', 'default']  # default: 'raise'
    strict: bool
    ref: str


Omitted = object()


def with_default_schema(
    schema: CoreSchema,
    *,
    default: Any = Omitted,
    default_factory: Callable[[], Any] | None = None,
    on_error: Literal['raise', 'omit', 'default'] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> WithDefaultSchema:
    s = dict_not_none(
        type='default', schema=schema, default_factory=default_factory, on_error=on_error, strict=strict, ref=ref
    )
    if default is not Omitted:
        s['default'] = default
    return s


class NullableSchema(TypedDict, total=False):
    type: Required[Literal['nullable']]
    schema: Required[CoreSchema]
    strict: bool
    ref: str


def nullable_schema(schema: CoreSchema, *, strict: bool | None = None, ref: str | None = None) -> NullableSchema:
    return dict_not_none(type='nullable', schema=schema, strict=strict, ref=ref)


class CustomError(TypedDict):
    kind: str
    message: str


def _custom_error(kind: str | None, message: str | None) -> CustomError | None:
    if kind is None and message is None:
        return None
    else:
        # let schema validation raise the error
        return CustomError(kind=kind, message=message)  # type: ignore


class UnionSchema(TypedDict, total=False):
    type: Required[Literal['union']]
    choices: Required[List[CoreSchema]]
    custom_error: CustomError
    strict: bool
    ref: str


@overload
def union_schema(
    *choices: CoreSchema,
    custom_error_kind: str,
    custom_error_message: str,
    strict: bool | None = None,
    ref: str | None = None,
) -> UnionSchema:
    ...


@overload
def union_schema(*choices: CoreSchema, strict: bool | None = None, ref: str | None = None) -> UnionSchema:
    ...


def union_schema(
    *choices: CoreSchema,
    custom_error_kind: str | None = None,
    custom_error_message: str | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> UnionSchema:
    return dict_not_none(
        type='union',
        choices=choices,
        custom_error=_custom_error(custom_error_kind, custom_error_message),
        strict=strict,
        ref=ref,
    )


class TaggedUnionSchema(TypedDict):
    type: Literal['tagged-union']
    choices: Dict[str, CoreSchema]
    discriminator: Union[str, List[Union[str, int]], List[List[Union[str, int]]], Callable[[Any], Optional[str]]]
    custom_error: NotRequired[CustomError]
    strict: NotRequired[bool]
    ref: NotRequired[str]


@overload
def tagged_union_schema(
    choices: Dict[str, CoreSchema],
    discriminator: str | list[str | int] | list[list[str | int]] | Callable[[Any], str | None],
    *,
    custom_error_kind: str,
    custom_error_message: str,
    strict: bool | None = None,
    ref: str | None = None,
) -> TaggedUnionSchema:
    ...


@overload
def tagged_union_schema(
    choices: Dict[str, CoreSchema],
    discriminator: str | list[str | int] | list[list[str | int]] | Callable[[Any], str | None],
    *,
    strict: bool | None = None,
    ref: str | None = None,
) -> TaggedUnionSchema:
    ...


def tagged_union_schema(
    choices: Dict[str, CoreSchema],
    discriminator: str | list[str | int] | list[list[str | int]] | Callable[[Any], str | None],
    *,
    custom_error_kind: str | None = None,
    custom_error_message: str | None = None,
    strict: bool | None = None,
    ref: str | None = None,
) -> TaggedUnionSchema:
    return dict_not_none(
        type='tagged-union',
        choices=choices,
        discriminator=discriminator,
        custom_error=_custom_error(custom_error_kind, custom_error_message),
        strict=strict,
        ref=ref,
    )


class ChainSchema(TypedDict):
    type: Literal['chain']
    steps: List[CoreSchema]
    ref: NotRequired[str]


def chain_schema(*steps: CoreSchema, ref: str | None = None) -> ChainSchema:
    return dict_not_none(type='chain', steps=steps, ref=ref)


class TypedDictField(TypedDict, total=False):
    schema: Required[CoreSchema]
    required: bool
    alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]
    frozen: bool


def typed_dict_field(
    schema: CoreSchema,
    *,
    required: bool | None = None,
    alias: str | list[str | int] | list[list[str | int]] | None = None,
    frozen: bool | None = None,
) -> TypedDictField:
    return dict_not_none(schema=schema, required=required, alias=alias, frozen=frozen)


class TypedDictSchema(TypedDict, total=False):
    type: Required[Literal['typed-dict']]
    fields: Required[Dict[str, TypedDictField]]
    strict: bool
    extra_validator: CoreSchema
    return_fields_set: bool
    ref: str
    # all these values can be set via config, equivalent fields have `typed_dict_` prefix
    extra_behavior: Literal['allow', 'forbid', 'ignore']
    total: bool  # default: True
    populate_by_name: bool  # replaces `allow_population_by_field_name` in pydantic v1
    from_attributes: bool


def typed_dict_schema(
    fields: Dict[str, TypedDictField],
    *,
    strict: bool | None = None,
    extra_validator: CoreSchema | None = None,
    return_fields_set: bool | None = None,
    ref: str | None = None,
    extra_behavior: Literal['allow', 'forbid', 'ignore'] | None = None,
    total: bool | None = None,
    populate_by_name: bool | None = None,
    from_attributes: bool | None = None,
) -> TypedDictSchema:
    return dict_not_none(
        type='typed-dict',
        fields=fields,
        strict=strict,
        extra_validator=extra_validator,
        return_fields_set=return_fields_set,
        ref=ref,
        extra_behavior=extra_behavior,
        total=total,
        populate_by_name=populate_by_name,
        from_attributes=from_attributes,
    )


class NewClassSchema(TypedDict):
    type: Literal['new-class']
    cls: Type[Any]
    schema: CoreSchema
    call_after_init: NotRequired[str]
    strict: NotRequired[bool]
    ref: NotRequired[str]
    config: NotRequired[CoreConfig]


def new_class_schema(
    cls: Type[Any],
    schema: CoreSchema,
    *,
    call_after_init: str | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    config: CoreConfig | None = None,
) -> NewClassSchema:
    return dict_not_none(
        type='new-class', cls=cls, schema=schema, call_after_init=call_after_init, strict=strict, ref=ref, config=config
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


def arguments_schema(
    *arguments: ArgumentsParameter,
    populate_by_name: bool | None = None,
    var_args_schema: CoreSchema | None = None,
    var_kwargs_schema: CoreSchema | None = None,
    ref: str | None = None,
) -> ArgumentsSchema:
    return dict_not_none(
        type='arguments',
        arguments_schema=arguments,
        populate_by_name=populate_by_name,
        var_args_schema=var_args_schema,
        var_kwargs_schema=var_kwargs_schema,
        ref=ref,
    )


class CallSchema(TypedDict):
    type: Literal['call']
    arguments_schema: CoreSchema
    function: Callable[..., Any]
    return_schema: NotRequired[CoreSchema]
    ref: NotRequired[str]


def call_schema(
    arguments: CoreSchema,
    function: Callable[..., Any],
    *,
    return_schema: CoreSchema | None = None,
    ref: str | None = None,
) -> CallSchema:
    return dict_not_none(
        type='call', arguments_schema=arguments, function=function, return_schema=return_schema, ref=ref
    )


class RecursiveReferenceSchema(TypedDict):
    type: Literal['recursive-ref']
    schema_ref: str


def recursive_reference_schema(schema_ref: str) -> RecursiveReferenceSchema:
    return {'type': 'recursive-ref', 'schema_ref': schema_ref}


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
    CallableSchema,
    ListSchema,
    TuplePositionalSchema,
    TupleVariableSchema,
    SetSchema,
    FrozenSetSchema,
    DictSchema,
    FunctionSchema,
    FunctionWrapSchema,
    FunctionPlainSchema,
    WithDefaultSchema,
    NullableSchema,
    UnionSchema,
    TaggedUnionSchema,
    ChainSchema,
    TypedDictSchema,
    NewClassSchema,
    ArgumentsSchema,
    CallSchema,
    RecursiveReferenceSchema,
]
