This module contains definitions to build schemas which `pydantic_core` can validate and serialize.

## WhenUsed

```python
WhenUsed = Literal[
    "always", "unless-none", "json", "json-unless-none"
]

```

Values have the following meanings:

- `'always'` means always use
- `'unless-none'` means use unless the value is `None`
- `'json'` means use when serializing to JSON
- `'json-unless-none'` means use when serializing to JSON and the value is not `None`

## CoreConfig

Bases: `TypedDict`

Base class for schema configuration options.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `title` | `str` | The name of the configuration. | | `strict` | `bool` | Whether the configuration should strictly adhere to specified rules. | | `extra_fields_behavior` | `ExtraBehavior` | The behavior for handling extra fields. | | `typed_dict_total` | `bool` | Whether the TypedDict should be considered total. Default is True. | | `from_attributes` | `bool` | Whether to use attributes for models, dataclasses, and tagged union keys. | | `loc_by_alias` | `bool` | Whether to use the used alias (or first alias for "field required" errors) instead of field_names to construct error locs. Default is True. | | `revalidate_instances` | `Literal['always', 'never', 'subclass-instances']` | Whether instances of models and dataclasses should re-validate. Default is 'never'. | | `validate_default` | `bool` | Whether to validate default values during validation. Default is False. | | `str_max_length` | `int` | The maximum length for string fields. | | `str_min_length` | `int` | The minimum length for string fields. | | `str_strip_whitespace` | `bool` | Whether to strip whitespace from string fields. | | `str_to_lower` | `bool` | Whether to convert string fields to lowercase. | | `str_to_upper` | `bool` | Whether to convert string fields to uppercase. | | `allow_inf_nan` | `bool` | Whether to allow infinity and NaN values for float fields. Default is True. | | `ser_json_timedelta` | `Literal['iso8601', 'float']` | The serialization option for timedelta values. Default is 'iso8601'. Note that if ser_json_temporal is set, then this param will be ignored. | | `ser_json_temporal` | `Literal['iso8601', 'seconds', 'milliseconds']` | The serialization option for datetime like values. Default is 'iso8601'. The types this covers are datetime, date, time and timedelta. If this is set, it will take precedence over ser_json_timedelta | | `ser_json_bytes` | `Literal['utf8', 'base64', 'hex']` | The serialization option for bytes values. Default is 'utf8'. | | `ser_json_inf_nan` | `Literal['null', 'constants', 'strings']` | The serialization option for infinity and NaN values in float fields. Default is 'null'. | | `val_json_bytes` | `Literal['utf8', 'base64', 'hex']` | The validation option for bytes values, complementing ser_json_bytes. Default is 'utf8'. | | `hide_input_in_errors` | `bool` | Whether to hide input data from ValidationError representation. | | `validation_error_cause` | `bool` | Whether to add user-python excs to the cause of a ValidationError. Requires exceptiongroup backport pre Python 3.11. | | `coerce_numbers_to_str` | `bool` | Whether to enable coercion of any Number type to str (not applicable in strict mode). | | `regex_engine` | `Literal['rust-regex', 'python-re']` | The regex engine to use for regex pattern validation. Default is 'rust-regex'. See StringSchema. | | `cache_strings` | `Union[bool, Literal['all', 'keys', 'none']]` | Whether to cache strings. Default is True, True or 'all' is required to cache strings during general validation since validators don't know if they're in a key or a value. | | `validate_by_alias` | `bool` | Whether to use the field's alias when validating against the provided input data. Default is True. | | `validate_by_name` | `bool` | Whether to use the field's name when validating against the provided input data. Default is False. Replacement for populate_by_name. | | `serialize_by_alias` | `bool` | Whether to serialize by alias. Default is False, expected to change to True in V3. | | `polymorphic_serialization` | `bool` | Whether to enable polymorphic serialization for models and dataclasses. Default is False. | | `url_preserve_empty_path` | `bool` | Whether to preserve empty URL paths when validating values for a URL type. Defaults to False. |

## SerializationInfo

Bases: `Protocol[ContextT]`

Extra data used during serialization.

### include

```python
include: IncExCall

```

The `include` argument set during serialization.

### exclude

```python
exclude: IncExCall

```

The `exclude` argument set during serialization.

### context

```python
context: ContextT

```

The current serialization context.

### mode

```python
mode: Literal['python', 'json'] | str

```

The serialization mode set during serialization.

### by_alias

```python
by_alias: bool

```

The `by_alias` argument set during serialization.

### exclude_unset

```python
exclude_unset: bool

```

The `exclude_unset` argument set during serialization.

### exclude_defaults

```python
exclude_defaults: bool

```

The `exclude_defaults` argument set during serialization.

### exclude_none

```python
exclude_none: bool

```

The `exclude_none` argument set during serialization.

### exclude_computed_fields

```python
exclude_computed_fields: bool

```

The `exclude_computed_fields` argument set during serialization.

### serialize_as_any

```python
serialize_as_any: bool

```

The `serialize_as_any` argument set during serialization.

### polymorphic_serialization

```python
polymorphic_serialization: bool | None

```

The `polymorphic_serialization` argument set during serialization, if any.

### round_trip

```python
round_trip: bool

```

The `round_trip` argument set during serialization.

## FieldSerializationInfo

Bases: `SerializationInfo[ContextT]`, `Protocol`

Extra data used during field serialization.

### field_name

```python
field_name: str

```

The name of the current field being serialized.

## ValidationInfo

Bases: `Protocol[ContextT]`

Extra data used during validation.

### context

```python
context: ContextT

```

The current validation context.

### config

```python
config: CoreConfig | None

```

The CoreConfig that applies to this validation.

### mode

```python
mode: Literal['python', 'json']

```

The type of input data we are currently validating.

### data

```python
data: dict[str, Any]

```

The data being validated for this model.

### field_name

```python
field_name: str | None

```

The name of the current field being validated if this validator is attached to a model field.

## simple_ser_schema

```python
simple_ser_schema(
    type: ExpectedSerializationTypes,
) -> SimpleSerSchema

```

Returns a schema for serialization with a custom type.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `type` | `ExpectedSerializationTypes` | The type to use for serialization | *required* |

Source code in `pydantic_core/core_schema.py`

```python
def simple_ser_schema(type: ExpectedSerializationTypes) -> SimpleSerSchema:
    """
    Returns a schema for serialization with a custom type.

    Args:
        type: The type to use for serialization
    """
    return SimpleSerSchema(type=type)

```

## plain_serializer_function_ser_schema

```python
plain_serializer_function_ser_schema(
    function: SerializerFunction,
    *,
    is_field_serializer: bool | None = None,
    info_arg: bool | None = None,
    return_schema: CoreSchema | None = None,
    when_used: WhenUsed = "always"
) -> PlainSerializerFunctionSerSchema

```

Returns a schema for serialization with a function, can be either a "general" or "field" function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `SerializerFunction` | The function to use for serialization | *required* | | `is_field_serializer` | `bool | None` | Whether the serializer is for a field, e.g. takes model as the first argument, and info includes field_name | `None` | | `info_arg` | `bool | None` | Whether the function takes an info argument | `None` | | `return_schema` | `CoreSchema | None` | Schema to use for serializing return value | `None` | | `when_used` | `WhenUsed` | When the function should be called | `'always'` |

Source code in `pydantic_core/core_schema.py`

```python
def plain_serializer_function_ser_schema(
    function: SerializerFunction,
    *,
    is_field_serializer: bool | None = None,
    info_arg: bool | None = None,
    return_schema: CoreSchema | None = None,
    when_used: WhenUsed = 'always',
) -> PlainSerializerFunctionSerSchema:
    """
    Returns a schema for serialization with a function, can be either a "general" or "field" function.

    Args:
        function: The function to use for serialization
        is_field_serializer: Whether the serializer is for a field, e.g. takes `model` as the first argument,
            and `info` includes `field_name`
        info_arg: Whether the function takes an `info` argument
        return_schema: Schema to use for serializing return value
        when_used: When the function should be called
    """
    if when_used == 'always':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return _dict_not_none(
        type='function-plain',
        function=function,
        is_field_serializer=is_field_serializer,
        info_arg=info_arg,
        return_schema=return_schema,
        when_used=when_used,
    )

```

## wrap_serializer_function_ser_schema

```python
wrap_serializer_function_ser_schema(
    function: WrapSerializerFunction,
    *,
    is_field_serializer: bool | None = None,
    info_arg: bool | None = None,
    schema: CoreSchema | None = None,
    return_schema: CoreSchema | None = None,
    when_used: WhenUsed = "always"
) -> WrapSerializerFunctionSerSchema

```

Returns a schema for serialization with a wrap function, can be either a "general" or "field" function.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `WrapSerializerFunction` | The function to use for serialization | *required* | | `is_field_serializer` | `bool | None` | Whether the serializer is for a field, e.g. takes model as the first argument, and info includes field_name | `None` | | `info_arg` | `bool | None` | Whether the function takes an info argument | `None` | | `schema` | `CoreSchema | None` | The schema to use for the inner serialization | `None` | | `return_schema` | `CoreSchema | None` | Schema to use for serializing return value | `None` | | `when_used` | `WhenUsed` | When the function should be called | `'always'` |

Source code in `pydantic_core/core_schema.py`

```python
def wrap_serializer_function_ser_schema(
    function: WrapSerializerFunction,
    *,
    is_field_serializer: bool | None = None,
    info_arg: bool | None = None,
    schema: CoreSchema | None = None,
    return_schema: CoreSchema | None = None,
    when_used: WhenUsed = 'always',
) -> WrapSerializerFunctionSerSchema:
    """
    Returns a schema for serialization with a wrap function, can be either a "general" or "field" function.

    Args:
        function: The function to use for serialization
        is_field_serializer: Whether the serializer is for a field, e.g. takes `model` as the first argument,
            and `info` includes `field_name`
        info_arg: Whether the function takes an `info` argument
        schema: The schema to use for the inner serialization
        return_schema: Schema to use for serializing return value
        when_used: When the function should be called
    """
    if when_used == 'always':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return _dict_not_none(
        type='function-wrap',
        function=function,
        is_field_serializer=is_field_serializer,
        info_arg=info_arg,
        schema=schema,
        return_schema=return_schema,
        when_used=when_used,
    )

```

## format_ser_schema

```python
format_ser_schema(
    formatting_string: str,
    *,
    when_used: WhenUsed = "json-unless-none"
) -> FormatSerSchema

```

Returns a schema for serialization using python's `format` method.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `formatting_string` | `str` | String defining the format to use | *required* | | `when_used` | `WhenUsed` | Same meaning as for [general_function_plain_ser_schema], but with a different default | `'json-unless-none'` |

Source code in `pydantic_core/core_schema.py`

```python
def format_ser_schema(formatting_string: str, *, when_used: WhenUsed = 'json-unless-none') -> FormatSerSchema:
    """
    Returns a schema for serialization using python's `format` method.

    Args:
        formatting_string: String defining the format to use
        when_used: Same meaning as for [general_function_plain_ser_schema], but with a different default
    """
    if when_used == 'json-unless-none':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        when_used = None  # type: ignore
    return _dict_not_none(type='format', formatting_string=formatting_string, when_used=when_used)

```

## to_string_ser_schema

```python
to_string_ser_schema(
    *, when_used: WhenUsed = "json-unless-none"
) -> ToStringSerSchema

```

Returns a schema for serialization using python's `str()` / `__str__` method.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `when_used` | `WhenUsed` | Same meaning as for [general_function_plain_ser_schema], but with a different default | `'json-unless-none'` |

Source code in `pydantic_core/core_schema.py`

```python
def to_string_ser_schema(*, when_used: WhenUsed = 'json-unless-none') -> ToStringSerSchema:
    """
    Returns a schema for serialization using python's `str()` / `__str__` method.

    Args:
        when_used: Same meaning as for [general_function_plain_ser_schema], but with a different default
    """
    s = dict(type='to-string')
    if when_used != 'json-unless-none':
        # just to avoid extra elements in schema, and to use the actual default defined in rust
        s['when_used'] = when_used
    return s  # type: ignore

```

## model_ser_schema

```python
model_ser_schema(
    cls: type[Any], schema: CoreSchema
) -> ModelSerSchema

```

Returns a schema for serialization using a model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cls` | `type[Any]` | The expected class type, used to generate warnings if the wrong type is passed | *required* | | `schema` | `CoreSchema` | Internal schema to use to serialize the model dict | *required* |

Source code in `pydantic_core/core_schema.py`

```python
def model_ser_schema(cls: type[Any], schema: CoreSchema) -> ModelSerSchema:
    """
    Returns a schema for serialization using a model.

    Args:
        cls: The expected class type, used to generate warnings if the wrong type is passed
        schema: Internal schema to use to serialize the model dict
    """
    return ModelSerSchema(type='model', cls=cls, schema=schema)

```

## invalid_schema

```python
invalid_schema(
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> InvalidSchema

```

Returns an invalid schema, used to indicate that a schema is invalid.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` |

Source code in `pydantic_core/core_schema.py`

```python
def invalid_schema(ref: str | None = None, metadata: dict[str, Any] | None = None) -> InvalidSchema:
    """
    Returns an invalid schema, used to indicate that a schema is invalid.

    Args:
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """

    return _dict_not_none(type='invalid', ref=ref, metadata=metadata)

```

## computed_field

```python
computed_field(
    property_name: str,
    return_schema: CoreSchema,
    *,
    alias: str | None = None,
    metadata: dict[str, Any] | None = None
) -> ComputedField

```

ComputedFields are properties of a model or dataclass that are included in serialization.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `property_name` | `str` | The name of the property on the model or dataclass | *required* | | `return_schema` | `CoreSchema` | The schema used for the type returned by the computed field | *required* | | `alias` | `str | None` | The name to use in the serialized output | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` |

Source code in `pydantic_core/core_schema.py`

```python
def computed_field(
    property_name: str, return_schema: CoreSchema, *, alias: str | None = None, metadata: dict[str, Any] | None = None
) -> ComputedField:
    """
    ComputedFields are properties of a model or dataclass that are included in serialization.

    Args:
        property_name: The name of the property on the model or dataclass
        return_schema: The schema used for the type returned by the computed field
        alias: The name to use in the serialized output
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """
    return _dict_not_none(
        type='computed-field', property_name=property_name, return_schema=return_schema, alias=alias, metadata=metadata
    )

```

## any_schema

```python
any_schema(
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> AnySchema

```

Returns a schema that matches any value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.any_schema()
v = SchemaValidator(schema)
assert v.validate_python(1) == 1

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def any_schema(
    *, ref: str | None = None, metadata: dict[str, Any] | None = None, serialization: SerSchema | None = None
) -> AnySchema:
    """
    Returns a schema that matches any value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.any_schema()
    v = SchemaValidator(schema)
    assert v.validate_python(1) == 1
    ```

    Args:
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='any', ref=ref, metadata=metadata, serialization=serialization)

````

## none_schema

```python
none_schema(
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> NoneSchema

```

Returns a schema that matches a None value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.none_schema()
v = SchemaValidator(schema)
assert v.validate_python(None) is None

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def none_schema(
    *, ref: str | None = None, metadata: dict[str, Any] | None = None, serialization: SerSchema | None = None
) -> NoneSchema:
    """
    Returns a schema that matches a None value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.none_schema()
    v = SchemaValidator(schema)
    assert v.validate_python(None) is None
    ```

    Args:
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='none', ref=ref, metadata=metadata, serialization=serialization)

````

## bool_schema

```python
bool_schema(
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> BoolSchema

```

Returns a schema that matches a bool value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.bool_schema()
v = SchemaValidator(schema)
assert v.validate_python('True') is True

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether the value should be a bool or a value that can be converted to a bool | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def bool_schema(
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='bool', strict=strict, ref=ref, metadata=metadata, serialization=serialization)

````

## int_schema

```python
int_schema(
    *,
    multiple_of: int | None = None,
    le: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    gt: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> IntSchema

```

Returns a schema that matches a int value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.int_schema(multiple_of=2, le=6, ge=2)
v = SchemaValidator(schema)
assert v.validate_python('4') == 4

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `multiple_of` | `int | None` | The value must be a multiple of this number | `None` | | `le` | `int | None` | The value must be less than or equal to this number | `None` | | `ge` | `int | None` | The value must be greater than or equal to this number | `None` | | `lt` | `int | None` | The value must be strictly less than this number | `None` | | `gt` | `int | None` | The value must be strictly greater than this number | `None` | | `strict` | `bool | None` | Whether the value should be a int or a value that can be converted to a int | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def int_schema(
    *,
    multiple_of: int | None = None,
    le: int | None = None,
    ge: int | None = None,
    lt: int | None = None,
    gt: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
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

````

## float_schema

```python
float_schema(
    *,
    allow_inf_nan: bool | None = None,
    multiple_of: float | None = None,
    le: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    gt: float | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> FloatSchema

```

Returns a schema that matches a float value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.float_schema(le=0.8, ge=0.2)
v = SchemaValidator(schema)
assert v.validate_python('0.5') == 0.5

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `allow_inf_nan` | `bool | None` | Whether to allow inf and nan values | `None` | | `multiple_of` | `float | None` | The value must be a multiple of this number | `None` | | `le` | `float | None` | The value must be less than or equal to this number | `None` | | `ge` | `float | None` | The value must be greater than or equal to this number | `None` | | `lt` | `float | None` | The value must be strictly less than this number | `None` | | `gt` | `float | None` | The value must be strictly greater than this number | `None` | | `strict` | `bool | None` | Whether the value should be a float or a value that can be converted to a float | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
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
    metadata: dict[str, Any] | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
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

````

## decimal_schema

```python
decimal_schema(
    *,
    allow_inf_nan: bool | None = None,
    multiple_of: Decimal | None = None,
    le: Decimal | None = None,
    ge: Decimal | None = None,
    lt: Decimal | None = None,
    gt: Decimal | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> DecimalSchema

```

Returns a schema that matches a decimal value, e.g.:

```py
from decimal import Decimal
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.decimal_schema(le=0.8, ge=0.2)
v = SchemaValidator(schema)
assert v.validate_python('0.5') == Decimal('0.5')

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `allow_inf_nan` | `bool | None` | Whether to allow inf and nan values | `None` | | `multiple_of` | `Decimal | None` | The value must be a multiple of this number | `None` | | `le` | `Decimal | None` | The value must be less than or equal to this number | `None` | | `ge` | `Decimal | None` | The value must be greater than or equal to this number | `None` | | `lt` | `Decimal | None` | The value must be strictly less than this number | `None` | | `gt` | `Decimal | None` | The value must be strictly greater than this number | `None` | | `max_digits` | `int | None` | The maximum number of decimal digits allowed | `None` | | `decimal_places` | `int | None` | The maximum number of decimal places allowed | `None` | | `strict` | `bool | None` | Whether the value should be a float or a value that can be converted to a float | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def decimal_schema(
    *,
    allow_inf_nan: bool | None = None,
    multiple_of: Decimal | None = None,
    le: Decimal | None = None,
    ge: Decimal | None = None,
    lt: Decimal | None = None,
    gt: Decimal | None = None,
    max_digits: int | None = None,
    decimal_places: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DecimalSchema:
    """
    Returns a schema that matches a decimal value, e.g.:

    ```py
    from decimal import Decimal
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.decimal_schema(le=0.8, ge=0.2)
    v = SchemaValidator(schema)
    assert v.validate_python('0.5') == Decimal('0.5')
    ```

    Args:
        allow_inf_nan: Whether to allow inf and nan values
        multiple_of: The value must be a multiple of this number
        le: The value must be less than or equal to this number
        ge: The value must be greater than or equal to this number
        lt: The value must be strictly less than this number
        gt: The value must be strictly greater than this number
        max_digits: The maximum number of decimal digits allowed
        decimal_places: The maximum number of decimal places allowed
        strict: Whether the value should be a float or a value that can be converted to a float
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='decimal',
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        max_digits=max_digits,
        decimal_places=decimal_places,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## complex_schema

```python
complex_schema(
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> ComplexSchema

```

Returns a schema that matches a complex value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.complex_schema()
v = SchemaValidator(schema)
assert v.validate_python('1+2j') == complex(1, 2)
assert v.validate_python(complex(1, 2)) == complex(1, 2)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether the value should be a complex object instance or a value that can be converted to a complex object | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def complex_schema(
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ComplexSchema:
    """
    Returns a schema that matches a complex value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.complex_schema()
    v = SchemaValidator(schema)
    assert v.validate_python('1+2j') == complex(1, 2)
    assert v.validate_python(complex(1, 2)) == complex(1, 2)
    ```

    Args:
        strict: Whether the value should be a complex object instance or a value that can be converted to a complex object
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='complex',
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## str_schema

```python
str_schema(
    *,
    pattern: str | Pattern[str] | None = None,
    max_length: int | None = None,
    min_length: int | None = None,
    strip_whitespace: bool | None = None,
    to_lower: bool | None = None,
    to_upper: bool | None = None,
    regex_engine: (
        Literal["rust-regex", "python-re"] | None
    ) = None,
    strict: bool | None = None,
    coerce_numbers_to_str: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> StringSchema

```

Returns a schema that matches a string value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.str_schema(max_length=10, min_length=2)
v = SchemaValidator(schema)
assert v.validate_python('hello') == 'hello'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `pattern` | `str | Pattern[str] | None` | A regex pattern that the value must match | `None` | | `max_length` | `int | None` | The value must be at most this length | `None` | | `min_length` | `int | None` | The value must be at least this length | `None` | | `strip_whitespace` | `bool | None` | Whether to strip whitespace from the value | `None` | | `to_lower` | `bool | None` | Whether to convert the value to lowercase | `None` | | `to_upper` | `bool | None` | Whether to convert the value to uppercase | `None` | | `regex_engine` | `Literal['rust-regex', 'python-re'] | None` | The regex engine to use for pattern validation. Default is 'rust-regex'. - rust-regex uses the regex Rust crate, which is non-backtracking and therefore more DDoS resistant, but does not support all regex features. - python-re use the re module, which supports all regex features, but may be slower. | `None` | | `strict` | `bool | None` | Whether the value should be a string or a value that can be converted to a string | `None` | | `coerce_numbers_to_str` | `bool | None` | Whether to enable coercion of any Number type to str (not applicable in strict mode). | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def str_schema(
    *,
    pattern: str | Pattern[str] | None = None,
    max_length: int | None = None,
    min_length: int | None = None,
    strip_whitespace: bool | None = None,
    to_lower: bool | None = None,
    to_upper: bool | None = None,
    regex_engine: Literal['rust-regex', 'python-re'] | None = None,
    strict: bool | None = None,
    coerce_numbers_to_str: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        regex_engine: The regex engine to use for pattern validation. Default is 'rust-regex'.
            - `rust-regex` uses the [`regex`](https://docs.rs/regex) Rust
              crate, which is non-backtracking and therefore more DDoS
              resistant, but does not support all regex features.
            - `python-re` use the [`re`](https://docs.python.org/3/library/re.html) module,
              which supports all regex features, but may be slower.
        strict: Whether the value should be a string or a value that can be converted to a string
        coerce_numbers_to_str: Whether to enable coercion of any `Number` type to `str` (not applicable in `strict` mode).
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='str',
        pattern=pattern,
        max_length=max_length,
        min_length=min_length,
        strip_whitespace=strip_whitespace,
        to_lower=to_lower,
        to_upper=to_upper,
        regex_engine=regex_engine,
        strict=strict,
        coerce_numbers_to_str=coerce_numbers_to_str,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## bytes_schema

```python
bytes_schema(
    *,
    max_length: int | None = None,
    min_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> BytesSchema

```

Returns a schema that matches a bytes value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.bytes_schema(max_length=10, min_length=2)
v = SchemaValidator(schema)
assert v.validate_python(b'hello') == b'hello'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `max_length` | `int | None` | The value must be at most this length | `None` | | `min_length` | `int | None` | The value must be at least this length | `None` | | `strict` | `bool | None` | Whether the value should be a bytes or a value that can be converted to a bytes | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def bytes_schema(
    *,
    max_length: int | None = None,
    min_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='bytes',
        max_length=max_length,
        min_length=min_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## date_schema

```python
date_schema(
    *,
    strict: bool | None = None,
    le: date | None = None,
    ge: date | None = None,
    lt: date | None = None,
    gt: date | None = None,
    now_op: Literal["past", "future"] | None = None,
    now_utc_offset: int | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> DateSchema

```

Returns a schema that matches a date value, e.g.:

```py
from datetime import date
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.date_schema(le=date(2020, 1, 1), ge=date(2019, 1, 1))
v = SchemaValidator(schema)
assert v.validate_python(date(2019, 6, 1)) == date(2019, 6, 1)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether the value should be a date or a value that can be converted to a date | `None` | | `le` | `date | None` | The value must be less than or equal to this date | `None` | | `ge` | `date | None` | The value must be greater than or equal to this date | `None` | | `lt` | `date | None` | The value must be strictly less than this date | `None` | | `gt` | `date | None` | The value must be strictly greater than this date | `None` | | `now_op` | `Literal['past', 'future'] | None` | The value must be in the past or future relative to the current date | `None` | | `now_utc_offset` | `int | None` | The value must be in the past or future relative to the current date with this utc offset | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
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
    metadata: dict[str, Any] | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
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

````

## time_schema

```python
time_schema(
    *,
    strict: bool | None = None,
    le: time | None = None,
    ge: time | None = None,
    lt: time | None = None,
    gt: time | None = None,
    tz_constraint: (
        Literal["aware", "naive"] | int | None
    ) = None,
    microseconds_precision: Literal[
        "truncate", "error"
    ] = "truncate",
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> TimeSchema

```

Returns a schema that matches a time value, e.g.:

```py
from datetime import time
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.time_schema(le=time(12, 0, 0), ge=time(6, 0, 0))
v = SchemaValidator(schema)
assert v.validate_python(time(9, 0, 0)) == time(9, 0, 0)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether the value should be a time or a value that can be converted to a time | `None` | | `le` | `time | None` | The value must be less than or equal to this time | `None` | | `ge` | `time | None` | The value must be greater than or equal to this time | `None` | | `lt` | `time | None` | The value must be strictly less than this time | `None` | | `gt` | `time | None` | The value must be strictly greater than this time | `None` | | `tz_constraint` | `Literal['aware', 'naive'] | int | None` | The value must be timezone aware or naive, or an int to indicate required tz offset | `None` | | `microseconds_precision` | `Literal['truncate', 'error']` | The behavior when seconds have more than 6 digits or microseconds is too large | `'truncate'` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def time_schema(
    *,
    strict: bool | None = None,
    le: time | None = None,
    ge: time | None = None,
    lt: time | None = None,
    gt: time | None = None,
    tz_constraint: Literal['aware', 'naive'] | int | None = None,
    microseconds_precision: Literal['truncate', 'error'] = 'truncate',
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        tz_constraint: The value must be timezone aware or naive, or an int to indicate required tz offset
        microseconds_precision: The behavior when seconds have more than 6 digits or microseconds is too large
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='time',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        tz_constraint=tz_constraint,
        microseconds_precision=microseconds_precision,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## datetime_schema

```python
datetime_schema(
    *,
    strict: bool | None = None,
    le: datetime | None = None,
    ge: datetime | None = None,
    lt: datetime | None = None,
    gt: datetime | None = None,
    now_op: Literal["past", "future"] | None = None,
    tz_constraint: (
        Literal["aware", "naive"] | int | None
    ) = None,
    now_utc_offset: int | None = None,
    microseconds_precision: Literal[
        "truncate", "error"
    ] = "truncate",
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> DatetimeSchema

```

Returns a schema that matches a datetime value, e.g.:

```py
from datetime import datetime
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.datetime_schema()
v = SchemaValidator(schema)
now = datetime.now()
assert v.validate_python(str(now)) == now

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether the value should be a datetime or a value that can be converted to a datetime | `None` | | `le` | `datetime | None` | The value must be less than or equal to this datetime | `None` | | `ge` | `datetime | None` | The value must be greater than or equal to this datetime | `None` | | `lt` | `datetime | None` | The value must be strictly less than this datetime | `None` | | `gt` | `datetime | None` | The value must be strictly greater than this datetime | `None` | | `now_op` | `Literal['past', 'future'] | None` | The value must be in the past or future relative to the current datetime | `None` | | `tz_constraint` | `Literal['aware', 'naive'] | int | None` | The value must be timezone aware or naive, or an int to indicate required tz offset TODO: use of a tzinfo where offset changes based on the datetime is not yet supported | `None` | | `now_utc_offset` | `int | None` | The value must be in the past or future relative to the current datetime with this utc offset | `None` | | `microseconds_precision` | `Literal['truncate', 'error']` | The behavior when seconds have more than 6 digits or microseconds is too large | `'truncate'` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def datetime_schema(
    *,
    strict: bool | None = None,
    le: datetime | None = None,
    ge: datetime | None = None,
    lt: datetime | None = None,
    gt: datetime | None = None,
    now_op: Literal['past', 'future'] | None = None,
    tz_constraint: Literal['aware', 'naive'] | int | None = None,
    now_utc_offset: int | None = None,
    microseconds_precision: Literal['truncate', 'error'] = 'truncate',
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        tz_constraint: The value must be timezone aware or naive, or an int to indicate required tz offset
            TODO: use of a tzinfo where offset changes based on the datetime is not yet supported
        now_utc_offset: The value must be in the past or future relative to the current datetime with this utc offset
        microseconds_precision: The behavior when seconds have more than 6 digits or microseconds is too large
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='datetime',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        now_op=now_op,
        tz_constraint=tz_constraint,
        now_utc_offset=now_utc_offset,
        microseconds_precision=microseconds_precision,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## timedelta_schema

```python
timedelta_schema(
    *,
    strict: bool | None = None,
    le: timedelta | None = None,
    ge: timedelta | None = None,
    lt: timedelta | None = None,
    gt: timedelta | None = None,
    microseconds_precision: Literal[
        "truncate", "error"
    ] = "truncate",
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> TimedeltaSchema

```

Returns a schema that matches a timedelta value, e.g.:

```py
from datetime import timedelta
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.timedelta_schema(le=timedelta(days=1), ge=timedelta(days=0))
v = SchemaValidator(schema)
assert v.validate_python(timedelta(hours=12)) == timedelta(hours=12)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether the value should be a timedelta or a value that can be converted to a timedelta | `None` | | `le` | `timedelta | None` | The value must be less than or equal to this timedelta | `None` | | `ge` | `timedelta | None` | The value must be greater than or equal to this timedelta | `None` | | `lt` | `timedelta | None` | The value must be strictly less than this timedelta | `None` | | `gt` | `timedelta | None` | The value must be strictly greater than this timedelta | `None` | | `microseconds_precision` | `Literal['truncate', 'error']` | The behavior when seconds have more than 6 digits or microseconds is too large | `'truncate'` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def timedelta_schema(
    *,
    strict: bool | None = None,
    le: timedelta | None = None,
    ge: timedelta | None = None,
    lt: timedelta | None = None,
    gt: timedelta | None = None,
    microseconds_precision: Literal['truncate', 'error'] = 'truncate',
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        microseconds_precision: The behavior when seconds have more than 6 digits or microseconds is too large
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='timedelta',
        strict=strict,
        le=le,
        ge=ge,
        lt=lt,
        gt=gt,
        microseconds_precision=microseconds_precision,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## literal_schema

```python
literal_schema(
    expected: list[Any],
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> LiteralSchema

```

Returns a schema that matches a literal value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.literal_schema(['hello', 'world'])
v = SchemaValidator(schema)
assert v.validate_python('hello') == 'hello'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `expected` | `list[Any]` | The value must be one of these values | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def literal_schema(
    expected: list[Any],
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> LiteralSchema:
    """
    Returns a schema that matches a literal value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.literal_schema(['hello', 'world'])
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    ```

    Args:
        expected: The value must be one of these values
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='literal', expected=expected, ref=ref, metadata=metadata, serialization=serialization)

````

## enum_schema

```python
enum_schema(
    cls: Any,
    members: list[Any],
    *,
    sub_type: Literal["str", "int", "float"] | None = None,
    missing: Callable[[Any], Any] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> EnumSchema

```

Returns a schema that matches an enum value, e.g.:

```py
from enum import Enum
from pydantic_core import SchemaValidator, core_schema

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

schema = core_schema.enum_schema(Color, list(Color.__members__.values()))
v = SchemaValidator(schema)
assert v.validate_python(2) is Color.GREEN

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cls` | `Any` | The enum class | *required* | | `members` | `list[Any]` | The members of the enum, generally list(MyEnum.__members__.values()) | *required* | | `sub_type` | `Literal['str', 'int', 'float'] | None` | The type of the enum, either 'str' or 'int' or None for plain enums | `None` | | `missing` | `Callable[[Any], Any] | None` | A function to use when the value is not found in the enum, from _missing_ | `None` | | `strict` | `bool | None` | Whether to use strict mode, defaults to False | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def enum_schema(
    cls: Any,
    members: list[Any],
    *,
    sub_type: Literal['str', 'int', 'float'] | None = None,
    missing: Callable[[Any], Any] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> EnumSchema:
    """
    Returns a schema that matches an enum value, e.g.:

    ```py
    from enum import Enum
    from pydantic_core import SchemaValidator, core_schema

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    schema = core_schema.enum_schema(Color, list(Color.__members__.values()))
    v = SchemaValidator(schema)
    assert v.validate_python(2) is Color.GREEN
    ```

    Args:
        cls: The enum class
        members: The members of the enum, generally `list(MyEnum.__members__.values())`
        sub_type: The type of the enum, either 'str' or 'int' or None for plain enums
        missing: A function to use when the value is not found in the enum, from `_missing_`
        strict: Whether to use strict mode, defaults to False
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='enum',
        cls=cls,
        members=members,
        sub_type=sub_type,
        missing=missing,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## missing_sentinel_schema

```python
missing_sentinel_schema(
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> MissingSentinelSchema

```

Returns a schema for the `MISSING` sentinel.

Source code in `pydantic_core/core_schema.py`

```python
def missing_sentinel_schema(
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> MissingSentinelSchema:
    """Returns a schema for the `MISSING` sentinel."""

    return _dict_not_none(
        type='missing-sentinel',
        metadata=metadata,
        serialization=serialization,
    )

```

## is_instance_schema

```python
is_instance_schema(
    cls: Any,
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> IsInstanceSchema

```

Returns a schema that checks if a value is an instance of a class, equivalent to python's `isinstance` method, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

class A:
    pass

schema = core_schema.is_instance_schema(cls=A)
v = SchemaValidator(schema)
v.validate_python(A())

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cls` | `Any` | The value must be an instance of this class | *required* | | `cls_repr` | `str | None` | If provided this string is used in the validator name instead of repr(cls) | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def is_instance_schema(
    cls: Any,
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> IsInstanceSchema:
    """
    Returns a schema that checks if a value is an instance of a class, equivalent to python's `isinstance` method, e.g.:

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
        cls_repr: If provided this string is used in the validator name instead of `repr(cls)`
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='is-instance', cls=cls, cls_repr=cls_repr, ref=ref, metadata=metadata, serialization=serialization
    )

````

## is_subclass_schema

```python
is_subclass_schema(
    cls: type[Any],
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> IsInstanceSchema

```

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

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cls` | `type[Any]` | The value must be a subclass of this class | *required* | | `cls_repr` | `str | None` | If provided this string is used in the validator name instead of repr(cls) | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def is_subclass_schema(
    cls: type[Any],
    *,
    cls_repr: str | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='is-subclass', cls=cls, cls_repr=cls_repr, ref=ref, metadata=metadata, serialization=serialization
    )

````

## callable_schema

```python
callable_schema(
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> CallableSchema

```

Returns a schema that checks if a value is callable, equivalent to python's `callable` method, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.callable_schema()
v = SchemaValidator(schema)
v.validate_python(min)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def callable_schema(
    *, ref: str | None = None, metadata: dict[str, Any] | None = None, serialization: SerSchema | None = None
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='callable', ref=ref, metadata=metadata, serialization=serialization)

````

## list_schema

```python
list_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None
) -> ListSchema

```

Returns a schema that matches a list value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.list_schema(core_schema.int_schema(), min_length=0, max_length=10)
v = SchemaValidator(schema)
assert v.validate_python(['4']) == [4]

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `items_schema` | `CoreSchema | None` | The value must be a list of items that match this schema | `None` | | `min_length` | `int | None` | The value must be a list with at least this many items | `None` | | `max_length` | `int | None` | The value must be a list with at most this many items | `None` | | `fail_fast` | `bool | None` | Stop validation on the first error | `None` | | `strict` | `bool | None` | The value must be a list with exactly this many items | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `IncExSeqOrElseSerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def list_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        fail_fast: Stop validation on the first error
        strict: The value must be a list with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='list',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## tuple_positional_schema

```python
tuple_positional_schema(
    items_schema: list[CoreSchema],
    *,
    extras_schema: CoreSchema | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None
) -> TupleSchema

```

Returns a schema that matches a tuple of schemas, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.tuple_positional_schema(
    [core_schema.int_schema(), core_schema.str_schema()]
)
v = SchemaValidator(schema)
assert v.validate_python((1, 'hello')) == (1, 'hello')

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `items_schema` | `list[CoreSchema]` | The value must be a tuple with items that match these schemas | *required* | | `extras_schema` | `CoreSchema | None` | The value must be a tuple with items that match this schema This was inspired by JSON schema's prefixItems and items fields. In python's typing.Tuple, you can't specify a type for "extra" items -- they must all be the same type if the length is variable. So this field won't be set from a typing.Tuple annotation on a pydantic model. | `None` | | `strict` | `bool | None` | The value must be a tuple with exactly this many items | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `IncExSeqOrElseSerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def tuple_positional_schema(
    items_schema: list[CoreSchema],
    *,
    extras_schema: CoreSchema | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleSchema:
    """
    Returns a schema that matches a tuple of schemas, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.tuple_positional_schema(
        [core_schema.int_schema(), core_schema.str_schema()]
    )
    v = SchemaValidator(schema)
    assert v.validate_python((1, 'hello')) == (1, 'hello')
    ```

    Args:
        items_schema: The value must be a tuple with items that match these schemas
        extras_schema: The value must be a tuple with items that match this schema
            This was inspired by JSON schema's `prefixItems` and `items` fields.
            In python's `typing.Tuple`, you can't specify a type for "extra" items -- they must all be the same type
            if the length is variable. So this field won't be set from a `typing.Tuple` annotation on a pydantic model.
        strict: The value must be a tuple with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    if extras_schema is not None:
        variadic_item_index = len(items_schema)
        items_schema = items_schema + [extras_schema]
    else:
        variadic_item_index = None
    return tuple_schema(
        items_schema=items_schema,
        variadic_item_index=variadic_item_index,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## tuple_variable_schema

```python
tuple_variable_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None
) -> TupleSchema

```

Returns a schema that matches a tuple of a given schema, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.tuple_variable_schema(
    items_schema=core_schema.int_schema(), min_length=0, max_length=10
)
v = SchemaValidator(schema)
assert v.validate_python(('1', 2, 3)) == (1, 2, 3)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `items_schema` | `CoreSchema | None` | The value must be a tuple with items that match this schema | `None` | | `min_length` | `int | None` | The value must be a tuple with at least this many items | `None` | | `max_length` | `int | None` | The value must be a tuple with at most this many items | `None` | | `strict` | `bool | None` | The value must be a tuple with exactly this many items | `None` | | `ref` | `str | None` | Optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `IncExSeqOrElseSerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def tuple_variable_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleSchema:
    """
    Returns a schema that matches a tuple of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.tuple_variable_schema(
        items_schema=core_schema.int_schema(), min_length=0, max_length=10
    )
    v = SchemaValidator(schema)
    assert v.validate_python(('1', 2, 3)) == (1, 2, 3)
    ```

    Args:
        items_schema: The value must be a tuple with items that match this schema
        min_length: The value must be a tuple with at least this many items
        max_length: The value must be a tuple with at most this many items
        strict: The value must be a tuple with exactly this many items
        ref: Optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return tuple_schema(
        items_schema=[items_schema or any_schema()],
        variadic_item_index=0,
        min_length=min_length,
        max_length=max_length,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## tuple_schema

```python
tuple_schema(
    items_schema: list[CoreSchema],
    *,
    variadic_item_index: int | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None
) -> TupleSchema

```

Returns a schema that matches a tuple of schemas, with an optional variadic item, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.tuple_schema(
    [core_schema.int_schema(), core_schema.str_schema(), core_schema.float_schema()],
    variadic_item_index=1,
)
v = SchemaValidator(schema)
assert v.validate_python((1, 'hello', 'world', 1.5)) == (1, 'hello', 'world', 1.5)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `items_schema` | `list[CoreSchema]` | The value must be a tuple with items that match these schemas | *required* | | `variadic_item_index` | `int | None` | The index of the schema in items_schema to be treated as variadic (following PEP 646) | `None` | | `min_length` | `int | None` | The value must be a tuple with at least this many items | `None` | | `max_length` | `int | None` | The value must be a tuple with at most this many items | `None` | | `fail_fast` | `bool | None` | Stop validation on the first error | `None` | | `strict` | `bool | None` | The value must be a tuple with exactly this many items | `None` | | `ref` | `str | None` | Optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `IncExSeqOrElseSerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def tuple_schema(
    items_schema: list[CoreSchema],
    *,
    variadic_item_index: int | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None,
) -> TupleSchema:
    """
    Returns a schema that matches a tuple of schemas, with an optional variadic item, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.tuple_schema(
        [core_schema.int_schema(), core_schema.str_schema(), core_schema.float_schema()],
        variadic_item_index=1,
    )
    v = SchemaValidator(schema)
    assert v.validate_python((1, 'hello', 'world', 1.5)) == (1, 'hello', 'world', 1.5)
    ```

    Args:
        items_schema: The value must be a tuple with items that match these schemas
        variadic_item_index: The index of the schema in `items_schema` to be treated as variadic (following PEP 646)
        min_length: The value must be a tuple with at least this many items
        max_length: The value must be a tuple with at most this many items
        fail_fast: Stop validation on the first error
        strict: The value must be a tuple with exactly this many items
        ref: Optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='tuple',
        items_schema=items_schema,
        variadic_item_index=variadic_item_index,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## set_schema

```python
set_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> SetSchema

```

Returns a schema that matches a set of a given schema, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.set_schema(
    items_schema=core_schema.int_schema(), min_length=0, max_length=10
)
v = SchemaValidator(schema)
assert v.validate_python({1, '2', 3}) == {1, 2, 3}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `items_schema` | `CoreSchema | None` | The value must be a set with items that match this schema | `None` | | `min_length` | `int | None` | The value must be a set with at least this many items | `None` | | `max_length` | `int | None` | The value must be a set with at most this many items | `None` | | `fail_fast` | `bool | None` | Stop validation on the first error | `None` | | `strict` | `bool | None` | The value must be a set with exactly this many items | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def set_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> SetSchema:
    """
    Returns a schema that matches a set of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.set_schema(
        items_schema=core_schema.int_schema(), min_length=0, max_length=10
    )
    v = SchemaValidator(schema)
    assert v.validate_python({1, '2', 3}) == {1, 2, 3}
    ```

    Args:
        items_schema: The value must be a set with items that match this schema
        min_length: The value must be a set with at least this many items
        max_length: The value must be a set with at most this many items
        fail_fast: Stop validation on the first error
        strict: The value must be a set with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='set',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## frozenset_schema

```python
frozenset_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> FrozenSetSchema

```

Returns a schema that matches a frozenset of a given schema, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.frozenset_schema(
    items_schema=core_schema.int_schema(), min_length=0, max_length=10
)
v = SchemaValidator(schema)
assert v.validate_python(frozenset(range(3))) == frozenset({0, 1, 2})

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `items_schema` | `CoreSchema | None` | The value must be a frozenset with items that match this schema | `None` | | `min_length` | `int | None` | The value must be a frozenset with at least this many items | `None` | | `max_length` | `int | None` | The value must be a frozenset with at most this many items | `None` | | `fail_fast` | `bool | None` | Stop validation on the first error | `None` | | `strict` | `bool | None` | The value must be a frozenset with exactly this many items | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def frozenset_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> FrozenSetSchema:
    """
    Returns a schema that matches a frozenset of a given schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.frozenset_schema(
        items_schema=core_schema.int_schema(), min_length=0, max_length=10
    )
    v = SchemaValidator(schema)
    assert v.validate_python(frozenset(range(3))) == frozenset({0, 1, 2})
    ```

    Args:
        items_schema: The value must be a frozenset with items that match this schema
        min_length: The value must be a frozenset with at least this many items
        max_length: The value must be a frozenset with at most this many items
        fail_fast: Stop validation on the first error
        strict: The value must be a frozenset with exactly this many items
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='frozenset',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## generator_schema

```python
generator_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: IncExSeqOrElseSerSchema | None = None
) -> GeneratorSchema

```

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

Unlike other types, validated generators do not raise ValidationErrors eagerly, but instead will raise a ValidationError when a violating value is actually read from the generator. This is to ensure that "validated" generators retain the benefit of lazy evaluation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `items_schema` | `CoreSchema | None` | The value must be a generator with items that match this schema | `None` | | `min_length` | `int | None` | The value must be a generator that yields at least this many items | `None` | | `max_length` | `int | None` | The value must be a generator that yields at most this many items | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `IncExSeqOrElseSerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def generator_schema(
    items_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='generator',
        items_schema=items_schema,
        min_length=min_length,
        max_length=max_length,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## dict_schema

```python
dict_schema(
    keys_schema: CoreSchema | None = None,
    values_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> DictSchema

```

Returns a schema that matches a dict value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.dict_schema(
    keys_schema=core_schema.str_schema(), values_schema=core_schema.int_schema()
)
v = SchemaValidator(schema)
assert v.validate_python({'a': '1', 'b': 2}) == {'a': 1, 'b': 2}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `keys_schema` | `CoreSchema | None` | The value must be a dict with keys that match this schema | `None` | | `values_schema` | `CoreSchema | None` | The value must be a dict with values that match this schema | `None` | | `min_length` | `int | None` | The value must be a dict with at least this many items | `None` | | `max_length` | `int | None` | The value must be a dict with at most this many items | `None` | | `fail_fast` | `bool | None` | Stop validation on the first error | `None` | | `strict` | `bool | None` | Whether the keys and values should be validated with strict mode | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def dict_schema(
    keys_schema: CoreSchema | None = None,
    values_schema: CoreSchema | None = None,
    *,
    min_length: int | None = None,
    max_length: int | None = None,
    fail_fast: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        fail_fast: Stop validation on the first error
        strict: Whether the keys and values should be validated with strict mode
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='dict',
        keys_schema=keys_schema,
        values_schema=values_schema,
        min_length=min_length,
        max_length=max_length,
        fail_fast=fail_fast,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## no_info_before_validator_function

```python
no_info_before_validator_function(
    function: NoInfoValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> BeforeValidatorFunctionSchema

```

Returns a schema that calls a validator function before validating, no `info` argument is provided, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: bytes) -> str:
    return v.decode() + 'world'

func_schema = core_schema.no_info_before_validator_function(
    function=fn, schema=core_schema.str_schema()
)
schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

v = SchemaValidator(schema)
assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `NoInfoValidatorFunction` | The validator function to call | *required* | | `schema` | `CoreSchema` | The schema to validate the output of the validator function | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `json_schema_input_schema` | `CoreSchema | None` | The core schema to be used to generate the corresponding JSON Schema input type | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def no_info_before_validator_function(
    function: NoInfoValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> BeforeValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function before validating, no `info` argument is provided, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: bytes) -> str:
        return v.decode() + 'world'

    func_schema = core_schema.no_info_before_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        json_schema_input_schema: The core schema to be used to generate the corresponding JSON Schema input type
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-before',
        function={'type': 'no-info', 'function': function},
        schema=schema,
        ref=ref,
        json_schema_input_schema=json_schema_input_schema,
        metadata=metadata,
        serialization=serialization,
    )

````

## with_info_before_validator_function

```python
with_info_before_validator_function(
    function: WithInfoValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> BeforeValidatorFunctionSchema

```

Returns a schema that calls a validator function before validation, the function is called with an `info` argument, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: bytes, info: core_schema.ValidationInfo) -> str:
    assert info.data is not None
    assert info.field_name is not None
    return v.decode() + 'world'

func_schema = core_schema.with_info_before_validator_function(
    function=fn, schema=core_schema.str_schema()
)
schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

v = SchemaValidator(schema)
assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `WithInfoValidatorFunction` | The validator function to call | *required* | | `field_name` | `str | None` | The name of the field this validator is applied to, if any (deprecated) | `None` | | `schema` | `CoreSchema` | The schema to validate the output of the validator function | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `json_schema_input_schema` | `CoreSchema | None` | The core schema to be used to generate the corresponding JSON Schema input type | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def with_info_before_validator_function(
    function: WithInfoValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> BeforeValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function before validation, the function is called with
    an `info` argument, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: bytes, info: core_schema.ValidationInfo) -> str:
        assert info.data is not None
        assert info.field_name is not None
        return v.decode() + 'world'

    func_schema = core_schema.with_info_before_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call
        field_name: The name of the field this validator is applied to, if any (deprecated)
        schema: The schema to validate the output of the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        json_schema_input_schema: The core schema to be used to generate the corresponding JSON Schema input type
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    if field_name is not None:
        warnings.warn(
            'The `field_name` argument on `with_info_before_validator_function` is deprecated, it will be passed to the function through `ValidationState` instead.',
            DeprecationWarning,
            stacklevel=2,
        )

    return _dict_not_none(
        type='function-before',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        schema=schema,
        ref=ref,
        json_schema_input_schema=json_schema_input_schema,
        metadata=metadata,
        serialization=serialization,
    )

````

## no_info_after_validator_function

```python
no_info_after_validator_function(
    function: NoInfoValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> AfterValidatorFunctionSchema

```

Returns a schema that calls a validator function after validating, no `info` argument is provided, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: str) -> str:
    return v + 'world'

func_schema = core_schema.no_info_after_validator_function(fn, core_schema.str_schema())
schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

v = SchemaValidator(schema)
assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `NoInfoValidatorFunction` | The validator function to call after the schema is validated | *required* | | `schema` | `CoreSchema` | The schema to validate before the validator function | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `json_schema_input_schema` | `CoreSchema | None` | The core schema to be used to generate the corresponding JSON Schema input type | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def no_info_after_validator_function(
    function: NoInfoValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> AfterValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function after validating, no `info` argument is provided, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str) -> str:
        return v + 'world'

    func_schema = core_schema.no_info_after_validator_function(fn, core_schema.str_schema())
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call after the schema is validated
        schema: The schema to validate before the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        json_schema_input_schema: The core schema to be used to generate the corresponding JSON Schema input type
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-after',
        function={'type': 'no-info', 'function': function},
        schema=schema,
        ref=ref,
        json_schema_input_schema=json_schema_input_schema,
        metadata=metadata,
        serialization=serialization,
    )

````

## with_info_after_validator_function

```python
with_info_after_validator_function(
    function: WithInfoValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> AfterValidatorFunctionSchema

```

Returns a schema that calls a validator function after validation, the function is called with an `info` argument, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: str, info: core_schema.ValidationInfo) -> str:
    assert info.data is not None
    assert info.field_name is not None
    return v + 'world'

func_schema = core_schema.with_info_after_validator_function(
    function=fn, schema=core_schema.str_schema()
)
schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

v = SchemaValidator(schema)
assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `WithInfoValidatorFunction` | The validator function to call after the schema is validated | *required* | | `schema` | `CoreSchema` | The schema to validate before the validator function | *required* | | `field_name` | `str | None` | The name of the field this validator is applied to, if any (deprecated) | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def with_info_after_validator_function(
    function: WithInfoValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> AfterValidatorFunctionSchema:
    """
    Returns a schema that calls a validator function after validation, the function is called with
    an `info` argument, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert info.data is not None
        assert info.field_name is not None
        return v + 'world'

    func_schema = core_schema.with_info_after_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    schema = core_schema.typed_dict_schema({'a': core_schema.typed_dict_field(func_schema)})

    v = SchemaValidator(schema)
    assert v.validate_python({'a': b'hello '}) == {'a': 'hello world'}
    ```

    Args:
        function: The validator function to call after the schema is validated
        schema: The schema to validate before the validator function
        field_name: The name of the field this validator is applied to, if any (deprecated)
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    if field_name is not None:
        warnings.warn(
            'The `field_name` argument on `with_info_after_validator_function` is deprecated, it will be passed to the function through `ValidationState` instead.',
            DeprecationWarning,
            stacklevel=2,
        )

    return _dict_not_none(
        type='function-after',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        schema=schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## no_info_wrap_validator_function

```python
no_info_wrap_validator_function(
    function: NoInfoWrapValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> WrapValidatorFunctionSchema

```

Returns a schema which calls a function with a `validator` callable argument which can optionally be used to call inner validation with the function logic, this is much like the "onion" implementation of middleware in many popular web frameworks, no `info` argument is passed, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(
    v: str,
    validator: core_schema.ValidatorFunctionWrapHandler,
) -> str:
    return validator(input_value=v) + 'world'

schema = core_schema.no_info_wrap_validator_function(
    function=fn, schema=core_schema.str_schema()
)
v = SchemaValidator(schema)
assert v.validate_python('hello ') == 'hello world'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `NoInfoWrapValidatorFunction` | The validator function to call | *required* | | `schema` | `CoreSchema` | The schema to validate the output of the validator function | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `json_schema_input_schema` | `CoreSchema | None` | The core schema to be used to generate the corresponding JSON Schema input type | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def no_info_wrap_validator_function(
    function: NoInfoWrapValidatorFunction,
    schema: CoreSchema,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> WrapValidatorFunctionSchema:
    """
    Returns a schema which calls a function with a `validator` callable argument which can
    optionally be used to call inner validation with the function logic, this is much like the
    "onion" implementation of middleware in many popular web frameworks, no `info` argument is passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(
        v: str,
        validator: core_schema.ValidatorFunctionWrapHandler,
    ) -> str:
        return validator(input_value=v) + 'world'

    schema = core_schema.no_info_wrap_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        ref: optional unique identifier of the schema, used to reference the schema in other places
        json_schema_input_schema: The core schema to be used to generate the corresponding JSON Schema input type
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-wrap',
        function={'type': 'no-info', 'function': function},
        schema=schema,
        json_schema_input_schema=json_schema_input_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## with_info_wrap_validator_function

```python
with_info_wrap_validator_function(
    function: WithInfoWrapValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> WrapValidatorFunctionSchema

```

Returns a schema which calls a function with a `validator` callable argument which can optionally be used to call inner validation with the function logic, this is much like the "onion" implementation of middleware in many popular web frameworks, an `info` argument is also passed, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(
    v: str,
    validator: core_schema.ValidatorFunctionWrapHandler,
    info: core_schema.ValidationInfo,
) -> str:
    return validator(input_value=v) + 'world'

schema = core_schema.with_info_wrap_validator_function(
    function=fn, schema=core_schema.str_schema()
)
v = SchemaValidator(schema)
assert v.validate_python('hello ') == 'hello world'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `WithInfoWrapValidatorFunction` | The validator function to call | *required* | | `schema` | `CoreSchema` | The schema to validate the output of the validator function | *required* | | `field_name` | `str | None` | The name of the field this validator is applied to, if any (deprecated) | `None` | | `json_schema_input_schema` | `CoreSchema | None` | The core schema to be used to generate the corresponding JSON Schema input type | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def with_info_wrap_validator_function(
    function: WithInfoWrapValidatorFunction,
    schema: CoreSchema,
    *,
    field_name: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> WrapValidatorFunctionSchema:
    """
    Returns a schema which calls a function with a `validator` callable argument which can
    optionally be used to call inner validation with the function logic, this is much like the
    "onion" implementation of middleware in many popular web frameworks, an `info` argument is also passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(
        v: str,
        validator: core_schema.ValidatorFunctionWrapHandler,
        info: core_schema.ValidationInfo,
    ) -> str:
        return validator(input_value=v) + 'world'

    schema = core_schema.with_info_wrap_validator_function(
        function=fn, schema=core_schema.str_schema()
    )
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        schema: The schema to validate the output of the validator function
        field_name: The name of the field this validator is applied to, if any (deprecated)
        json_schema_input_schema: The core schema to be used to generate the corresponding JSON Schema input type
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    if field_name is not None:
        warnings.warn(
            'The `field_name` argument on `with_info_wrap_validator_function` is deprecated, it will be passed to the function through `ValidationState` instead.',
            DeprecationWarning,
            stacklevel=2,
        )

    return _dict_not_none(
        type='function-wrap',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        schema=schema,
        json_schema_input_schema=json_schema_input_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## no_info_plain_validator_function

```python
no_info_plain_validator_function(
    function: NoInfoValidatorFunction,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> PlainValidatorFunctionSchema

```

Returns a schema that uses the provided function for validation, no `info` argument is passed, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: str) -> str:
    assert 'hello' in v
    return v + 'world'

schema = core_schema.no_info_plain_validator_function(function=fn)
v = SchemaValidator(schema)
assert v.validate_python('hello ') == 'hello world'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `NoInfoValidatorFunction` | The validator function to call | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `json_schema_input_schema` | `CoreSchema | None` | The core schema to be used to generate the corresponding JSON Schema input type | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def no_info_plain_validator_function(
    function: NoInfoValidatorFunction,
    *,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> PlainValidatorFunctionSchema:
    """
    Returns a schema that uses the provided function for validation, no `info` argument is passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str) -> str:
        assert 'hello' in v
        return v + 'world'

    schema = core_schema.no_info_plain_validator_function(function=fn)
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        ref: optional unique identifier of the schema, used to reference the schema in other places
        json_schema_input_schema: The core schema to be used to generate the corresponding JSON Schema input type
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='function-plain',
        function={'type': 'no-info', 'function': function},
        ref=ref,
        json_schema_input_schema=json_schema_input_schema,
        metadata=metadata,
        serialization=serialization,
    )

````

## with_info_plain_validator_function

```python
with_info_plain_validator_function(
    function: WithInfoValidatorFunction,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> PlainValidatorFunctionSchema

```

Returns a schema that uses the provided function for validation, an `info` argument is passed, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: str, info: core_schema.ValidationInfo) -> str:
    assert 'hello' in v
    return v + 'world'

schema = core_schema.with_info_plain_validator_function(function=fn)
v = SchemaValidator(schema)
assert v.validate_python('hello ') == 'hello world'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `function` | `WithInfoValidatorFunction` | The validator function to call | *required* | | `field_name` | `str | None` | The name of the field this validator is applied to, if any (deprecated) | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `json_schema_input_schema` | `CoreSchema | None` | The core schema to be used to generate the corresponding JSON Schema input type | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def with_info_plain_validator_function(
    function: WithInfoValidatorFunction,
    *,
    field_name: str | None = None,
    ref: str | None = None,
    json_schema_input_schema: CoreSchema | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> PlainValidatorFunctionSchema:
    """
    Returns a schema that uses the provided function for validation, an `info` argument is passed, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert 'hello' in v
        return v + 'world'

    schema = core_schema.with_info_plain_validator_function(function=fn)
    v = SchemaValidator(schema)
    assert v.validate_python('hello ') == 'hello world'
    ```

    Args:
        function: The validator function to call
        field_name: The name of the field this validator is applied to, if any (deprecated)
        ref: optional unique identifier of the schema, used to reference the schema in other places
        json_schema_input_schema: The core schema to be used to generate the corresponding JSON Schema input type
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    if field_name is not None:
        warnings.warn(
            'The `field_name` argument on `with_info_plain_validator_function` is deprecated, it will be passed to the function through `ValidationState` instead.',
            DeprecationWarning,
            stacklevel=2,
        )

    return _dict_not_none(
        type='function-plain',
        function=_dict_not_none(type='with-info', function=function, field_name=field_name),
        ref=ref,
        json_schema_input_schema=json_schema_input_schema,
        metadata=metadata,
        serialization=serialization,
    )

````

## with_default_schema

```python
with_default_schema(
    schema: CoreSchema,
    *,
    default: Any = PydanticUndefined,
    default_factory: Union[
        Callable[[], Any],
        Callable[[dict[str, Any]], Any],
        None,
    ] = None,
    default_factory_takes_data: bool | None = None,
    on_error: (
        Literal["raise", "omit", "default"] | None
    ) = None,
    validate_default: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> WithDefaultSchema

```

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

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The schema to add a default value to | *required* | | `default` | `Any` | The default value to use | `PydanticUndefined` | | `default_factory` | `Union[Callable[[], Any], Callable[[dict[str, Any]], Any], None]` | A callable that returns the default value to use | `None` | | `default_factory_takes_data` | `bool | None` | Whether the default factory takes a validated data argument | `None` | | `on_error` | `Literal['raise', 'omit', 'default'] | None` | What to do if the schema validation fails. One of 'raise', 'omit', 'default' | `None` | | `validate_default` | `bool | None` | Whether the default value should be validated | `None` | | `strict` | `bool | None` | Whether the underlying schema should be validated with strict mode | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def with_default_schema(
    schema: CoreSchema,
    *,
    default: Any = PydanticUndefined,
    default_factory: Union[Callable[[], Any], Callable[[dict[str, Any]], Any], None] = None,
    default_factory_takes_data: bool | None = None,
    on_error: Literal['raise', 'omit', 'default'] | None = None,
    validate_default: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        default_factory: A callable that returns the default value to use
        default_factory_takes_data: Whether the default factory takes a validated data argument
        on_error: What to do if the schema validation fails. One of 'raise', 'omit', 'default'
        validate_default: Whether the default value should be validated
        strict: Whether the underlying schema should be validated with strict mode
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    s = _dict_not_none(
        type='default',
        schema=schema,
        default_factory=default_factory,
        default_factory_takes_data=default_factory_takes_data,
        on_error=on_error,
        validate_default=validate_default,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )
    if default is not PydanticUndefined:
        s['default'] = default
    return s

````

## nullable_schema

```python
nullable_schema(
    schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> NullableSchema

```

Returns a schema that matches a nullable value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.nullable_schema(core_schema.str_schema())
v = SchemaValidator(schema)
assert v.validate_python(None) is None

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The schema to wrap | *required* | | `strict` | `bool | None` | Whether the underlying schema should be validated with strict mode | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def nullable_schema(
    schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='nullable', schema=schema, strict=strict, ref=ref, metadata=metadata, serialization=serialization
    )

````

## union_schema

```python
union_schema(
    choices: list[CoreSchema | tuple[CoreSchema, str]],
    *,
    auto_collapse: bool | None = None,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: (
        dict[str, str | int] | None
    ) = None,
    mode: Literal["smart", "left_to_right"] | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> UnionSchema

```

Returns a schema that matches a union value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.union_schema([core_schema.str_schema(), core_schema.int_schema()])
v = SchemaValidator(schema)
assert v.validate_python('hello') == 'hello'
assert v.validate_python(1) == 1

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `choices` | `list[CoreSchema | tuple[CoreSchema, str]]` | The schemas to match. If a tuple, the second item is used as the label for the case. | *required* | | `auto_collapse` | `bool | None` | whether to automatically collapse unions with one element to the inner validator, default true | `None` | | `custom_error_type` | `str | None` | The custom error type to use if the validation fails | `None` | | `custom_error_message` | `str | None` | The custom error message to use if the validation fails | `None` | | `custom_error_context` | `dict[str, str | int] | None` | The custom error context to use if the validation fails | `None` | | `mode` | `Literal['smart', 'left_to_right'] | None` | How to select which choice to return * smart (default) will try to return the choice which is the closest match to the input value * left_to_right will return the first choice in choices which succeeds validation | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def union_schema(
    choices: list[CoreSchema | tuple[CoreSchema, str]],
    *,
    auto_collapse: bool | None = None,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, str | int] | None = None,
    mode: Literal['smart', 'left_to_right'] | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> UnionSchema:
    """
    Returns a schema that matches a union value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.union_schema([core_schema.str_schema(), core_schema.int_schema()])
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello'
    assert v.validate_python(1) == 1
    ```

    Args:
        choices: The schemas to match. If a tuple, the second item is used as the label for the case.
        auto_collapse: whether to automatically collapse unions with one element to the inner validator, default true
        custom_error_type: The custom error type to use if the validation fails
        custom_error_message: The custom error message to use if the validation fails
        custom_error_context: The custom error context to use if the validation fails
        mode: How to select which choice to return
            * `smart` (default) will try to return the choice which is the closest match to the input value
            * `left_to_right` will return the first choice in `choices` which succeeds validation
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='union',
        choices=choices,
        auto_collapse=auto_collapse,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        mode=mode,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## tagged_union_schema

```python
tagged_union_schema(
    choices: dict[Any, CoreSchema],
    discriminator: (
        str
        | list[str | int]
        | list[list[str | int]]
        | Callable[[Any], Any]
    ),
    *,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: (
        dict[str, int | str | float] | None
    ) = None,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> TaggedUnionSchema

```

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
        'spam': core_schema.typed_dict_field(
            core_schema.list_schema(items_schema=core_schema.int_schema())
        ),
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
assert v.validate_python({'foo': 'banana', 'spam': [1, 2, 3]}) == {
    'foo': 'banana',
    'spam': [1, 2, 3],
}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `choices` | `dict[Any, CoreSchema]` | The schemas to match When retrieving a schema from choices using the discriminator value, if the value is a str, it should be fed back into the choices map until a schema is obtained (This approach is to prevent multiple ownership of a single schema in Rust) | *required* | | `discriminator` | `str | list[str | int] | list[list[str | int]] | Callable[[Any], Any]` | The discriminator to use to determine the schema to use * If discriminator is a str, it is the name of the attribute to use as the discriminator * If discriminator is a list of int/str, it should be used as a "path" to access the discriminator * If discriminator is a list of lists, each inner list is a path, and the first path that exists is used * If discriminator is a callable, it should return the discriminator when called on the value to validate; the callable can return None to indicate that there is no matching discriminator present on the input | *required* | | `custom_error_type` | `str | None` | The custom error type to use if the validation fails | `None` | | `custom_error_message` | `str | None` | The custom error message to use if the validation fails | `None` | | `custom_error_context` | `dict[str, int | str | float] | None` | The custom error context to use if the validation fails | `None` | | `strict` | `bool | None` | Whether the underlying schemas should be validated with strict mode | `None` | | `from_attributes` | `bool | None` | Whether to use the attributes of the object to retrieve the discriminator value | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def tagged_union_schema(
    choices: dict[Any, CoreSchema],
    discriminator: str | list[str | int] | list[list[str | int]] | Callable[[Any], Any],
    *,
    custom_error_type: str | None = None,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, int | str | float] | None = None,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
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
            'spam': core_schema.typed_dict_field(
                core_schema.list_schema(items_schema=core_schema.int_schema())
            ),
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
    assert v.validate_python({'foo': 'banana', 'spam': [1, 2, 3]}) == {
        'foo': 'banana',
        'spam': [1, 2, 3],
    }
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
            * If `discriminator` is a callable, it should return the discriminator when called on the value to validate;
              the callable can return `None` to indicate that there is no matching discriminator present on the input
        custom_error_type: The custom error type to use if the validation fails
        custom_error_message: The custom error message to use if the validation fails
        custom_error_context: The custom error context to use if the validation fails
        strict: Whether the underlying schemas should be validated with strict mode
        from_attributes: Whether to use the attributes of the object to retrieve the discriminator value
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
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

````

## chain_schema

```python
chain_schema(
    steps: list[CoreSchema],
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> ChainSchema

```

Returns a schema that chains the provided validation schemas, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: str, info: core_schema.ValidationInfo) -> str:
    assert 'hello' in v
    return v + ' world'

fn_schema = core_schema.with_info_plain_validator_function(function=fn)
schema = core_schema.chain_schema(
    [fn_schema, fn_schema, fn_schema, core_schema.str_schema()]
)
v = SchemaValidator(schema)
assert v.validate_python('hello') == 'hello world world world'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `steps` | `list[CoreSchema]` | The schemas to chain | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def chain_schema(
    steps: list[CoreSchema],
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ChainSchema:
    """
    Returns a schema that chains the provided validation schemas, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert 'hello' in v
        return v + ' world'

    fn_schema = core_schema.with_info_plain_validator_function(function=fn)
    schema = core_schema.chain_schema(
        [fn_schema, fn_schema, fn_schema, core_schema.str_schema()]
    )
    v = SchemaValidator(schema)
    assert v.validate_python('hello') == 'hello world world world'
    ```

    Args:
        steps: The schemas to chain
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='chain', steps=steps, ref=ref, metadata=metadata, serialization=serialization)

````

## lax_or_strict_schema

```python
lax_or_strict_schema(
    lax_schema: CoreSchema,
    strict_schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> LaxOrStrictSchema

```

Returns a schema that uses the lax or strict schema, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

def fn(v: str, info: core_schema.ValidationInfo) -> str:
    assert 'hello' in v
    return v + ' world'

lax_schema = core_schema.int_schema(strict=False)
strict_schema = core_schema.int_schema(strict=True)

schema = core_schema.lax_or_strict_schema(
    lax_schema=lax_schema, strict_schema=strict_schema, strict=True
)
v = SchemaValidator(schema)
assert v.validate_python(123) == 123

schema = core_schema.lax_or_strict_schema(
    lax_schema=lax_schema, strict_schema=strict_schema, strict=False
)
v = SchemaValidator(schema)
assert v.validate_python('123') == 123

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `lax_schema` | `CoreSchema` | The lax schema to use | *required* | | `strict_schema` | `CoreSchema` | The strict schema to use | *required* | | `strict` | `bool | None` | Whether the strict schema should be used | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def lax_or_strict_schema(
    lax_schema: CoreSchema,
    strict_schema: CoreSchema,
    *,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> LaxOrStrictSchema:
    """
    Returns a schema that uses the lax or strict schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    def fn(v: str, info: core_schema.ValidationInfo) -> str:
        assert 'hello' in v
        return v + ' world'

    lax_schema = core_schema.int_schema(strict=False)
    strict_schema = core_schema.int_schema(strict=True)

    schema = core_schema.lax_or_strict_schema(
        lax_schema=lax_schema, strict_schema=strict_schema, strict=True
    )
    v = SchemaValidator(schema)
    assert v.validate_python(123) == 123

    schema = core_schema.lax_or_strict_schema(
        lax_schema=lax_schema, strict_schema=strict_schema, strict=False
    )
    v = SchemaValidator(schema)
    assert v.validate_python('123') == 123
    ```

    Args:
        lax_schema: The lax schema to use
        strict_schema: The strict schema to use
        strict: Whether the strict schema should be used
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='lax-or-strict',
        lax_schema=lax_schema,
        strict_schema=strict_schema,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## json_or_python_schema

```python
json_or_python_schema(
    json_schema: CoreSchema,
    python_schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> JsonOrPythonSchema

```

Returns a schema that uses the Json or Python schema depending on the input:

```py
from pydantic_core import SchemaValidator, ValidationError, core_schema

v = SchemaValidator(
    core_schema.json_or_python_schema(
        json_schema=core_schema.int_schema(),
        python_schema=core_schema.int_schema(strict=True),
    )
)

assert v.validate_json('"123"') == 123

try:
    v.validate_python('123')
except ValidationError:
    pass
else:
    raise AssertionError('Validation should have failed')

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `json_schema` | `CoreSchema` | The schema to use for Json inputs | *required* | | `python_schema` | `CoreSchema` | The schema to use for Python inputs | *required* | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def json_or_python_schema(
    json_schema: CoreSchema,
    python_schema: CoreSchema,
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> JsonOrPythonSchema:
    """
    Returns a schema that uses the Json or Python schema depending on the input:

    ```py
    from pydantic_core import SchemaValidator, ValidationError, core_schema

    v = SchemaValidator(
        core_schema.json_or_python_schema(
            json_schema=core_schema.int_schema(),
            python_schema=core_schema.int_schema(strict=True),
        )
    )

    assert v.validate_json('"123"') == 123

    try:
        v.validate_python('123')
    except ValidationError:
        pass
    else:
        raise AssertionError('Validation should have failed')
    ```

    Args:
        json_schema: The schema to use for Json inputs
        python_schema: The schema to use for Python inputs
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='json-or-python',
        json_schema=json_schema,
        python_schema=python_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## typed_dict_field

```python
typed_dict_field(
    schema: CoreSchema,
    *,
    required: bool | None = None,
    validation_alias: (
        str | list[str | int] | list[list[str | int]] | None
    ) = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    metadata: dict[str, Any] | None = None,
    serialization_exclude_if: (
        Callable[[Any], bool] | None
    ) = None
) -> TypedDictField

```

Returns a schema that matches a typed dict field, e.g.:

```py
from pydantic_core import core_schema

field = core_schema.typed_dict_field(schema=core_schema.int_schema(), required=True)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The schema to use for the field | *required* | | `required` | `bool | None` | Whether the field is required, otherwise uses the value from total on the typed dict | `None` | | `validation_alias` | `str | list[str | int] | list[list[str | int]] | None` | The alias(es) to use to find the field in the validation data | `None` | | `serialization_alias` | `str | None` | The alias to use as a key when serializing | `None` | | `serialization_exclude` | `bool | None` | Whether to exclude the field when serializing | `None` | | `serialization_exclude_if` | `Callable[[Any], bool] | None` | A callable that determines whether to exclude the field when serializing based on its value. | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def typed_dict_field(
    schema: CoreSchema,
    *,
    required: bool | None = None,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    metadata: dict[str, Any] | None = None,
    serialization_exclude_if: Callable[[Any], bool] | None = None,
) -> TypedDictField:
    """
    Returns a schema that matches a typed dict field, e.g.:

    ```py
    from pydantic_core import core_schema

    field = core_schema.typed_dict_field(schema=core_schema.int_schema(), required=True)
    ```

    Args:
        schema: The schema to use for the field
        required: Whether the field is required, otherwise uses the value from `total` on the typed dict
        validation_alias: The alias(es) to use to find the field in the validation data
        serialization_alias: The alias to use as a key when serializing
        serialization_exclude: Whether to exclude the field when serializing
        serialization_exclude_if: A callable that determines whether to exclude the field when serializing based on its value.
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """
    return _dict_not_none(
        type='typed-dict-field',
        schema=schema,
        required=required,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        serialization_exclude_if=serialization_exclude_if,
        metadata=metadata,
    )

````

## typed_dict_schema

```python
typed_dict_schema(
    fields: dict[str, TypedDictField],
    *,
    cls: type[Any] | None = None,
    cls_name: str | None = None,
    computed_fields: list[ComputedField] | None = None,
    strict: bool | None = None,
    extras_schema: CoreSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
    total: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    config: CoreConfig | None = None
) -> TypedDictSchema

```

Returns a schema that matches a typed dict, e.g.:

```py
from typing_extensions import TypedDict

from pydantic_core import SchemaValidator, core_schema

class MyTypedDict(TypedDict):
    a: str

wrapper_schema = core_schema.typed_dict_schema(
    {'a': core_schema.typed_dict_field(core_schema.str_schema())}, cls=MyTypedDict
)
v = SchemaValidator(wrapper_schema)
assert v.validate_python({'a': 'hello'}) == {'a': 'hello'}

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `fields` | `dict[str, TypedDictField]` | The fields to use for the typed dict | *required* | | `cls` | `type[Any] | None` | The class to use for the typed dict | `None` | | `cls_name` | `str | None` | The name to use in error locations. Falls back to cls.__name__, or the validator name if no class is provided. | `None` | | `computed_fields` | `list[ComputedField] | None` | Computed fields to use when serializing the model, only applies when directly inside a model | `None` | | `strict` | `bool | None` | Whether the typed dict is strict | `None` | | `extras_schema` | `CoreSchema | None` | The extra validator to use for the typed dict | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `extra_behavior` | `ExtraBehavior | None` | The extra behavior to use for the typed dict | `None` | | `total` | `bool | None` | Whether the typed dict is total, otherwise uses typed_dict_total from config | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def typed_dict_schema(
    fields: dict[str, TypedDictField],
    *,
    cls: type[Any] | None = None,
    cls_name: str | None = None,
    computed_fields: list[ComputedField] | None = None,
    strict: bool | None = None,
    extras_schema: CoreSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
    total: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    config: CoreConfig | None = None,
) -> TypedDictSchema:
    """
    Returns a schema that matches a typed dict, e.g.:

    ```py
    from typing_extensions import TypedDict

    from pydantic_core import SchemaValidator, core_schema

    class MyTypedDict(TypedDict):
        a: str

    wrapper_schema = core_schema.typed_dict_schema(
        {'a': core_schema.typed_dict_field(core_schema.str_schema())}, cls=MyTypedDict
    )
    v = SchemaValidator(wrapper_schema)
    assert v.validate_python({'a': 'hello'}) == {'a': 'hello'}
    ```

    Args:
        fields: The fields to use for the typed dict
        cls: The class to use for the typed dict
        cls_name: The name to use in error locations. Falls back to `cls.__name__`, or the validator name if no class
            is provided.
        computed_fields: Computed fields to use when serializing the model, only applies when directly inside a model
        strict: Whether the typed dict is strict
        extras_schema: The extra validator to use for the typed dict
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        extra_behavior: The extra behavior to use for the typed dict
        total: Whether the typed dict is total, otherwise uses `typed_dict_total` from config
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='typed-dict',
        fields=fields,
        cls=cls,
        cls_name=cls_name,
        computed_fields=computed_fields,
        strict=strict,
        extras_schema=extras_schema,
        extra_behavior=extra_behavior,
        total=total,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
        config=config,
    )

````

## model_field

```python
model_field(
    schema: CoreSchema,
    *,
    validation_alias: (
        str | list[str | int] | list[list[str | int]] | None
    ) = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    serialization_exclude_if: (
        Callable[[Any], bool] | None
    ) = None,
    frozen: bool | None = None,
    metadata: dict[str, Any] | None = None
) -> ModelField

```

Returns a schema for a model field, e.g.:

```py
from pydantic_core import core_schema

field = core_schema.model_field(schema=core_schema.int_schema())

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The schema to use for the field | *required* | | `validation_alias` | `str | list[str | int] | list[list[str | int]] | None` | The alias(es) to use to find the field in the validation data | `None` | | `serialization_alias` | `str | None` | The alias to use as a key when serializing | `None` | | `serialization_exclude` | `bool | None` | Whether to exclude the field when serializing | `None` | | `serialization_exclude_if` | `Callable[[Any], bool] | None` | A Callable that determines whether to exclude a field during serialization based on its value. | `None` | | `frozen` | `bool | None` | Whether the field is frozen | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def model_field(
    schema: CoreSchema,
    *,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    serialization_exclude_if: Callable[[Any], bool] | None = None,
    frozen: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> ModelField:
    """
    Returns a schema for a model field, e.g.:

    ```py
    from pydantic_core import core_schema

    field = core_schema.model_field(schema=core_schema.int_schema())
    ```

    Args:
        schema: The schema to use for the field
        validation_alias: The alias(es) to use to find the field in the validation data
        serialization_alias: The alias to use as a key when serializing
        serialization_exclude: Whether to exclude the field when serializing
        serialization_exclude_if: A Callable that determines whether to exclude a field during serialization based on its value.
        frozen: Whether the field is frozen
        metadata: Any other information you want to include with the schema, not used by pydantic-core
    """
    return _dict_not_none(
        type='model-field',
        schema=schema,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        serialization_exclude_if=serialization_exclude_if,
        frozen=frozen,
        metadata=metadata,
    )

````

## model_fields_schema

```python
model_fields_schema(
    fields: dict[str, ModelField],
    *,
    model_name: str | None = None,
    computed_fields: list[ComputedField] | None = None,
    strict: bool | None = None,
    extras_schema: CoreSchema | None = None,
    extras_keys_schema: CoreSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> ModelFieldsSchema

```

Returns a schema that matches the fields of a Pydantic model, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

wrapper_schema = core_schema.model_fields_schema(
    {'a': core_schema.model_field(core_schema.str_schema())}
)
v = SchemaValidator(wrapper_schema)
print(v.validate_python({'a': 'hello'}))
#> ({'a': 'hello'}, None, {'a'})

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `fields` | `dict[str, ModelField]` | The fields of the model | *required* | | `model_name` | `str | None` | The name of the model, used for error messages, defaults to "Model" | `None` | | `computed_fields` | `list[ComputedField] | None` | Computed fields to use when serializing the model, only applies when directly inside a model | `None` | | `strict` | `bool | None` | Whether the model is strict | `None` | | `extras_schema` | `CoreSchema | None` | The schema to use when validating extra input data | `None` | | `extras_keys_schema` | `CoreSchema | None` | The schema to use when validating the keys of extra input data | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `extra_behavior` | `ExtraBehavior | None` | The extra behavior to use for the model fields | `None` | | `from_attributes` | `bool | None` | Whether the model fields should be populated from attributes | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def model_fields_schema(
    fields: dict[str, ModelField],
    *,
    model_name: str | None = None,
    computed_fields: list[ComputedField] | None = None,
    strict: bool | None = None,
    extras_schema: CoreSchema | None = None,
    extras_keys_schema: CoreSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
    from_attributes: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ModelFieldsSchema:
    """
    Returns a schema that matches the fields of a Pydantic model, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    wrapper_schema = core_schema.model_fields_schema(
        {'a': core_schema.model_field(core_schema.str_schema())}
    )
    v = SchemaValidator(wrapper_schema)
    print(v.validate_python({'a': 'hello'}))
    #> ({'a': 'hello'}, None, {'a'})
    ```

    Args:
        fields: The fields of the model
        model_name: The name of the model, used for error messages, defaults to "Model"
        computed_fields: Computed fields to use when serializing the model, only applies when directly inside a model
        strict: Whether the model is strict
        extras_schema: The schema to use when validating extra input data
        extras_keys_schema: The schema to use when validating the keys of extra input data
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        extra_behavior: The extra behavior to use for the model fields
        from_attributes: Whether the model fields should be populated from attributes
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='model-fields',
        fields=fields,
        model_name=model_name,
        computed_fields=computed_fields,
        strict=strict,
        extras_schema=extras_schema,
        extras_keys_schema=extras_keys_schema,
        extra_behavior=extra_behavior,
        from_attributes=from_attributes,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## model_schema

```python
model_schema(
    cls: type[Any],
    schema: CoreSchema,
    *,
    generic_origin: type[Any] | None = None,
    custom_init: bool | None = None,
    root_model: bool | None = None,
    post_init: str | None = None,
    revalidate_instances: (
        Literal["always", "never", "subclass-instances"]
        | None
    ) = None,
    strict: bool | None = None,
    frozen: bool | None = None,
    extra_behavior: ExtraBehavior | None = None,
    config: CoreConfig | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> ModelSchema

```

A model schema generally contains a typed-dict schema. It will run the typed dict validator, then create a new class and set the dict and fields set returned from the typed dict validator to `__dict__` and `__pydantic_fields_set__` respectively.

Example:

```py
from pydantic_core import CoreConfig, SchemaValidator, core_schema

class MyModel:
    __slots__ = (
        '__dict__',
        '__pydantic_fields_set__',
        '__pydantic_extra__',
        '__pydantic_private__',
    )

schema = core_schema.model_schema(
    cls=MyModel,
    config=CoreConfig(str_max_length=5),
    schema=core_schema.model_fields_schema(
        fields={'a': core_schema.model_field(core_schema.str_schema())},
    ),
)
v = SchemaValidator(schema)
assert v.isinstance_python({'a': 'hello'}) is True
assert v.isinstance_python({'a': 'too long'}) is False

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cls` | `type[Any]` | The class to use for the model | *required* | | `schema` | `CoreSchema` | The schema to use for the model | *required* | | `generic_origin` | `type[Any] | None` | The origin type used for this model, if it's a parametrized generic. Ex, if this model schema represents SomeModel[int], generic_origin is SomeModel | `None` | | `custom_init` | `bool | None` | Whether the model has a custom init method | `None` | | `root_model` | `bool | None` | Whether the model is a RootModel | `None` | | `post_init` | `str | None` | The call after init to use for the model | `None` | | `revalidate_instances` | `Literal['always', 'never', 'subclass-instances'] | None` | whether instances of models and dataclasses (including subclass instances) should re-validate defaults to config.revalidate_instances, else 'never' | `None` | | `strict` | `bool | None` | Whether the model is strict | `None` | | `frozen` | `bool | None` | Whether the model is frozen | `None` | | `extra_behavior` | `ExtraBehavior | None` | The extra behavior to use for the model, used in serialization | `None` | | `config` | `CoreConfig | None` | The config to use for the model | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def model_schema(
    cls: type[Any],
    schema: CoreSchema,
    *,
    generic_origin: type[Any] | None = None,
    custom_init: bool | None = None,
    root_model: bool | None = None,
    post_init: str | None = None,
    revalidate_instances: Literal['always', 'never', 'subclass-instances'] | None = None,
    strict: bool | None = None,
    frozen: bool | None = None,
    extra_behavior: ExtraBehavior | None = None,
    config: CoreConfig | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ModelSchema:
    """
    A model schema generally contains a typed-dict schema.
    It will run the typed dict validator, then create a new class
    and set the dict and fields set returned from the typed dict validator
    to `__dict__` and `__pydantic_fields_set__` respectively.

    Example:

    ```py
    from pydantic_core import CoreConfig, SchemaValidator, core_schema

    class MyModel:
        __slots__ = (
            '__dict__',
            '__pydantic_fields_set__',
            '__pydantic_extra__',
            '__pydantic_private__',
        )

    schema = core_schema.model_schema(
        cls=MyModel,
        config=CoreConfig(str_max_length=5),
        schema=core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(core_schema.str_schema())},
        ),
    )
    v = SchemaValidator(schema)
    assert v.isinstance_python({'a': 'hello'}) is True
    assert v.isinstance_python({'a': 'too long'}) is False
    ```

    Args:
        cls: The class to use for the model
        schema: The schema to use for the model
        generic_origin: The origin type used for this model, if it's a parametrized generic. Ex,
            if this model schema represents `SomeModel[int]`, generic_origin is `SomeModel`
        custom_init: Whether the model has a custom init method
        root_model: Whether the model is a `RootModel`
        post_init: The call after init to use for the model
        revalidate_instances: whether instances of models and dataclasses (including subclass instances)
            should re-validate defaults to config.revalidate_instances, else 'never'
        strict: Whether the model is strict
        frozen: Whether the model is frozen
        extra_behavior: The extra behavior to use for the model, used in serialization
        config: The config to use for the model
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='model',
        cls=cls,
        generic_origin=generic_origin,
        schema=schema,
        custom_init=custom_init,
        root_model=root_model,
        post_init=post_init,
        revalidate_instances=revalidate_instances,
        strict=strict,
        frozen=frozen,
        extra_behavior=extra_behavior,
        config=config,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## dataclass_field

```python
dataclass_field(
    name: str,
    schema: CoreSchema,
    *,
    kw_only: bool | None = None,
    init: bool | None = None,
    init_only: bool | None = None,
    validation_alias: (
        str | list[str | int] | list[list[str | int]] | None
    ) = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    metadata: dict[str, Any] | None = None,
    serialization_exclude_if: (
        Callable[[Any], bool] | None
    ) = None,
    frozen: bool | None = None
) -> DataclassField

```

Returns a schema for a dataclass field, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

field = core_schema.dataclass_field(
    name='a', schema=core_schema.str_schema(), kw_only=False
)
schema = core_schema.dataclass_args_schema('Foobar', [field])
v = SchemaValidator(schema)
assert v.validate_python({'a': 'hello'}) == ({'a': 'hello'}, None)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name to use for the argument parameter | *required* | | `schema` | `CoreSchema` | The schema to use for the argument parameter | *required* | | `kw_only` | `bool | None` | Whether the field can be set with a positional argument as well as a keyword argument | `None` | | `init` | `bool | None` | Whether the field should be validated during initialization | `None` | | `init_only` | `bool | None` | Whether the field should be omitted from __dict__ and passed to __post_init__ | `None` | | `validation_alias` | `str | list[str | int] | list[list[str | int]] | None` | The alias(es) to use to find the field in the validation data | `None` | | `serialization_alias` | `str | None` | The alias to use as a key when serializing | `None` | | `serialization_exclude` | `bool | None` | Whether to exclude the field when serializing | `None` | | `serialization_exclude_if` | `Callable[[Any], bool] | None` | A callable that determines whether to exclude the field when serializing based on its value. | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `frozen` | `bool | None` | Whether the field is frozen | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def dataclass_field(
    name: str,
    schema: CoreSchema,
    *,
    kw_only: bool | None = None,
    init: bool | None = None,
    init_only: bool | None = None,
    validation_alias: str | list[str | int] | list[list[str | int]] | None = None,
    serialization_alias: str | None = None,
    serialization_exclude: bool | None = None,
    metadata: dict[str, Any] | None = None,
    serialization_exclude_if: Callable[[Any], bool] | None = None,
    frozen: bool | None = None,
) -> DataclassField:
    """
    Returns a schema for a dataclass field, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    field = core_schema.dataclass_field(
        name='a', schema=core_schema.str_schema(), kw_only=False
    )
    schema = core_schema.dataclass_args_schema('Foobar', [field])
    v = SchemaValidator(schema)
    assert v.validate_python({'a': 'hello'}) == ({'a': 'hello'}, None)
    ```

    Args:
        name: The name to use for the argument parameter
        schema: The schema to use for the argument parameter
        kw_only: Whether the field can be set with a positional argument as well as a keyword argument
        init: Whether the field should be validated during initialization
        init_only: Whether the field should be omitted  from `__dict__` and passed to `__post_init__`
        validation_alias: The alias(es) to use to find the field in the validation data
        serialization_alias: The alias to use as a key when serializing
        serialization_exclude: Whether to exclude the field when serializing
        serialization_exclude_if: A callable that determines whether to exclude the field when serializing based on its value.
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        frozen: Whether the field is frozen
    """
    return _dict_not_none(
        type='dataclass-field',
        name=name,
        schema=schema,
        kw_only=kw_only,
        init=init,
        init_only=init_only,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        serialization_exclude=serialization_exclude,
        serialization_exclude_if=serialization_exclude_if,
        metadata=metadata,
        frozen=frozen,
    )

````

## dataclass_args_schema

```python
dataclass_args_schema(
    dataclass_name: str,
    fields: list[DataclassField],
    *,
    computed_fields: list[ComputedField] | None = None,
    collect_init_only: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    extra_behavior: ExtraBehavior | None = None
) -> DataclassArgsSchema

```

Returns a schema for validating dataclass arguments, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

field_a = core_schema.dataclass_field(
    name='a', schema=core_schema.str_schema(), kw_only=False
)
field_b = core_schema.dataclass_field(
    name='b', schema=core_schema.bool_schema(), kw_only=False
)
schema = core_schema.dataclass_args_schema('Foobar', [field_a, field_b])
v = SchemaValidator(schema)
assert v.validate_python({'a': 'hello', 'b': True}) == ({'a': 'hello', 'b': True}, None)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `dataclass_name` | `str` | The name of the dataclass being validated | *required* | | `fields` | `list[DataclassField]` | The fields to use for the dataclass | *required* | | `computed_fields` | `list[ComputedField] | None` | Computed fields to use when serializing the dataclass | `None` | | `collect_init_only` | `bool | None` | Whether to collect init only fields into a dict to pass to __post_init__ | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` | | `extra_behavior` | `ExtraBehavior | None` | How to handle extra fields | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def dataclass_args_schema(
    dataclass_name: str,
    fields: list[DataclassField],
    *,
    computed_fields: list[ComputedField] | None = None,
    collect_init_only: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    extra_behavior: ExtraBehavior | None = None,
) -> DataclassArgsSchema:
    """
    Returns a schema for validating dataclass arguments, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    field_a = core_schema.dataclass_field(
        name='a', schema=core_schema.str_schema(), kw_only=False
    )
    field_b = core_schema.dataclass_field(
        name='b', schema=core_schema.bool_schema(), kw_only=False
    )
    schema = core_schema.dataclass_args_schema('Foobar', [field_a, field_b])
    v = SchemaValidator(schema)
    assert v.validate_python({'a': 'hello', 'b': True}) == ({'a': 'hello', 'b': True}, None)
    ```

    Args:
        dataclass_name: The name of the dataclass being validated
        fields: The fields to use for the dataclass
        computed_fields: Computed fields to use when serializing the dataclass
        collect_init_only: Whether to collect init only fields into a dict to pass to `__post_init__`
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
        extra_behavior: How to handle extra fields
    """
    return _dict_not_none(
        type='dataclass-args',
        dataclass_name=dataclass_name,
        fields=fields,
        computed_fields=computed_fields,
        collect_init_only=collect_init_only,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
        extra_behavior=extra_behavior,
    )

````

## dataclass_schema

```python
dataclass_schema(
    cls: type[Any],
    schema: CoreSchema,
    fields: list[str],
    *,
    generic_origin: type[Any] | None = None,
    cls_name: str | None = None,
    post_init: bool | None = None,
    revalidate_instances: (
        Literal["always", "never", "subclass-instances"]
        | None
    ) = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    frozen: bool | None = None,
    slots: bool | None = None,
    config: CoreConfig | None = None
) -> DataclassSchema

```

Returns a schema for a dataclass. As with `ModelSchema`, this schema can only be used as a field within another schema, not as the root type.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cls` | `type[Any]` | The dataclass type, used to perform subclass checks | *required* | | `schema` | `CoreSchema` | The schema to use for the dataclass fields | *required* | | `fields` | `list[str]` | Fields of the dataclass, this is used in serialization and in validation during re-validation and while validating assignment | *required* | | `generic_origin` | `type[Any] | None` | The origin type used for this dataclass, if it's a parametrized generic. Ex, if this model schema represents SomeDataclass[int], generic_origin is SomeDataclass | `None` | | `cls_name` | `str | None` | The name to use in error locs, etc; this is useful for generics (default: cls.__name__) | `None` | | `post_init` | `bool | None` | Whether to call __post_init__ after validation | `None` | | `revalidate_instances` | `Literal['always', 'never', 'subclass-instances'] | None` | whether instances of models and dataclasses (including subclass instances) should re-validate defaults to config.revalidate_instances, else 'never' | `None` | | `strict` | `bool | None` | Whether to require an exact instance of cls | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` | | `frozen` | `bool | None` | Whether the dataclass is frozen | `None` | | `slots` | `bool | None` | Whether slots=True on the dataclass, means each field is assigned independently, rather than simply setting __dict__, default false | `None` |

Source code in `pydantic_core/core_schema.py`

```python
def dataclass_schema(
    cls: type[Any],
    schema: CoreSchema,
    fields: list[str],
    *,
    generic_origin: type[Any] | None = None,
    cls_name: str | None = None,
    post_init: bool | None = None,
    revalidate_instances: Literal['always', 'never', 'subclass-instances'] | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
    frozen: bool | None = None,
    slots: bool | None = None,
    config: CoreConfig | None = None,
) -> DataclassSchema:
    """
    Returns a schema for a dataclass. As with `ModelSchema`, this schema can only be used as a field within
    another schema, not as the root type.

    Args:
        cls: The dataclass type, used to perform subclass checks
        schema: The schema to use for the dataclass fields
        fields: Fields of the dataclass, this is used in serialization and in validation during re-validation
            and while validating assignment
        generic_origin: The origin type used for this dataclass, if it's a parametrized generic. Ex,
            if this model schema represents `SomeDataclass[int]`, generic_origin is `SomeDataclass`
        cls_name: The name to use in error locs, etc; this is useful for generics (default: `cls.__name__`)
        post_init: Whether to call `__post_init__` after validation
        revalidate_instances: whether instances of models and dataclasses (including subclass instances)
            should re-validate defaults to config.revalidate_instances, else 'never'
        strict: Whether to require an exact instance of `cls`
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
        frozen: Whether the dataclass is frozen
        slots: Whether `slots=True` on the dataclass, means each field is assigned independently, rather than
            simply setting `__dict__`, default false
    """
    return _dict_not_none(
        type='dataclass',
        cls=cls,
        generic_origin=generic_origin,
        fields=fields,
        cls_name=cls_name,
        schema=schema,
        post_init=post_init,
        revalidate_instances=revalidate_instances,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
        frozen=frozen,
        slots=slots,
        config=config,
    )

```

## arguments_parameter

```python
arguments_parameter(
    name: str,
    schema: CoreSchema,
    *,
    mode: (
        Literal[
            "positional_only",
            "positional_or_keyword",
            "keyword_only",
        ]
        | None
    ) = None,
    alias: (
        str | list[str | int] | list[list[str | int]] | None
    ) = None
) -> ArgumentsParameter

```

Returns a schema that matches an argument parameter, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

param = core_schema.arguments_parameter(
    name='a', schema=core_schema.str_schema(), mode='positional_only'
)
schema = core_schema.arguments_schema([param])
v = SchemaValidator(schema)
assert v.validate_python(('hello',)) == (('hello',), {})

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name to use for the argument parameter | *required* | | `schema` | `CoreSchema` | The schema to use for the argument parameter | *required* | | `mode` | `Literal['positional_only', 'positional_or_keyword', 'keyword_only'] | None` | The mode to use for the argument parameter | `None` | | `alias` | `str | list[str | int] | list[list[str | int]] | None` | The alias to use for the argument parameter | `None` |

Source code in `pydantic_core/core_schema.py`

````python
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

    param = core_schema.arguments_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    schema = core_schema.arguments_schema([param])
    v = SchemaValidator(schema)
    assert v.validate_python(('hello',)) == (('hello',), {})
    ```

    Args:
        name: The name to use for the argument parameter
        schema: The schema to use for the argument parameter
        mode: The mode to use for the argument parameter
        alias: The alias to use for the argument parameter
    """
    return _dict_not_none(name=name, schema=schema, mode=mode, alias=alias)

````

## arguments_schema

```python
arguments_schema(
    arguments: list[ArgumentsParameter],
    *,
    validate_by_name: bool | None = None,
    validate_by_alias: bool | None = None,
    var_args_schema: CoreSchema | None = None,
    var_kwargs_mode: VarKwargsMode | None = None,
    var_kwargs_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> ArgumentsSchema

```

Returns a schema that matches an arguments schema, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

param_a = core_schema.arguments_parameter(
    name='a', schema=core_schema.str_schema(), mode='positional_only'
)
param_b = core_schema.arguments_parameter(
    name='b', schema=core_schema.bool_schema(), mode='positional_only'
)
schema = core_schema.arguments_schema([param_a, param_b])
v = SchemaValidator(schema)
assert v.validate_python(('hello', True)) == (('hello', True), {})

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `arguments` | `list[ArgumentsParameter]` | The arguments to use for the arguments schema | *required* | | `validate_by_name` | `bool | None` | Whether to populate by the parameter names, defaults to False. | `None` | | `validate_by_alias` | `bool | None` | Whether to populate by the parameter aliases, defaults to True. | `None` | | `var_args_schema` | `CoreSchema | None` | The variable args schema to use for the arguments schema | `None` | | `var_kwargs_mode` | `VarKwargsMode | None` | The validation mode to use for variadic keyword arguments. If 'uniform', every value of the keyword arguments will be validated against the var_kwargs_schema schema. If 'unpacked-typed-dict', the var_kwargs_schema argument must be a typed_dict_schema | `None` | | `var_kwargs_schema` | `CoreSchema | None` | The variable kwargs schema to use for the arguments schema | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def arguments_schema(
    arguments: list[ArgumentsParameter],
    *,
    validate_by_name: bool | None = None,
    validate_by_alias: bool | None = None,
    var_args_schema: CoreSchema | None = None,
    var_kwargs_mode: VarKwargsMode | None = None,
    var_kwargs_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ArgumentsSchema:
    """
    Returns a schema that matches an arguments schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    param_a = core_schema.arguments_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    param_b = core_schema.arguments_parameter(
        name='b', schema=core_schema.bool_schema(), mode='positional_only'
    )
    schema = core_schema.arguments_schema([param_a, param_b])
    v = SchemaValidator(schema)
    assert v.validate_python(('hello', True)) == (('hello', True), {})
    ```

    Args:
        arguments: The arguments to use for the arguments schema
        validate_by_name: Whether to populate by the parameter names, defaults to `False`.
        validate_by_alias: Whether to populate by the parameter aliases, defaults to `True`.
        var_args_schema: The variable args schema to use for the arguments schema
        var_kwargs_mode: The validation mode to use for variadic keyword arguments. If `'uniform'`, every value of the
            keyword arguments will be validated against the `var_kwargs_schema` schema. If `'unpacked-typed-dict'`,
            the `var_kwargs_schema` argument must be a [`typed_dict_schema`][pydantic_core.core_schema.typed_dict_schema]
        var_kwargs_schema: The variable kwargs schema to use for the arguments schema
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='arguments',
        arguments_schema=arguments,
        validate_by_name=validate_by_name,
        validate_by_alias=validate_by_alias,
        var_args_schema=var_args_schema,
        var_kwargs_mode=var_kwargs_mode,
        var_kwargs_schema=var_kwargs_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## arguments_v3_parameter

```python
arguments_v3_parameter(
    name: str,
    schema: CoreSchema,
    *,
    mode: (
        Literal[
            "positional_only",
            "positional_or_keyword",
            "keyword_only",
            "var_args",
            "var_kwargs_uniform",
            "var_kwargs_unpacked_typed_dict",
        ]
        | None
    ) = None,
    alias: (
        str | list[str | int] | list[list[str | int]] | None
    ) = None
) -> ArgumentsV3Parameter

```

Returns a schema that matches an argument parameter, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

param = core_schema.arguments_v3_parameter(
    name='a', schema=core_schema.str_schema(), mode='positional_only'
)
schema = core_schema.arguments_v3_schema([param])
v = SchemaValidator(schema)
assert v.validate_python({'a': 'hello'}) == (('hello',), {})

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `name` | `str` | The name to use for the argument parameter | *required* | | `schema` | `CoreSchema` | The schema to use for the argument parameter | *required* | | `mode` | `Literal['positional_only', 'positional_or_keyword', 'keyword_only', 'var_args', 'var_kwargs_uniform', 'var_kwargs_unpacked_typed_dict'] | None` | The mode to use for the argument parameter | `None` | | `alias` | `str | list[str | int] | list[list[str | int]] | None` | The alias to use for the argument parameter | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def arguments_v3_parameter(
    name: str,
    schema: CoreSchema,
    *,
    mode: Literal[
        'positional_only',
        'positional_or_keyword',
        'keyword_only',
        'var_args',
        'var_kwargs_uniform',
        'var_kwargs_unpacked_typed_dict',
    ]
    | None = None,
    alias: str | list[str | int] | list[list[str | int]] | None = None,
) -> ArgumentsV3Parameter:
    """
    Returns a schema that matches an argument parameter, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    param = core_schema.arguments_v3_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    schema = core_schema.arguments_v3_schema([param])
    v = SchemaValidator(schema)
    assert v.validate_python({'a': 'hello'}) == (('hello',), {})
    ```

    Args:
        name: The name to use for the argument parameter
        schema: The schema to use for the argument parameter
        mode: The mode to use for the argument parameter
        alias: The alias to use for the argument parameter
    """
    return _dict_not_none(name=name, schema=schema, mode=mode, alias=alias)

````

## arguments_v3_schema

```python
arguments_v3_schema(
    arguments: list[ArgumentsV3Parameter],
    *,
    validate_by_name: bool | None = None,
    validate_by_alias: bool | None = None,
    extra_behavior: (
        Literal["forbid", "ignore"] | None
    ) = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> ArgumentsV3Schema

```

Returns a schema that matches an arguments schema, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

param_a = core_schema.arguments_v3_parameter(
    name='a', schema=core_schema.str_schema(), mode='positional_only'
)
param_b = core_schema.arguments_v3_parameter(
    name='kwargs', schema=core_schema.bool_schema(), mode='var_kwargs_uniform'
)
schema = core_schema.arguments_v3_schema([param_a, param_b])
v = SchemaValidator(schema)
assert v.validate_python({'a': 'hi', 'kwargs': {'b': True}}) == (('hi',), {'b': True})

```

This schema is currently not used by other Pydantic components. In V3, it will most likely become the default arguments schema for the `'call'` schema.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `arguments` | `list[ArgumentsV3Parameter]` | The arguments to use for the arguments schema. | *required* | | `validate_by_name` | `bool | None` | Whether to populate by the parameter names, defaults to False. | `None` | | `validate_by_alias` | `bool | None` | Whether to populate by the parameter aliases, defaults to True. | `None` | | `extra_behavior` | `Literal['forbid', 'ignore'] | None` | The extra behavior to use. | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places. | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core. | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema. | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def arguments_v3_schema(
    arguments: list[ArgumentsV3Parameter],
    *,
    validate_by_name: bool | None = None,
    validate_by_alias: bool | None = None,
    extra_behavior: Literal['forbid', 'ignore'] | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> ArgumentsV3Schema:
    """
    Returns a schema that matches an arguments schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    param_a = core_schema.arguments_v3_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    param_b = core_schema.arguments_v3_parameter(
        name='kwargs', schema=core_schema.bool_schema(), mode='var_kwargs_uniform'
    )
    schema = core_schema.arguments_v3_schema([param_a, param_b])
    v = SchemaValidator(schema)
    assert v.validate_python({'a': 'hi', 'kwargs': {'b': True}}) == (('hi',), {'b': True})
    ```

    This schema is currently not used by other Pydantic components. In V3, it will most likely
    become the default arguments schema for the `'call'` schema.

    Args:
        arguments: The arguments to use for the arguments schema.
        validate_by_name: Whether to populate by the parameter names, defaults to `False`.
        validate_by_alias: Whether to populate by the parameter aliases, defaults to `True`.
        extra_behavior: The extra behavior to use.
        ref: optional unique identifier of the schema, used to reference the schema in other places.
        metadata: Any other information you want to include with the schema, not used by pydantic-core.
        serialization: Custom serialization schema.
    """
    return _dict_not_none(
        type='arguments-v3',
        arguments_schema=arguments,
        validate_by_name=validate_by_name,
        validate_by_alias=validate_by_alias,
        extra_behavior=extra_behavior,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## call_schema

```python
call_schema(
    arguments: CoreSchema,
    function: Callable[..., Any],
    *,
    function_name: str | None = None,
    return_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> CallSchema

```

Returns a schema that matches an arguments schema, then calls a function, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

param_a = core_schema.arguments_parameter(
    name='a', schema=core_schema.str_schema(), mode='positional_only'
)
param_b = core_schema.arguments_parameter(
    name='b', schema=core_schema.bool_schema(), mode='positional_only'
)
args_schema = core_schema.arguments_schema([param_a, param_b])

schema = core_schema.call_schema(
    arguments=args_schema,
    function=lambda a, b: a + str(not b),
    return_schema=core_schema.str_schema(),
)
v = SchemaValidator(schema)
assert v.validate_python((('hello', True))) == 'helloFalse'

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `arguments` | `CoreSchema` | The arguments to use for the arguments schema | *required* | | `function` | `Callable[..., Any]` | The function to use for the call schema | *required* | | `function_name` | `str | None` | The function name to use for the call schema, if not provided function.__name__ is used | `None` | | `return_schema` | `CoreSchema | None` | The return schema to use for the call schema | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def call_schema(
    arguments: CoreSchema,
    function: Callable[..., Any],
    *,
    function_name: str | None = None,
    return_schema: CoreSchema | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> CallSchema:
    """
    Returns a schema that matches an arguments schema, then calls a function, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    param_a = core_schema.arguments_parameter(
        name='a', schema=core_schema.str_schema(), mode='positional_only'
    )
    param_b = core_schema.arguments_parameter(
        name='b', schema=core_schema.bool_schema(), mode='positional_only'
    )
    args_schema = core_schema.arguments_schema([param_a, param_b])

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
        function_name: The function name to use for the call schema, if not provided `function.__name__` is used
        return_schema: The return schema to use for the call schema
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='call',
        arguments_schema=arguments,
        function=function,
        function_name=function_name,
        return_schema=return_schema,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## custom_error_schema

```python
custom_error_schema(
    schema: CoreSchema,
    custom_error_type: str,
    *,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, Any] | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> CustomErrorSchema

```

Returns a schema that matches a custom error value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.custom_error_schema(
    schema=core_schema.int_schema(),
    custom_error_type='MyError',
    custom_error_message='Error msg',
)
v = SchemaValidator(schema)
v.validate_python(1)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The schema to use for the custom error schema | *required* | | `custom_error_type` | `str` | The custom error type to use for the custom error schema | *required* | | `custom_error_message` | `str | None` | The custom error message to use for the custom error schema | `None` | | `custom_error_context` | `dict[str, Any] | None` | The custom error context to use for the custom error schema | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def custom_error_schema(
    schema: CoreSchema,
    custom_error_type: str,
    *,
    custom_error_message: str | None = None,
    custom_error_context: dict[str, Any] | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> CustomErrorSchema:
    """
    Returns a schema that matches a custom error value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.custom_error_schema(
        schema=core_schema.int_schema(),
        custom_error_type='MyError',
        custom_error_message='Error msg',
    )
    v = SchemaValidator(schema)
    v.validate_python(1)
    ```

    Args:
        schema: The schema to use for the custom error schema
        custom_error_type: The custom error type to use for the custom error schema
        custom_error_message: The custom error message to use for the custom error schema
        custom_error_context: The custom error context to use for the custom error schema
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='custom-error',
        schema=schema,
        custom_error_type=custom_error_type,
        custom_error_message=custom_error_message,
        custom_error_context=custom_error_context,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## json_schema

```python
json_schema(
    schema: CoreSchema | None = None,
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> JsonSchema

```

Returns a schema that matches a JSON value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

dict_schema = core_schema.model_fields_schema(
    {
        'field_a': core_schema.model_field(core_schema.str_schema()),
        'field_b': core_schema.model_field(core_schema.bool_schema()),
    },
)

class MyModel:
    __slots__ = (
        '__dict__',
        '__pydantic_fields_set__',
        '__pydantic_extra__',
        '__pydantic_private__',
    )
    field_a: str
    field_b: bool

json_schema = core_schema.json_schema(schema=dict_schema)
schema = core_schema.model_schema(cls=MyModel, schema=json_schema)
v = SchemaValidator(schema)
m = v.validate_python('{"field_a": "hello", "field_b": true}')
assert isinstance(m, MyModel)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema | None` | The schema to use for the JSON schema | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def json_schema(
    schema: CoreSchema | None = None,
    *,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> JsonSchema:
    """
    Returns a schema that matches a JSON value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    dict_schema = core_schema.model_fields_schema(
        {
            'field_a': core_schema.model_field(core_schema.str_schema()),
            'field_b': core_schema.model_field(core_schema.bool_schema()),
        },
    )

    class MyModel:
        __slots__ = (
            '__dict__',
            '__pydantic_fields_set__',
            '__pydantic_extra__',
            '__pydantic_private__',
        )
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
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(type='json', schema=schema, ref=ref, metadata=metadata, serialization=serialization)

````

## url_schema

```python
url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    preserve_empty_path: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> UrlSchema

```

Returns a schema that matches a URL value, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.url_schema()
v = SchemaValidator(schema)
print(v.validate_python('https://example.com'))
#> https://example.com/

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `max_length` | `int | None` | The maximum length of the URL | `None` | | `allowed_schemes` | `list[str] | None` | The allowed URL schemes | `None` | | `host_required` | `bool | None` | Whether the URL must have a host | `None` | | `default_host` | `str | None` | The default host to use if the URL does not have a host | `None` | | `default_port` | `int | None` | The default port to use if the URL does not have a port | `None` | | `default_path` | `str | None` | The default path to use if the URL does not have a path | `None` | | `preserve_empty_path` | `bool | None` | Whether to preserve an empty path or convert it to '/', default False | `None` | | `strict` | `bool | None` | Whether to use strict URL parsing | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    preserve_empty_path: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> UrlSchema:
    """
    Returns a schema that matches a URL value, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.url_schema()
    v = SchemaValidator(schema)
    print(v.validate_python('https://example.com'))
    #> https://example.com/
    ```

    Args:
        max_length: The maximum length of the URL
        allowed_schemes: The allowed URL schemes
        host_required: Whether the URL must have a host
        default_host: The default host to use if the URL does not have a host
        default_port: The default port to use if the URL does not have a port
        default_path: The default path to use if the URL does not have a path
        preserve_empty_path: Whether to preserve an empty path or convert it to '/', default False
        strict: Whether to use strict URL parsing
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='url',
        max_length=max_length,
        allowed_schemes=allowed_schemes,
        host_required=host_required,
        default_host=default_host,
        default_port=default_port,
        default_path=default_path,
        preserve_empty_path=preserve_empty_path,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## multi_host_url_schema

```python
multi_host_url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    preserve_empty_path: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None
) -> MultiHostUrlSchema

```

Returns a schema that matches a URL value with possibly multiple hosts, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.multi_host_url_schema()
v = SchemaValidator(schema)
print(v.validate_python('redis://localhost,0.0.0.0,127.0.0.1'))
#> redis://localhost,0.0.0.0,127.0.0.1

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `max_length` | `int | None` | The maximum length of the URL | `None` | | `allowed_schemes` | `list[str] | None` | The allowed URL schemes | `None` | | `host_required` | `bool | None` | Whether the URL must have a host | `None` | | `default_host` | `str | None` | The default host to use if the URL does not have a host | `None` | | `default_port` | `int | None` | The default port to use if the URL does not have a port | `None` | | `default_path` | `str | None` | The default path to use if the URL does not have a path | `None` | | `preserve_empty_path` | `bool | None` | Whether to preserve an empty path or convert it to '/', default False | `None` | | `strict` | `bool | None` | Whether to use strict URL parsing | `None` | | `ref` | `str | None` | optional unique identifier of the schema, used to reference the schema in other places | `None` | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def multi_host_url_schema(
    *,
    max_length: int | None = None,
    allowed_schemes: list[str] | None = None,
    host_required: bool | None = None,
    default_host: str | None = None,
    default_port: int | None = None,
    default_path: str | None = None,
    preserve_empty_path: bool | None = None,
    strict: bool | None = None,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> MultiHostUrlSchema:
    """
    Returns a schema that matches a URL value with possibly multiple hosts, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema = core_schema.multi_host_url_schema()
    v = SchemaValidator(schema)
    print(v.validate_python('redis://localhost,0.0.0.0,127.0.0.1'))
    #> redis://localhost,0.0.0.0,127.0.0.1
    ```

    Args:
        max_length: The maximum length of the URL
        allowed_schemes: The allowed URL schemes
        host_required: Whether the URL must have a host
        default_host: The default host to use if the URL does not have a host
        default_port: The default port to use if the URL does not have a port
        default_path: The default path to use if the URL does not have a path
        preserve_empty_path: Whether to preserve an empty path or convert it to '/', default False
        strict: Whether to use strict URL parsing
        ref: optional unique identifier of the schema, used to reference the schema in other places
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='multi-host-url',
        max_length=max_length,
        allowed_schemes=allowed_schemes,
        host_required=host_required,
        default_host=default_host,
        default_port=default_port,
        default_path=default_path,
        preserve_empty_path=preserve_empty_path,
        strict=strict,
        ref=ref,
        metadata=metadata,
        serialization=serialization,
    )

````

## definitions_schema

```python
definitions_schema(
    schema: CoreSchema, definitions: list[CoreSchema]
) -> DefinitionsSchema

```

Build a schema that contains both an inner schema and a list of definitions which can be used within the inner schema.

```py
from pydantic_core import SchemaValidator, core_schema

schema = core_schema.definitions_schema(
    core_schema.list_schema(core_schema.definition_reference_schema('foobar')),
    [core_schema.int_schema(ref='foobar')],
)
v = SchemaValidator(schema)
assert v.validate_python([1, 2, '3']) == [1, 2, 3]

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The inner schema | *required* | | `definitions` | `list[CoreSchema]` | List of definitions which can be referenced within inner schema | *required* |

Source code in `pydantic_core/core_schema.py`

````python
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

````

## definition_reference_schema

```python
definition_reference_schema(
    schema_ref: str,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DefinitionReferenceSchema

```

Returns a schema that points to a schema stored in "definitions", this is useful for nested recursive models and also when you want to define validators separately from the main schema, e.g.:

```py
from pydantic_core import SchemaValidator, core_schema

schema_definition = core_schema.definition_reference_schema('list-schema')
schema = core_schema.definitions_schema(
    schema=schema_definition,
    definitions=[
        core_schema.list_schema(items_schema=schema_definition, ref='list-schema'),
    ],
)
v = SchemaValidator(schema)
assert v.validate_python([()]) == [[]]

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema_ref` | `str` | The schema ref to use for the definition reference schema | *required* | | `metadata` | `dict[str, Any] | None` | Any other information you want to include with the schema, not used by pydantic-core | `None` | | `serialization` | `SerSchema | None` | Custom serialization schema | `None` |

Source code in `pydantic_core/core_schema.py`

````python
def definition_reference_schema(
    schema_ref: str,
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
    serialization: SerSchema | None = None,
) -> DefinitionReferenceSchema:
    """
    Returns a schema that points to a schema stored in "definitions", this is useful for nested recursive
    models and also when you want to define validators separately from the main schema, e.g.:

    ```py
    from pydantic_core import SchemaValidator, core_schema

    schema_definition = core_schema.definition_reference_schema('list-schema')
    schema = core_schema.definitions_schema(
        schema=schema_definition,
        definitions=[
            core_schema.list_schema(items_schema=schema_definition, ref='list-schema'),
        ],
    )
    v = SchemaValidator(schema)
    assert v.validate_python([()]) == [[]]
    ```

    Args:
        schema_ref: The schema ref to use for the definition reference schema
        metadata: Any other information you want to include with the schema, not used by pydantic-core
        serialization: Custom serialization schema
    """
    return _dict_not_none(
        type='definition-ref', schema_ref=schema_ref, ref=ref, metadata=metadata, serialization=serialization
    )

````
