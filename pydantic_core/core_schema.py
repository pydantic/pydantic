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


class SerializationInfo(Protocol):
    include: IncExCall
    exclude: IncExCall
    mode: str
    by_alias: bool
    exclude_unset: bool
    exclude_defaults: bool
    exclude_none: bool
    round_trip: bool

    def mode_is_json(self) -> bool:
        ...

    def __str__(self) -> str:
        ...

    def __repr__(self) -> str:
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
    'generator',
    'dict',
    'datetime',
    'date',
    'time',
    'timedelta',
    'url',
    'multi-host-url',
    'json',
]


class SimpleSerSchema(TypedDict, total=False):
    type: Required[ExpectedSerializationTypes]


def simple_ser_schema(type: ExpectedSerializationTypes) -> SimpleSerSchema:
    """
    Returns a schema for serialization with a custom type.

    Args:
        type: The type to use for serialization
    """
    return SimpleSerSchema(type=type)


class SerializePlainFunction(Protocol):  # pragma: no cover
    def __call__(self, __input_value: Any, __info: SerializationInfo) -> Any:
        ...


# must match `src/serializers/ob_type.rs::ObType`
JsonReturnTypes = Literal[
    'int',
    'int_subclass',
    'bool',
    'float',
    'float_subclass',
    'decimal',
    'str',
    'str_subclass',
    'bytes',
    'bytearray',
    'list',
    'tuple',
    'set',
    'frozenset',
    'generator',
    'dict',
    'datetime',
    'date',
    'time',
    'timedelta',
    'url',
    'multi_host_url',
    'dataclass',
    'model',
    'enum',
]

WhenUsed = Literal['always', 'unless-none', 'json', 'json-unless-none']
"""
Values have the following meanings:
* `'always'` means always use
* `'unless-none'` means use unless the value is `None`
* `'json'` means use when serializing to JSON
* `'json-unless-none'` means use when serializing to JSON and the value is not `None`
"""


class FunctionPlainSerSchema(TypedDict, total=False):
    type: Required[Literal['function-plain']]
    function: Required[SerializePlainFunction]
    json_return_type: JsonReturnTypes
    when_used: WhenUsed  # default: 'always'


def function_plain_ser_schema(
    function: SerializePlainFunction, *, json_return_type: JsonReturnTypes | None = None, when_used: WhenUsed = 'always'
) -> FunctionPlainSerSchema:
    """
    Returns a schema for serialization with a function.

    Args:
        function: The function to use for serialization
        json_return_type: The type that the function returns if `mode='json'`
        when_used: When the function should be called
    """
    if when_used == 'always':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return dict_not_none(
        type='function-plain', function=function, json_return_type=json_return_type, when_used=when_used
    )


class SerializeWrapHandler(Protocol):  # pragma: no cover
    def __call__(self, __input_value: Any, __index_key: int | str | None = None) -> Any:
        ...


class SerializeWrapFunction(Protocol):  # pragma: no cover
    def __call__(self, __input_value: Any, __serializer: SerializeWrapHandler, __info: SerializationInfo) -> Any:
        ...


class FunctionWrapSerSchema(TypedDict, total=False):
    type: Required[Literal['function-wrap']]
    function: Required[SerializeWrapFunction]
    schema: Required[CoreSchema]
    json_return_type: JsonReturnTypes
    when_used: WhenUsed  # default: 'always'


def function_wrap_ser_schema(
    function: SerializeWrapFunction,
    schema: CoreSchema,
    *,
    json_return_type: JsonReturnTypes | None = None,
    when_used: WhenUsed = 'always',
) -> FunctionWrapSerSchema:
    """
    Returns a schema for serialization with a function.

    Args:
        function: The function to use for serialization
        schema: The schema to use for the inner serialization
        json_return_type: The type that the function returns if `mode='json'`
        when_used: When the function should be called
    """
    if when_used == 'always':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return dict_not_none(
        type='function-wrap', schema=schema, function=function, json_return_type=json_return_type, when_used=when_used
    )


class FormatSerSchema(TypedDict, total=False):
    type: Required[Literal['format']]
    formatting_string: Required[str]
    when_used: WhenUsed  # default: 'json-unless-none'


def format_ser_schema(formatting_string: str, *, when_used: WhenUsed = 'json-unless-none') -> FormatSerSchema:
    """
    Returns a schema for serialization using python's `format` method.

    Args:
        formatting_string: String defining the format to use
        when_used: Same meaning as for [function_plain_ser_schema], but with a different default
    """
    if when_used == 'json-unless-none':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return dict_not_none(type='format', formatting_string=formatting_string, when_used=when_used)


class ToStringSerSchema(TypedDict, total=False):
    type: Required[Literal['to-string']]
    when_used: WhenUsed  # default: 'json-unless-none'


def to_string_ser_schema(*, when_used: WhenUsed = 'json-unless-none') -> ToStringSerSchema:
    """
    Returns a schema for serialization using python's `str()` / `__str__` method.

    Args:
        when_used: Same meaning as for [function_plain_ser_schema], but with a different default
    """
    s = dict(type='to-string')
    if when_used != 'json-unless-none':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        s['when_used'] = when_used
    return s  # type: ignore


class ModelSerSchema(TypedDict, total=False):
    type: Required[Literal['model']]
    cls: Required[Type[Any]]
    schema: Required[CoreSchema]


def model_ser_schema(cls: Type[Any], schema: CoreSchema) -> ModelSerSchema:
    """
    Returns a schema for serialization using a model.

    Args:
        cls: The expected class type, used to generate warnings if the wrong type is passed
        schema: Internal schema to use to serialize the model dict
    """
    return ModelSerSchema(type='model', cls=cls, schema=schema)


SerSchema = Union[
    SimpleSerSchema, FunctionPlainSerSchema, FunctionWrapSerSchema, FormatSerSchema, ToStringSerSchema, ModelSerSchema
]


class AnySchema(TypedDict, total=False):
    type: Required[Literal['any']]
    ref: str
    metadata: Any
    serialization: SerSchema


def any_schema(*, ref: str | None = None, metadata: Any = None, serialization: SerSchema | None = None) -> AnySchema:
    """
    Returns a schema that matches any value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.any_schema()
    v = SchemaValidator(schema)
    assert v.validate_python(1) == 1
    ```

    Args:
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='any', ref=ref, metadata=metadata, serialization=serialization)


class NoneSchema(TypedDict, total=False):
    type: Required[Literal['none']]
    ref: str
    metadata: Any
    serialization: SerSchema


def none_schema(*, ref: str | None = None, metadata: Any = None, serialization: SerSchema | None = None) -> NoneSchema:
    """
    Returns a schema that matches a None value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.none_schema()
    v = SchemaValidator(schema)
    assert v.validate_python(None) is None
    ```

    Args:
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='none', ref=ref, metadata=metadata, serialization=serialization)


class BoolSchema(TypedDict, total=False):
    type: Required[Literal['bool']]
    strict: bool
    ref: str
    metadata: Any
    serialization: SerSchema


def bool_schema(
    strict: bool | None = None, ref: str | None = None, metadata: Any = None, serialization: SerSchema | None = None
) -> BoolSchema:
    """
    Returns a schema that matches a bool value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.bool_schema()
    v = SchemaValidator(schema)
    assert v.validate_python('True') is True
    ```

    Args:
        strict: Whether the value should be a bool or a value that can be converted to a bool
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='bool', strict=strict, ref=ref, metadata=metadata, serialization=serialization)


class IntSchema(TypedDict, total=False):
    type: Required[Literal['int']]
    multiple_of: int
    le: int
    ge: int
    lt: int
    gt: int
    strict: bool
    ref: str
    metadata: Any
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
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> IntSchema:
    """
    Returns a schema that matches a int value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.int_schema(multiple_of=2, le=6, ge=2)
    v = SchemaValidator(schema)
    assert v.validate_python('4') == 4
    ```

    Args:
        multiple_of: The value must be a multiple of this number
        le: The value must be less than or equal to this number
        ge: The value must be greater than or equal to this number
        lt: The value must be strictly less than this number
        gt: The value must be strictly greater than this number
        strict: Whether the value should be a int or a value that can be converted to a int
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='int',
        multiple_of=multiple_of,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        strict=strict,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
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
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> FloatSchema:
    """
    Returns a schema that matches a float value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.float_schema(le=0.8, ge=0.2)
    v = SchemaValidator(schema)
    assert v.validate_python('0.5') == 0.5
    ```

    Args:
        allow_inf_nan: Whether to allow inf and nan values
        multiple_of: The value must be a multiple of this number
        le: The value must be less than or equal to this number
        ge: The value must be greater than or equal to this number
        lt: The value must be strictly less than this number
        gt: The value must be strictly greater than this number
        strict: Whether the value should be a float or a value that can be converted to a float
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
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
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def str_schema(
    *,
    pattern: str | None = None,
    max_length: int | None = None,
    min_length: int | None = None,
    strip_whitespace: bool | None = None,
    to_lower: bool | None = None,
    to_upper: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> StringSchema:
    """
    Returns a schema that matches a string value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.str_schema(max_length=10, min_length=2)
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    ```

    Args:
        pattern: A regex pattern that the value must match
        max_length: The value must be at most this length
        min_length: The value must be at least this length
        strip_whitespace: Whether to strip whitespace from the value
        to_lower: Whether to convert the value to lowercase
        to_upper: Whether to convert the value to uppercase
        strict: Whether the value should be a string or a value that can be converted to a string
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
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
        metadata=metadata,
        serialization=serialization,
    )


class BytesSchema(TypedDict, total=False):
    type: Required[Literal['bytes']]
    max_length: int
    min_length: int
    strict: bool
    ref: str
    metadata: Any
    serialization: SerSchema


def bytes_schema(
    *,
    max_length: int | None = None,
    min_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> BytesSchema:
    """
    Returns a schema that matches a bytes value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.bytes_schema(max_length=10, min_length=2)
    v = SchemaValidator(schema)
    assert v.validate_python(b'hello') == b'hello'
    ```

    Args:
        max_length: The value must be at most this length
        min_length: The value must be at least this length
        strict: Whether the value should be a bytes or a value that can be converted to a bytes
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='bytes',
        max_length=max_length,
        min_length=min_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def date_schema(
    *,
    strict: bool | None = None,
    le: date | None = None,
    ge: date | None = None,
    lt: date | None = None,
    gt: date | None = None,
    now_op: Literal['past', 'future'] | None = None,
    now_utc_offset: int | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> DateSchema:
    """
    Returns a schema that matches a date value, e.g.:

    ```py
    from datetime import date
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.date_schema(le=date(2020, 1, 1), ge=date(2019, 1, 1))
    v = SchemaValidator(schema)
    assert v.validate_python(date(2019, 6, 1)) == date(2019, 6, 1)
    ```

    Args:
        strict: Whether the value should be a date or a value that can be converted to a date
        le: The value must be less than or equal to this date
        ge: The value must be greater than or equal to this date
        lt: The value must be strictly less than this date
        gt: The value must be strictly greater than this date
        now_op: The value must be in the past or future relative to the current date
        now_utc_offset: The value must be in the past or future relative to the current date with this utc offset
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
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
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def time_schema(
    *,
    strict: bool | None = None,
    le: time | None = None,
    ge: time | None = None,
    lt: time | None = None,
    gt: time | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> TimeSchema:
    """
    Returns a schema that matches a time value, e.g.:

    ```py
    from datetime import time
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.time_schema(le=time(12, 0, 0), ge=time(6, 0, 0))
    v = SchemaValidator(schema)
    assert v.validate_python(time(9, 0, 0)) == time(9, 0, 0)
    ```

    Args:
        strict: Whether the value should be a time or a value that can be converted to a time
        le: The value must be less than or equal to this time
        ge: The value must be greater than or equal to this time
        lt: The value must be strictly less than this time
        gt: The value must be strictly greater than this time
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='time', strict=strict, le=le, ge=ge, lt=lt, gt=gt, ref=ref, metadata=metadata, serialization=serialization
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
    metadata: Any
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
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> DatetimeSchema:
    """
    Returns a schema that matches a datetime value, e.g.:

    ```py
    from datetime import datetime
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.datetime_schema()
    v = SchemaValidator(schema)
    now = datetime.now()
    assert v.validate_python(str(now)) == now
    ```

    Args:
        strict: Whether the value should be a datetime or a value that can be converted to a datetime
        le: The value must be less than or equal to this datetime
        ge: The value must be greater than or equal to this datetime
        lt: The value must be strictly less than this datetime
        gt: The value must be strictly greater than this datetime
        now_op: The value must be in the past or future relative to the current datetime
        tz_constraint: The value must be timezone aware or naive
        now_utc_offset: The value must be in the past or future relative to the current datetime with this utc offset
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
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
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def timedelta_schema(
    *,
    strict: bool | None = None,
    le: timedelta | None = None,
    ge: timedelta | None = None,
    lt: timedelta | None = None,
    gt: timedelta | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> TimedeltaSchema:
    """
    Returns a schema that matches a timedelta value, e.g.:

    ```py
    from datetime import timedelta
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.timedelta_schema(le=timedelta(days=1), ge=timedelta(days=0))
    v = SchemaValidator(schema)
    assert v.validate_python(timedelta(hours=12)) == timedelta(hours=12)
    ```

    Args:
        strict: Whether the value should be a timedelta or a value that can be converted to a timedelta
        le: The value must be less than or equal to this timedelta
        ge: The value must be greater than or equal to this timedelta
        lt: The value must be strictly less than this timedelta
        gt: The value must be strictly greater than this timedelta
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='timedelta',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class LiteralSchema(TypedDict, total=False):
    type: Required[Literal['literal']]
    expected: Required[List[Any]]
    ref: str
    metadata: Any
    serialization: SerSchema


def literal_schema(
    *expected: Any, ref: str | None = None, metadata: Any = None, serialization: SerSchema | None = None
) -> LiteralSchema:
    """
    Returns a schema that matches a literal value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.literal_schema('hello', "world")
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    ```

    Args:
        expected: The value must be one of these values
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='literal', expected=expected, ref=ref, metadata=metadata, serialization=serialization)


# must match input/parse_json.rs::JsonType::try_from
JsonType = Literal['null', 'bool', 'int', 'float', 'str', 'list', 'dict']


class IsInstanceSchema(TypedDict, total=False):
    type: Required[Literal['is-instance']]
    cls: Required[Any]
    cls_repr: str
    json_types: Set[JsonType]
    json_function: Callable[[Any], Any]
    ref: str
    metadata: Any
    serialization: SerSchema


def is_instance_schema(
    cls: Any,
    *,
    json_types: Set[JsonType] | None = None,
    json_function: Callable[[Any], Any] | None = None,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> IsInstanceSchema:
    """
    Returns a schema that checks if a value is an instance of a class, equivalent to python's `isinstnace` method, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    class A:
        pass

    schema = core_schema.is_instance_schema(cls=A)
    v = SchemaValidator(schema)
    v.validate_python(A())
    ```

    Args:
        cls: The value must be an instance of this class
        json_types: When parsing JSON directly, the value must be one of these json types
        json_function: When parsing JSON directly, If provided, the JSON value is passed to this
            function and the return value used as the output value
        cls_repr: If provided this string is used in the validator name instead of `repr(cls)`
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='is-instance',
        cls=cls,
        json_types=json_types,
        json_function=json_function,
        cls_repr=cls_repr,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class IsSubclassSchema(TypedDict, total=False):
    type: Required[Literal['is-subclass']]
    cls: Required[Type[Any]]
    cls_repr: str
    ref: str
    metadata: Any
    serialization: SerSchema


def is_subclass_schema(
    cls: Type[Any],
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> IsInstanceSchema:
    """
    Returns a schema that checks if a value is a subtype of a class, equivalent to python's `issubclass` method, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    class A:
        pass

    class B(A):
        pass

    schema = core_schema.is_subclass_schema(cls=A)
    v = SchemaValidator(schema)
    v.validate_python(B)
    ```

    Args:
        cls: The value must be a subclass of this class
        cls_repr: If provided this string is used in the validator name instead of `repr(cls)`
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='is-subclass', cls=cls, cls_repr=cls_repr, ref=ref, metadata=metadata, serialization=serialization
    )


class CallableSchema(TypedDict, total=False):
    type: Required[Literal['callable']]
    ref: str
    metadata: Any
    serialization: SerSchema


def callable_schema(
    *, ref: str | None = None, metadata: Any = None, serialization: SerSchema | None = None
) -> CallableSchema:
    """
    Returns a schema that checks if a value is callable, equivalent to python's `callable` method, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.callable_schema()
    v = SchemaValidator(schema)
    v.validate_python(min)
    ```

    Args:
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='callable', ref=ref, metadata=metadata, serialization=serialization)


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
    metadata: Any
    serialization: IncExSeqOrElseSerSchema


def list_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    allow_any_iter: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> ListSchema:
    """
    Returns a schema that matches a list value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.list_schema(core_schema.int_schema(), min_length=0, max_length=10)
    v = SchemaValidator(schema)
    assert v.validate_python(['4']) == [4]
    ```

    Args:
        items_schema: The value must be a list of items that match this schema
        min_length: The value must be a list with at least this many items
        max_length: The value must be a list with at most this many items
        strict: The value must be a list with exactly this many items
        allow_any_iter: Whether the value can be any iterable
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='list',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        allow_any_iter=allow_any_iter,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TuplePositionalSchema(TypedDict, total=False):
    type: Required[Literal['tuple']]
    mode: Required[Literal['positional']]
    items_schema: Required[List[CoreSchema]]
    extra_schema: CoreSchema
    strict: bool
    ref: str
    metadata: Any
    serialization: IncExSeqOrElseSerSchema


def tuple_positional_schema(
    *items_schema: CoreSchema,
    extra_schema: CoreSchema | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TuplePositionalSchema:
    """
    Returns a schema that matches a tuple of schemas, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.tuple_positional_schema(core_schema.int_schema(), core_schema.str_schema())
    v = SchemaValidator(schema)
    assert v.validate_python((1, 'hello')) == (1, 'hello')
    ```

    Args:
        items_schema: The value must be a tuple with items that match these schemas
        extra_schema: The value must be a tuple with items that match this schema
            This was inspired by JSON schema's `prefixItems` and `items` fields.
            In python's `typing.Tuple`, you can't specify a type for "extra" items -- they must all be the same type
            if the length is variable. So this field won't be set from a `typing.Tuple` annotation on a pydantic model.
        strict: The value must be a tuple with exactly this many items
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='tuple',
        mode='positional',
        items_schema=items_schema,
        extra_schema=extra_schema,
        strict=strict,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: IncExSeqOrElseSerSchema


def tuple_variable_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleVariableSchema:
    """
    Returns a schema that matches a tuple of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.tuple_variable_schema(items_schema=core_schema.int_schema(), min_length=0, max_length=10)
    v = SchemaValidator(schema)
    assert v.validate_python(('1', 2, 3)) == (1, 2, 3)
    ```

    Args:
        items_schema: The value must be a tuple with items that match this schema
        min_length: The value must be a tuple with at least this many items
        max_length: The value must be a tuple with at most this many items
        strict: The value must be a tuple with exactly this many items
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='tuple',
        mode='variable',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def set_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    generator_max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> SetSchema:
    """
    Returns a schema that matches a set of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.set_schema(items_schema=core_schema.int_schema(), min_length=0, max_length=10)
    v = SchemaValidator(schema)
    assert v.validate_python({1, '2', 3}) == {1, 2, 3}
    ```

    Args:
        items_schema: The value must be a set with items that match this schema
        min_length: The value must be a set with at least this many items
        max_length: The value must be a set with at most this many items
        generator_max_length: At most this many items will be read from a generator before failing validation
            This is important because generators can be infinite, and even with a `max_length` on the set,
            an infinite generator could run forever without producing more than `max_length` distinct items.
        strict: The value must be a set with exactly this many items
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='set',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        generator_max_length=generator_max_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def frozenset_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    generator_max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> FrozenSetSchema:
    """
    Returns a schema that matches a frozenset of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.frozenset_schema(items_schema=core_schema.int_schema(), min_length=0, max_length=10)
    v = SchemaValidator(schema)
    assert v.validate_python(frozenset(range(3))) == frozenset({0, 1, 2})
    ```

    Args:
        items_schema: The value must be a frozenset with items that match this schema
        min_length: The value must be a frozenset with at least this many items
        max_length: The value must be a frozenset with at most this many items
        generator_max_length: The value must generate a frozenset with at most this many items
        strict: The value must be a frozenset with exactly this many items
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='frozenset',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        generator_max_length=generator_max_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class GeneratorSchema(TypedDict, total=False):
    type: Required[Literal['generator']]
    items_schema: CoreSchema
    min_length: int
    max_length: int
    ref: str
    metadata: Any
    serialization: IncExSeqOrElseSerSchema


def generator_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> GeneratorSchema:
    """
    Returns a schema that matches a generator value, e.g.:

    ```py
    from typing import Iterator
    from pydantic_core import SchemaValidator, core_schema

    def gen() -> Iterator[int]:
        yield 1

    schema = core_schema.generator_schema(items_schema=core_schema.int_schema())
    v = SchemaValidator(schema)
    v.validate_python(gen())
    ```

    Unlike other types, validated generators do not raise ValidationErrors eagerly,
    but instead will raise a ValidationError when a violating value is actually read from the generator.
    This is to ensure that "validated" generators retain the benefit of lazy evaluation.

    Args:
        items_schema: The value must be a generator with items that match this schema
        min_length: The value must be a generator that yields at least this many items
        max_length: The value must be a generator that yields at most this many items
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='generator',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: IncExDictOrElseSerSchema


def dict_schema(
    keys_schema: CoreSchema | None = None,
    values_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> DictSchema:
    """
    Returns a schema that matches a dict value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.dict_schema(
        keys_schema=core_schema.str_schema(), values_schema=core_schema.int_schema()
    )
    v = SchemaValidator(schema)
    assert v.validate_python({'a': '1', 'b': 2}) == {'a': 1, 'b': 2}
    ```

    Args:
        keys_schema: The value must be a dict with keys that match this schema
        values_schema: The value must be a dict with values that match this schema
        min_length: The value must be a dict with at least this many items
        max_length: The value must be a dict with at most this many items
        strict: Whether the keys and values should be validated with strict mode
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='dict',
        keys_schema=keys_schema,
        values_schema=values_schema,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def function_before_schema(
    function: ValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> FunctionSchema:
    """
    Returns a schema that calls a validator function before validating the provided schema, e.g.:

    ```py
    from typing import Any
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: Any, **kwargs) -> str:
        v_str = str(v)
        assert 'hello' in v_str
        return v_str + 'world'

    schema = core_schema.function_before_schema(function=fn, schema=core_schema.str_schema())
    v = SchemaValidator(schema)
    assert v.validate_python(b"hello ") == "b'hello 'world"
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='function',
        mode='before',
        function=function,
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


def function_after_schema(
    schema: CoreSchema,
    function: ValidatorFunction,
    *,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> FunctionSchema:
    """
    Returns a schema that calls a validator function after validating the provided schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, **kwargs) -> str:
        assert 'hello' in v
        return v + 'world'

    schema = core_schema.function_after_schema(schema=core_schema.str_schema(), function=fn)
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        schema: The schema to validate before the validator function
        function: The validator function to call after the schema is validated
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='function',
        mode='after',
        function=function,
        schema=schema,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def function_wrap_schema(
    function: WrapValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> FunctionWrapSchema:
    """
    Returns a schema which calls a function with a `validator` callable argument which can
    optionally be used to call inner validation with the function logic, this is much like the
    "onion" implementation of middleware in many popular web frameworks, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, *, validator, **kwargs) -> str:
        return validator(input_value=v) + 'world'

    schema = core_schema.function_wrap_schema(function=fn, schema=core_schema.str_schema())
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='function',
        mode='wrap',
        function=function,
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class FunctionPlainSchema(TypedDict, total=False):
    type: Required[Literal['function']]
    mode: Required[Literal['plain']]
    function: Required[ValidatorFunction]
    ref: str
    metadata: Any
    serialization: SerSchema


def function_plain_schema(
    function: ValidatorFunction, *, ref: str | None = None, metadata: Any = None, serialization: SerSchema | None = None
) -> FunctionPlainSchema:
    """
    Returns a schema that uses the provided function for validation, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, **kwargs) -> str:
        assert 'hello' in v
        return v + 'world'

    schema = core_schema.function_plain_schema(function=fn)
    v = SchemaValidator(schema)
    assert v.validate_python("hello ") == 'hello world'
    ```

    Args:
        function: The validator function to call
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='function', mode='plain', function=function, ref=ref, metadata=metadata, serialization=serialization
    )


class WithDefaultSchema(TypedDict, total=False):
    type: Required[Literal['default']]
    schema: Required[CoreSchema]
    default: Any
    default_factory: Callable[[], Any]
    on_error: Literal['raise', 'omit', 'default']  # default: 'raise'
    strict: bool
    ref: str
    metadata: Any
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
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> WithDefaultSchema:
    """
    Returns a schema that adds a default value to the given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.with_default_schema(core_schema.str_schema(), default='hello')
    wrapper_schema = core_schema.typed_dict_schema(
        {'a': core_schema.typed_dict_field(schema)}
    )
    v = SchemaValidator(wrapper_schema)
    assert v.validate_python({}) == v.validate_python({'a': 'hello'})
    ```

    Args:
        schema: The schema to add a default value to
        default: The default value to use
        default_factory: A function that returns the default value to use
        on_error: What to do if the schema validation fails. One of 'raise', 'omit', 'default'
        strict: Whether the underlying schema should be validated with strict mode
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    s = dict_not_none(
        type='default',
        schema=schema,
        default_factory=default_factory,
        on_error=on_error,
        strict=strict,
        ref=ref,
        metadata=metadata,
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
    metadata: Any
    serialization: SerSchema


def nullable_schema(
    schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> NullableSchema:
    """
    Returns a schema that matches a nullable value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.nullable_schema(core_schema.str_schema())
    v = SchemaValidator(schema)
    assert v.validate_python(None) is None
    ```

    Args:
        schema: The schema to wrap
        strict: Whether the underlying schema should be validated with strict mode
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='nullable', schema=schema, strict=strict, ref=ref, metadata=metadata, serialization=serialization
    )


class UnionSchema(TypedDict, total=False):
    type: Required[Literal['union']]
    choices: Required[List[CoreSchema]]
    # default true, whether to automatically collapse unions with one element to the inner validator
    auto_collapse: bool
    custom_error_type: str
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    strict: bool
    ref: str
    metadata: Any
    serialization: SerSchema


def union_schema(
    *choices: CoreSchema,
    auto_collapse: bool | None = None,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, str | int] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> UnionSchema:
    """
    Returns a schema that matches a union value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.union_schema(core_schema.str_schema(), core_schema.int_schema())
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    assert v.validate_python(1) == 1
    ```

    Args:
        *choices: The schemas to match
        auto_collapse: whether to automatically collapse unions with one element to the inner validator, default true
        custom_error_type: The custom error type to use if the validation fails
        custom_error_message: The custom error message to use if the validation fails
        custom_error_context: The custom error context to use if the validation fails
        strict: Whether the underlying schemas should be validated with strict mode
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='union',
        choices=choices,
        auto_collapse=auto_collapse,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TaggedUnionSchema(TypedDict, total=False):
    type: Required[Literal['tagged-union']]
    choices: Required[Dict[Union[str, int], Union[str, int, CoreSchema]]]
    discriminator: Required[
        Union[str, List[Union[str, int]], List[List[Union[str, int]]], Callable[[Any], Optional[str]]]
    ]
    custom_error_type: str
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    strict: bool
    from_attributes: bool  # default: True
    ref: str
    metadata: Any
    serialization: SerSchema


def tagged_union_schema(
    choices: Dict[Union[int, str], int | str | CoreSchema],
    discriminator: str | list[str | int] | list[list[str | int]] | Callable[[Any], str | None],
    *,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, int | str | float] | None = None,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> TaggedUnionSchema:
    """
    Returns a schema that matches a tagged union value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    apple_schema = core_schema.typed_dict_schema(
        {
            'foo': core_schema.typed_dict_field(core_schema.str_schema()),
            'bar': core_schema.typed_dict_field(core_schema.int_schema()),
        }
    )
    banana_schema = core_schema.typed_dict_schema(
        {
            'foo': core_schema.typed_dict_field(core_schema.str_schema()),
            'spam': core_schema.typed_dict_field(core_schema.list_schema(items_schema=core_schema.int_schema())),
        }
    )
    schema = core_schema.tagged_union_schema(
        choices={
            'apple': apple_schema,
            'banana': banana_schema,
        },
        discriminator='foo',
    )
    v = SchemaValidator(schema)
    assert v.validate_python({'foo': 'apple', 'bar': '123'}) == {'foo': 'apple', 'bar': 123}
    assert v.validate_python({'foo': 'banana', 'spam': [1, 2, 3]}) == {'foo': 'banana', 'spam': [1, 2, 3]}
    ```

    Args:
        choices: The schemas to match
            When retrieving a schema from `choices` using the discriminator value, if the value is a str,
            it should be fed back into the `choices` map until a schema is obtained
            (This approach is to prevent multiple ownership of a single schema in Rust)
        discriminator: The discriminator to use to determine the schema to use
            * If `discriminator` is a str, it is the name of the attribute to use as the discriminator
            * If `discriminator` is a list of int/str, it should be used as a "path" to access the discriminator
            * If `discriminator` is a list of lists, each inner list is a path, and the first path that exists is used
            * If `discriminator` is a callable, it should return the discriminator when called on the value to validate
        custom_error_type: The custom error type to use if the validation fails
        custom_error_message: The custom error message to use if the validation fails
        custom_error_context: The custom error context to use if the validation fails
        strict: Whether the underlying schemas should be validated with strict mode
        from_attributes: Whether to use the attributes of the object to retrieve the discriminator value
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='tagged-union',
        choices=choices,
        discriminator=discriminator,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        strict=strict,
        from_attributes=from_attributes,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class ChainSchema(TypedDict, total=False):
    type: Required[Literal['chain']]
    steps: Required[List[CoreSchema]]
    ref: str
    metadata: Any
    serialization: SerSchema


def chain_schema(
    *steps: CoreSchema, ref: str | None = None, metadata: Any = None, serialization: SerSchema | None = None
) -> ChainSchema:
    """
    Returns a schema that chains the provided validation schemas, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, **kwargs) -> str:
        assert 'hello' in v
        return v + ' world'

    fn_schema = core_schema.function_plain_schema(function=fn)
    schema = core_schema.chain_schema(fn_schema, fn_schema, fn_schema, core_schema.str_schema())
    v = SchemaValidator(schema)
    assert v.validate_python("hello") == 'hello world world world'
    ```

    Args:
        steps: The schemas to chain
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='chain', steps=steps, ref=ref, metadata=metadata, serialization=serialization)


class LaxOrStrictSchema(TypedDict, total=False):
    type: Required[Literal['lax-or-strict']]
    lax_schema: Required[CoreSchema]
    strict_schema: Required[CoreSchema]
    strict: bool
    ref: str
    metadata: Any
    serialization: SerSchema


def lax_or_strict_schema(
    lax_schema: CoreSchema,
    strict_schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> LaxOrStrictSchema:
    """
    Returns a schema that uses the lax or strict schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, **kwargs) -> str:
        assert 'hello' in v
        return v + ' world'

    lax_schema = core_schema.int_schema(strict=False)
    strict_schema = core_schema.int_schema(strict=True)

    schema = core_schema.lax_or_strict_schema(lax_schema=lax_schema, strict_schema=strict_schema, strict=True)
    v = SchemaValidator(schema)
    assert v.validate_python(123) == 123

    schema = core_schema.lax_or_strict_schema(lax_schema=lax_schema, strict_schema=strict_schema, strict=False)
    v = SchemaValidator(schema)
    assert v.validate_python('123') == 123
    ```

    Args:
        lax_schema: The lax schema to use
        strict_schema: The strict schema to use
        strict: Whether the strict schema should be used
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='lax-or-strict',
        lax_schema=lax_schema,
        strict_schema=strict_schema,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class TypedDictField(TypedDict, total=False):
    schema: Required[CoreSchema]
    required: bool
    validation_alias: Union[str, List[Union[str, int]], List[List[Union[str, int]]]]
    serialization_alias: str
    serialization_exclude: bool  # default: False
    frozen: bool
    metadata: Any


def typed_dict_field(
    schema: CoreSchema,
    *,
    required: bool | None = None,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    frozen: bool | None = None,
    metadata: Any = None,
) -> TypedDictField:
    """
    Returns a schema that matches a typed dict field, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    field = core_schema.typed_dict_field(schema=core_schema.int_schema(), required=True)
    ```

    Args:
        schema: The schema to use for the field
        required: Whether the field is required
        alias: The alias(es) to use for the field
        frozen: Whether the field is frozen
    """
    return dict_not_none(
        schema=schema,
        required=required,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        frozen=frozen,
        metadata=metadata,
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
    metadata: Any
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
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> TypedDictSchema:
    """
    Returns a schema that matches a typed dict, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    wrapper_schema = core_schema.typed_dict_schema(
        {'a': core_schema.typed_dict_field(core_schema.str_schema())}
    )
    v = SchemaValidator(wrapper_schema)
    assert v.validate_python({'a': 'hello'}) == {'a': 'hello'}
    ```

    Args:
        fields: The fields to use for the typed dict
        strict: Whether the typed dict is strict
        extra_validator: The extra validator to use for the typed dict
        return_fields_set: Whether the typed dict should return a fields set
        ref: See [TODO] for details
        metadata: See [TODO] for details
        extra_behavior: The extra behavior to use for the typed dict
        total: Whether the typed dict is total
        populate_by_name: Whether the typed dict should populate by name
        from_attributes: Whether the typed dict should be populated from attributes
    """
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
        metadata=metadata,
        serialization=serialization,
    )


class ModelSchema(TypedDict, total=False):
    type: Required[Literal['model']]
    cls: Required[Type[Any]]
    schema: Required[CoreSchema]
    call_after_init: str
    strict: bool
    config: CoreConfig
    ref: str
    metadata: Any
    serialization: SerSchema


def model_schema(
    cls: Type[Any],
    schema: CoreSchema,
    *,
    call_after_init: str | None = None,
    strict: bool | None = None,
    config: CoreConfig | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> ModelSchema:
    """
    A model schema generally contains a typed-dict schema.
    It will run the typed dict validator, then create a new class
    and set the dict and fields set returned from the typed dict validator
    to `__dict__` and `__fields_set__` respectively.

    Example:

    ```py
    from pydantic_core import CoreConfig, SchemaValidator, core_schema

    class MyModel:
        __slots__ = '__dict__', '__fields_set__'

    schema = core_schema.model_schema(
        cls=MyModel,
        config=CoreConfig(str_max_length=5),
        schema=core_schema.typed_dict_schema(
            fields={'a': core_schema.typed_dict_field(core_schema.str_schema())},
        ),
    )
    v = SchemaValidator(schema)
    assert v.isinstance_python({'a': 'hello'}) is True
    assert v.isinstance_python({'a': 'too long'}) is False
    ```

    Args:
        cls: The class to use for the model
        schema: The schema to use for the model
        call_after_init: The call after init to use for the model
        strict: Whether the model is strict
        config: The config to use for the model
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='model',
        cls=cls,
        schema=schema,
        call_after_init=call_after_init,
        strict=strict,
        config=config,
        ref=ref,
        metadata=metadata,
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
    """
    Returns a schema that matches an argument parameter, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    param = core_schema.arguments_parameter(name='a', schema=core_schema.str_schema(), mode='positional_only')
    ```

    Args:
        name: The name to use for the argument parameter
        schema: The schema to use for the argument parameter
        mode: The mode to use for the argument parameter
        alias: The alias to use for the argument parameter
    """
    return dict_not_none(name=name, schema=schema, mode=mode, alias=alias)


class ArgumentsSchema(TypedDict, total=False):
    type: Required[Literal['arguments']]
    arguments_schema: Required[List[ArgumentsParameter]]
    populate_by_name: bool
    var_args_schema: CoreSchema
    var_kwargs_schema: CoreSchema
    ref: str
    metadata: Any
    serialization: SerSchema


def arguments_schema(
    *arguments: ArgumentsParameter,
    populate_by_name: bool | None = None,
    var_args_schema: CoreSchema | None = None,
    var_kwargs_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> ArgumentsSchema:
    """
    Returns a schema that matches an arguments schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    param_a = core_schema.arguments_parameter(name='a', schema=core_schema.str_schema(), mode='positional_only')
    param_b = core_schema.arguments_parameter(name='b', schema=core_schema.bool_schema(), mode='positional_only')
    schema = core_schema.arguments_schema(param_a, param_b)
    v = SchemaValidator(schema)
    v.validate_python({'__args__': ('hello', True), '__kwargs__': {}})
    ```

    Args:
        arguments: The arguments to use for the arguments schema
        populate_by_name: Whether to populate by name
        var_args_schema: The variable args schema to use for the arguments schema
        var_kwargs_schema: The variable kwargs schema to use for the arguments schema
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='arguments',
        arguments_schema=arguments,
        populate_by_name=populate_by_name,
        var_args_schema=var_args_schema,
        var_kwargs_schema=var_kwargs_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class CallSchema(TypedDict, total=False):
    type: Required[Literal['call']]
    arguments_schema: Required[CoreSchema]
    function: Required[Callable[..., Any]]
    return_schema: CoreSchema
    ref: str
    metadata: Any
    serialization: SerSchema


def call_schema(
    arguments: CoreSchema,
    function: Callable[..., Any],
    *,
    return_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> CallSchema:
    """
    Returns a schema that matches an arguments schema, then calls a function, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    param_a = core_schema.arguments_parameter(name='a', schema=core_schema.str_schema(), mode='positional_only')
    param_b = core_schema.arguments_parameter(name='b', schema=core_schema.bool_schema(), mode='positional_only')
    args_schema = core_schema.arguments_schema(param_a, param_b)

    schema = core_schema.call_schema(
        arguments=args_schema,
        function=lambda a, b: a + str(not b),
        return_schema=core_schema.str_schema(),
    )
    v = SchemaValidator(schema)
    assert v.validate_python((('hello', True))) == 'helloFalse'
    ```

    Args:
        arguments: The arguments to use for the arguments schema
        function: The function to use for the call schema
        return_schema: The return schema to use for the call schema
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='call',
        arguments_schema=arguments,
        function=function,
        return_schema=return_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class CustomErrorSchema(TypedDict, total=False):
    type: Required[Literal['custom-error']]
    schema: Required[CoreSchema]
    custom_error_type: Required[str]
    custom_error_message: str
    custom_error_context: Dict[str, Union[str, int, float]]
    ref: str
    metadata: Any
    serialization: SerSchema


def custom_error_schema(
    schema: CoreSchema,
    custom_error_type: str,
    *,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, str | int | float] | None = None,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> CustomErrorSchema:
    """
    Returns a schema that matches a custom error value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.custom_error_schema(
        schema=core_schema.int_schema(), custom_error_type='MyError', custom_error_message="Error msg"
    )
    v = SchemaValidator(schema)
    v.validate_python(1)
    ```

    Args:
        schema: The schema to use for the custom error schema
        custom_error_type: The custom error type to use for the custom error schema
        custom_error_message: The custom error message to use for the custom error schema
        custom_error_context: The custom error context to use for the custom error schema
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(
        type='custom-error',
        schema=schema,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )


class JsonSchema(TypedDict, total=False):
    type: Required[Literal['json']]
    schema: CoreSchema
    ref: str
    metadata: Any
    serialization: SerSchema


def json_schema(
    schema: CoreSchema | None = None,
    *,
    ref: str | None = None,
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> JsonSchema:
    """
    Returns a schema that matches a JSON value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    dict_schema = core_schema.typed_dict_schema(
        {
            'field_a': core_schema.typed_dict_field(core_schema.str_schema()),
            'field_b': core_schema.typed_dict_field(core_schema.bool_schema()),
        }
    )

    class MyModel:
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: bool

    json_schema = core_schema.json_schema(schema=dict_schema)
    schema = core_schema.model_schema(cls=MyModel, schema=json_schema)
    v = SchemaValidator(schema)
    m = v.validate_python('{"field_a": "hello", "field_b": true}')
    assert isinstance(m, MyModel)
    ```

    Args:
        schema: The schema to use for the JSON schema
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='json', schema=schema, ref=ref, metadata=metadata, serialization=serialization)


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
    metadata: Any
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
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> UrlSchema:
    """
    Returns a schema that matches a URL value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.url_schema()
    v = SchemaValidator(schema)
    # TODO: Assert this is equal to a constructed URL object
    v.validate_python('https://example.com')
    ```

    Args:
        max_length: The maximum length of the URL
        allowed_schemes: The allowed URL schemes
        host_required: Whether the URL must have a host
        default_host: The default host to use if the URL does not have a host
        default_port: The default port to use if the URL does not have a port
        default_path: The default path to use if the URL does not have a path
        strict: Whether to use strict URL parsing
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
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
        metadata=metadata,
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
    metadata: Any
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
    metadata: Any = None,
    serialization: SerSchema | None = None,
) -> MultiHostUrlSchema:
    """
    Returns a schema that matches a URL value with possibly multiple hosts, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.multi_host_url_schema()
    v = SchemaValidator(schema)
    # TODO: Assert this is equal to a constructed URL object
    v.validate_python('redis://localhost,0.0.0.0,127.0.0.1')
    ```

    Args:
        max_length: The maximum length of the URL
        allowed_schemes: The allowed URL schemes
        host_required: Whether the URL must have a host
        default_host: The default host to use if the URL does not have a host
        default_port: The default port to use if the URL does not have a port
        default_path: The default path to use if the URL does not have a path
        strict: Whether to use strict URL parsing
        ref: See [TODO] for details
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
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
        metadata=metadata,
        serialization=serialization,
    )


class DefinitionsSchema(TypedDict, total=False):
    type: Required[Literal['definitions']]
    schema: Required[CoreSchema]
    definitions: Required[List[CoreSchema]]
    metadata: Any
    serialization: SerSchema


def definitions_schema(schema: CoreSchema, definitions: list[CoreSchema]) -> DefinitionsSchema:
    """
    Build a schema that contains both an inner schema and a list of definitions which can be used
    within the inner schema.

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema = core_schema.definitions_schema(
        core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
        [core_schema.int_schema(ref='foobar')],
    )
    v = SchemaValidator(schema)
    assert v.validate_python([1, 2, '3']) == [1, 2, 3]
    ```

    Args:
        schema: The inner schema
        definitions: List of definitions which can be referenced within inner schema
    """
    return DefinitionsSchema(type='definitions', schema=schema, definitions=definitions)


class DefinitionReferenceSchema(TypedDict, total=False):
    type: Required[Literal['definition-ref']]
    schema_ref: Required[str]
    metadata: Any
    serialization: SerSchema


def definition_reference_schema(
    schema_ref: str, metadata: Any = None, serialization: SerSchema | None = None
) -> DefinitionReferenceSchema:
    """
    Returns a schema that points to a schema stored in "definitions", this is useful for nested recursive
    models and also when you want to define validators separately from the main schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema
    schema_definition = core_schema.definition_reference_schema('list-schema')
    schema = core_schema.list_schema(items_schema=schema_definition, ref='list-schema')
    v = SchemaValidator(schema)
    assert v.validate_python([[]]) == [[]]
    ```

    Args:
        schema_ref: The schema ref to use for the definition reference schema
        metadata: See [TODO] for details
        serialization: Custom serialization schema
    """
    return dict_not_none(type='definition-ref', schema_ref=schema_ref, metadata=metadata, serialization=serialization)


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
    ModelSchema,
    ArgumentsSchema,
    CallSchema,
    CustomErrorSchema,
    JsonSchema,
    UrlSchema,
    MultiHostUrlSchema,
    DefinitionsSchema,
    DefinitionReferenceSchema,
]

# to update this, call `pytest -k test_core_schema_type_literal` and copy the output
CoreSchemaType = Literal[
    'any',
    'none',
    'bool',
    'int',
    'float',
    'str',
    'bytes',
    'date',
    'time',
    'datetime',
    'timedelta',
    'literal',
    'is-instance',
    'is-subclass',
    'callable',
    'list',
    'tuple',
    'set',
    'frozenset',
    'generator',
    'dict',
    'function',
    'default',
    'nullable',
    'union',
    'tagged-union',
    'chain',
    'lax-or-strict',
    'typed-dict',
    'model',
    'arguments',
    'call',
    'custom-error',
    'json',
    'url',
    'multi-host-url',
    'definitions',
    'definition-ref',
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
