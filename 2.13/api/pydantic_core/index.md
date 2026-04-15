## __version__

```python
__version__: str

```

## SchemaValidator

```python
SchemaValidator(
    schema: CoreSchema,
    config: CoreConfig | None = None,
    _use_prebuilt: bool = True,
)

```

`SchemaValidator` is the Python wrapper for `pydantic-core`'s Rust validation logic, internally it owns one `CombinedValidator` which may in turn own more `CombinedValidator`s which make up the full schema validator.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The CoreSchema to use for validation. | *required* | | `config` | `CoreConfig | None` | Optionally a CoreConfig to configure validation. | `None` | | `_use_prebuilt` | `bool` | Whether to use pre-built validators (False during rebuilds to avoid stale references). | `True` |

### title

```python
title: str

```

The title of the schema, as used in the heading of ValidationError.__str__().

### validate_python

```python
validate_python(
    input: Any,
    *,
    strict: bool | None = None,
    extra: ExtraBehavior | None = None,
    from_attributes: bool | None = None,
    context: Any | None = None,
    self_instance: Any | None = None,
    allow_partial: (
        bool | Literal["off", "on", "trailing-strings"]
    ) = False,
    by_alias: bool | None = None,
    by_name: bool | None = None
) -> Any

```

Validate a Python object against the schema and return the validated object.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `input` | `Any` | The Python object to validate. | *required* | | `strict` | `bool | None` | Whether to validate the object in strict mode. If None, the value of CoreConfig.strict is used. | `None` | | `extra` | `ExtraBehavior | None` | Whether to ignore, allow, or forbid extra data during model validation. If None, the value of CoreConfig.extra_fields_behavior is used. | `None` | | `from_attributes` | `bool | None` | Whether to validate objects as inputs to models by extracting attributes. If None, the value of CoreConfig.from_attributes is used. | `None` | | `context` | `Any | None` | The context to use for validation, this is passed to functional validators as info.context. | `None` | | `self_instance` | `Any | None` | An instance of a model set attributes on from validation, this is used when running validation from the __init__ method of a model. | `None` | | `allow_partial` | `bool | Literal['off', 'on', 'trailing-strings']` | Whether to allow partial validation; if True errors in the last element of sequences and mappings are ignored. 'trailing-strings' means any final unfinished JSON string is included in the result. | `False` | | `by_alias` | `bool | None` | Whether to use the field's alias when validating against the provided input data. | `None` | | `by_name` | `bool | None` | Whether to use the field's name when validating against the provided input data. | `None` |

Raises:

| Type | Description | | --- | --- | | `ValidationError` | If validation fails. | | `Exception` | Other error types maybe raised if internal errors occur. |

Returns:

| Type | Description | | --- | --- | | `Any` | The validated object. |

### isinstance_python

```python
isinstance_python(
    input: Any,
    *,
    strict: bool | None = None,
    extra: ExtraBehavior | None = None,
    from_attributes: bool | None = None,
    context: Any | None = None,
    self_instance: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None
) -> bool

```

Similar to validate_python() but returns a boolean.

Arguments match `validate_python()`. This method will not raise `ValidationError`s but will raise internal errors.

Returns:

| Type | Description | | --- | --- | | `bool` | True if validation succeeds, False if validation fails. |

### validate_json

```python
validate_json(
    input: str | bytes | bytearray,
    *,
    strict: bool | None = None,
    extra: ExtraBehavior | None = None,
    context: Any | None = None,
    self_instance: Any | None = None,
    allow_partial: (
        bool | Literal["off", "on", "trailing-strings"]
    ) = False,
    by_alias: bool | None = None,
    by_name: bool | None = None
) -> Any

```

Validate JSON data directly against the schema and return the validated Python object.

This method should be significantly faster than `validate_python(json.loads(json_data))` as it avoids the need to create intermediate Python objects

It also handles constructing the correct Python type even in strict mode, where `validate_python(json.loads(json_data))` would fail validation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `input` | `str | bytes | bytearray` | The JSON data to validate. | *required* | | `strict` | `bool | None` | Whether to validate the object in strict mode. If None, the value of CoreConfig.strict is used. | `None` | | `extra` | `ExtraBehavior | None` | Whether to ignore, allow, or forbid extra data during model validation. If None, the value of CoreConfig.extra_fields_behavior is used. | `None` | | `context` | `Any | None` | The context to use for validation, this is passed to functional validators as info.context. | `None` | | `self_instance` | `Any | None` | An instance of a model set attributes on from validation. | `None` | | `allow_partial` | `bool | Literal['off', 'on', 'trailing-strings']` | Whether to allow partial validation; if True incomplete JSON will be parsed successfully and errors in the last element of sequences and mappings are ignored. 'trailing-strings' means any final unfinished JSON string is included in the result. | `False` | | `by_alias` | `bool | None` | Whether to use the field's alias when validating against the provided input data. | `None` | | `by_name` | `bool | None` | Whether to use the field's name when validating against the provided input data. | `None` |

Raises:

| Type | Description | | --- | --- | | `ValidationError` | If validation fails or if the JSON data is invalid. | | `Exception` | Other error types maybe raised if internal errors occur. |

Returns:

| Type | Description | | --- | --- | | `Any` | The validated Python object. |

### validate_strings

```python
validate_strings(
    input: _StringInput,
    *,
    strict: bool | None = None,
    extra: ExtraBehavior | None = None,
    context: Any | None = None,
    allow_partial: (
        bool | Literal["off", "on", "trailing-strings"]
    ) = False,
    by_alias: bool | None = None,
    by_name: bool | None = None
) -> Any

```

Validate a string against the schema and return the validated Python object.

This is similar to `validate_json` but applies to scenarios where the input will be a string but not JSON data, e.g. URL fragments, query parameters, etc.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `input` | `_StringInput` | The input as a string, or bytes/bytearray if strict=False. | *required* | | `strict` | `bool | None` | Whether to validate the object in strict mode. If None, the value of CoreConfig.strict is used. | `None` | | `extra` | `ExtraBehavior | None` | Whether to ignore, allow, or forbid extra data during model validation. If None, the value of CoreConfig.extra_fields_behavior is used. | `None` | | `context` | `Any | None` | The context to use for validation, this is passed to functional validators as info.context. | `None` | | `allow_partial` | `bool | Literal['off', 'on', 'trailing-strings']` | Whether to allow partial validation; if True errors in the last element of sequences and mappings are ignored. 'trailing-strings' means any final unfinished JSON string is included in the result. | `False` | | `by_alias` | `bool | None` | Whether to use the field's alias when validating against the provided input data. | `None` | | `by_name` | `bool | None` | Whether to use the field's name when validating against the provided input data. | `None` |

Raises:

| Type | Description | | --- | --- | | `ValidationError` | If validation fails or if the JSON data is invalid. | | `Exception` | Other error types maybe raised if internal errors occur. |

Returns:

| Type | Description | | --- | --- | | `Any` | The validated Python object. |

### validate_assignment

```python
validate_assignment(
    obj: Any,
    field_name: str,
    field_value: Any,
    *,
    strict: bool | None = None,
    extra: ExtraBehavior | None = None,
    from_attributes: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None
) -> (
    dict[str, Any]
    | tuple[dict[str, Any], dict[str, Any] | None, set[str]]
)

```

Validate an assignment to a field on a model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `obj` | `Any` | The model instance being assigned to. | *required* | | `field_name` | `str` | The name of the field to validate assignment for. | *required* | | `field_value` | `Any` | The value to assign to the field. | *required* | | `strict` | `bool | None` | Whether to validate the object in strict mode. If None, the value of CoreConfig.strict is used. | `None` | | `extra` | `ExtraBehavior | None` | Whether to ignore, allow, or forbid extra data during model validation. If None, the value of CoreConfig.extra_fields_behavior is used. | `None` | | `from_attributes` | `bool | None` | Whether to validate objects as inputs to models by extracting attributes. If None, the value of CoreConfig.from_attributes is used. | `None` | | `context` | `Any | None` | The context to use for validation, this is passed to functional validators as info.context. | `None` | | `by_alias` | `bool | None` | Whether to use the field's alias when validating against the provided input data. | `None` | | `by_name` | `bool | None` | Whether to use the field's name when validating against the provided input data. | `None` |

Raises:

| Type | Description | | --- | --- | | `ValidationError` | If validation fails. | | `Exception` | Other error types maybe raised if internal errors occur. |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any] | tuple[dict[str, Any], dict[str, Any] | None, set[str]]` | Either the model dict or a tuple of (model_data, model_extra, fields_set) |

### get_default_value

```python
get_default_value(
    *, strict: bool | None = None, context: Any = None
) -> Some | None

```

Get the default value for the schema, including running default value validation.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `strict` | `bool | None` | Whether to validate the default value in strict mode. If None, the value of CoreConfig.strict is used. | `None` | | `context` | `Any` | The context to use for validation, this is passed to functional validators as info.context. | `None` |

Raises:

| Type | Description | | --- | --- | | `ValidationError` | If validation fails. | | `Exception` | Other error types maybe raised if internal errors occur. |

Returns:

| Type | Description | | --- | --- | | `Some | None` | None if the schema has no default value, otherwise a Some containing the default. |

## SchemaSerializer

```python
SchemaSerializer(
    schema: CoreSchema,
    config: CoreConfig | None = None,
    _use_prebuilt: bool = True,
)

```

`SchemaSerializer` is the Python wrapper for `pydantic-core`'s Rust serialization logic, internally it owns one `CombinedSerializer` which may in turn own more `CombinedSerializer`s which make up the full schema serializer.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `schema` | `CoreSchema` | The CoreSchema to use for serialization. | *required* | | `config` | `CoreConfig | None` | Optionally a CoreConfig to to configure serialization. | `None` | | `_use_prebuilt` | `bool` | Whether to use pre-built validators (False during rebuilds to avoid stale references). | `True` |

### to_python

```python
to_python(
    value: Any,
    *,
    mode: str | None = None,
    include: _IncEx | None = None,
    exclude: _IncEx | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: (
        bool | Literal["none", "warn", "error"]
    ) = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    polymorphic_serialization: bool | None = None,
    context: Any | None = None
) -> Any

```

Serialize/marshal a Python object to a Python object including transforming and filtering data.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `Any` | The Python object to serialize. | *required* | | `mode` | `str | None` | The serialization mode to use, either 'python' or 'json', defaults to 'python'. In JSON mode, all values are converted to JSON compatible types, e.g. None, int, float, str, list, dict. | `None` | | `include` | `_IncEx | None` | A set of fields to include, if None all fields are included. | `None` | | `exclude` | `_IncEx | None` | A set of fields to exclude, if None no fields are excluded. | `None` | | `by_alias` | `bool | None` | Whether to use the alias names of fields. | `None` | | `exclude_unset` | `bool` | Whether to exclude fields that are not set, e.g. are not included in __pydantic_fields_set__. | `False` | | `exclude_defaults` | `bool` | Whether to exclude fields that are equal to their default value. | `False` | | `exclude_none` | `bool` | Whether to exclude fields that have a value of None. | `False` | | `exclude_computed_fields` | `bool` | Whether to exclude computed fields. | `False` | | `round_trip` | `bool` | Whether to enable serialization and validation round-trip support. | `False` | | `warnings` | `bool | Literal['none', 'warn', 'error']` | How to handle invalid fields. False/"none" ignores them, True/"warn" logs errors, "error" raises a PydanticSerializationError. | `True` | | `fallback` | `Callable[[Any], Any] | None` | A function to call when an unknown value is encountered, if None a PydanticSerializationError error is raised. | `None` | | `serialize_as_any` | `bool` | Whether to serialize fields with duck-typing serialization behavior. | `False` | | `polymorphic_serialization` | `bool | None` | Whether to use model and dataclass polymorphic serialization for this call. | `None` | | `context` | `Any | None` | The context to use for serialization, this is passed to functional serializers as info.context. | `None` |

Raises:

| Type | Description | | --- | --- | | `PydanticSerializationError` | If serialization fails and no fallback function is provided. |

Returns:

| Type | Description | | --- | --- | | `Any` | The serialized Python object. |

### to_json

```python
to_json(
    value: Any,
    *,
    indent: int | None = None,
    ensure_ascii: bool = False,
    include: _IncEx | None = None,
    exclude: _IncEx | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    exclude_computed_fields: bool = False,
    round_trip: bool = False,
    warnings: (
        bool | Literal["none", "warn", "error"]
    ) = True,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    polymorphic_serialization: bool | None = None,
    context: Any | None = None
) -> bytes

```

Serialize a Python object to JSON including transforming and filtering data.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `Any` | The Python object to serialize. | *required* | | `indent` | `int | None` | If None, the JSON will be compact, otherwise it will be pretty-printed with the indent provided. | `None` | | `ensure_ascii` | `bool` | If True, the output is guaranteed to have all incoming non-ASCII characters escaped. If False (the default), these characters will be output as-is. | `False` | | `include` | `_IncEx | None` | A set of fields to include, if None all fields are included. | `None` | | `exclude` | `_IncEx | None` | A set of fields to exclude, if None no fields are excluded. | `None` | | `by_alias` | `bool | None` | Whether to use the alias names of fields. | `None` | | `exclude_unset` | `bool` | Whether to exclude fields that are not set, e.g. are not included in __pydantic_fields_set__. | `False` | | `exclude_defaults` | `bool` | Whether to exclude fields that are equal to their default value. | `False` | | `exclude_none` | `bool` | Whether to exclude fields that have a value of None. | `False` | | `exclude_computed_fields` | `bool` | Whether to exclude computed fields. | `False` | | `round_trip` | `bool` | Whether to enable serialization and validation round-trip support. | `False` | | `warnings` | `bool | Literal['none', 'warn', 'error']` | How to handle invalid fields. False/"none" ignores them, True/"warn" logs errors, "error" raises a PydanticSerializationError. | `True` | | `fallback` | `Callable[[Any], Any] | None` | A function to call when an unknown value is encountered, if None a PydanticSerializationError error is raised. | `None` | | `serialize_as_any` | `bool` | Whether to serialize fields with duck-typing serialization behavior. | `False` | | `polymorphic_serialization` | `bool | None` | Whether to use model and dataclass polymorphic serialization for this call. | `None` | | `context` | `Any | None` | The context to use for serialization, this is passed to functional serializers as info.context. | `None` |

Raises:

| Type | Description | | --- | --- | | `PydanticSerializationError` | If serialization fails and no fallback function is provided. |

Returns:

| Type | Description | | --- | --- | | `bytes` | JSON bytes. |

## ValidationError

Bases: `ValueError`

`ValidationError` is the exception raised by `pydantic-core` when validation fails, it contains a list of errors which detail why validation failed.

### title

```python
title: str

```

The title of the error, as used in the heading of `str(validation_error)`.

### from_exception_data

```python
from_exception_data(
    title: str,
    line_errors: list[InitErrorDetails],
    input_type: Literal["python", "json"] = "python",
    hide_input: bool = False,
) -> Self

```

Python constructor for a Validation Error.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `title` | `str` | The title of the error, as used in the heading of str(validation_error) | *required* | | `line_errors` | `list[InitErrorDetails]` | A list of InitErrorDetails which contain information about errors that occurred during validation. | *required* | | `input_type` | `Literal['python', 'json']` | Whether the error is for a Python object or JSON. | `'python'` | | `hide_input` | `bool` | Whether to hide the input value in the error message. | `False` |

### error_count

```python
error_count() -> int

```

Returns:

| Type | Description | | --- | --- | | `int` | The number of errors in the validation error. |

### errors

```python
errors(
    *,
    include_url: bool = True,
    include_context: bool = True,
    include_input: bool = True
) -> list[ErrorDetails]

```

Details about each error in the validation error.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `include_url` | `bool` | Whether to include a URL to documentation on the error each error. | `True` | | `include_context` | `bool` | Whether to include the context of each error. | `True` | | `include_input` | `bool` | Whether to include the input value of each error. | `True` |

Returns:

| Type | Description | | --- | --- | | `list[ErrorDetails]` | A list of ErrorDetails for each error in the validation error. |

### json

```python
json(
    *,
    indent: int | None = None,
    include_url: bool = True,
    include_context: bool = True,
    include_input: bool = True
) -> str

```

Same as errors() but returns a JSON string.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `indent` | `int | None` | The number of spaces to indent the JSON by, or None for no indentation - compact JSON. | `None` | | `include_url` | `bool` | Whether to include a URL to documentation on the error each error. | `True` | | `include_context` | `bool` | Whether to include the context of each error. | `True` | | `include_input` | `bool` | Whether to include the input value of each error. | `True` |

Returns:

| Type | Description | | --- | --- | | `str` | a JSON string. |

## ErrorDetails

Bases: `TypedDict`

### type

```python
type: str

```

The type of error that occurred, this is an identifier designed for programmatic use that will change rarely or never.

`type` is unique for each error message, and can hence be used as an identifier to build custom error messages.

### loc

```python
loc: tuple[int | str, ...]

```

Tuple of strings and ints identifying where in the schema the error occurred.

### msg

```python
msg: str

```

A human readable error message.

### input

```python
input: Any

```

The input data at this `loc` that caused the error.

### ctx

```python
ctx: NotRequired[dict[str, Any]]

```

Values which are required to render the error message, and could hence be useful in rendering custom error messages. Also useful for passing custom error data forward.

### url

```python
url: NotRequired[str]

```

The documentation URL giving information about the error. No URL is available if a PydanticCustomError is used.

## InitErrorDetails

Bases: `TypedDict`

### type

```python
type: str | PydanticCustomError

```

The type of error that occurred, this should be a "slug" identifier that changes rarely or never.

### loc

```python
loc: NotRequired[tuple[int | str, ...]]

```

Tuple of strings and ints identifying where in the schema the error occurred.

### input

```python
input: Any

```

The input data at this `loc` that caused the error.

### ctx

```python
ctx: NotRequired[dict[str, Any]]

```

Values which are required to render the error message, and could hence be useful in rendering custom error messages. Also useful for passing custom error data forward.

## SchemaError

Bases: `Exception`

Information about errors that occur while building a SchemaValidator or SchemaSerializer.

### error_count

```python
error_count() -> int

```

Returns:

| Type | Description | | --- | --- | | `int` | The number of errors in the schema. |

### errors

```python
errors() -> list[ErrorDetails]

```

Returns:

| Type | Description | | --- | --- | | `list[ErrorDetails]` | A list of ErrorDetails for each error in the schema. |

## PydanticCustomError

```python
PydanticCustomError(
    error_type: LiteralString,
    message_template: LiteralString,
    context: dict[str, Any] | None = None,
)

```

Bases: `ValueError`

A custom exception providing flexible error handling for Pydantic validators.

You can raise this error in custom validators when you'd like flexibility in regards to the error type, message, and context.

Example

```py
from pydantic_core import PydanticCustomError

def custom_validator(v) -> None:
    if v <= 10:
        raise PydanticCustomError('custom_value_error', 'Value must be greater than {value}', {'value': 10, 'extra_context': 'extra_data'})
    return v

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `error_type` | `LiteralString` | The error type. | *required* | | `message_template` | `LiteralString` | The message template. | *required* | | `context` | `dict[str, Any] | None` | The data to inject into the message template. | `None` |

### context

```python
context: dict[str, Any] | None

```

Values which are required to render the error message, and could hence be useful in passing error data forward.

### type

```python
type: str

```

The error type associated with the error. For consistency with Pydantic, this is typically a snake_case string.

### message_template

```python
message_template: str

```

The message template associated with the error. This is a string that can be formatted with context variables in `{curly_braces}`.

### message

```python
message() -> str

```

The formatted message associated with the error. This presents as the message template with context variables appropriately injected.

## PydanticKnownError

```python
PydanticKnownError(
    error_type: ErrorType,
    context: dict[str, Any] | None = None,
)

```

Bases: `ValueError`

A helper class for raising exceptions that mimic Pydantic's built-in exceptions, with more flexibility in regards to context.

Unlike PydanticCustomError, the `error_type` argument must be a known `ErrorType`.

Example

```py
from pydantic_core import PydanticKnownError

def custom_validator(v) -> None:
    if v <= 10:
        raise PydanticKnownError('greater_than', {'gt': 10})
    return v

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `error_type` | `ErrorType` | The error type. | *required* | | `context` | `dict[str, Any] | None` | The data to inject into the message template. | `None` |

### context

```python
context: dict[str, Any] | None

```

Values which are required to render the error message, and could hence be useful in passing error data forward.

### type

```python
type: ErrorType

```

The type of the error.

### message_template

```python
message_template: str

```

The message template associated with the provided error type. This is a string that can be formatted with context variables in `{curly_braces}`.

### message

```python
message() -> str

```

The formatted message associated with the error. This presents as the message template with context variables appropriately injected.

## PydanticOmit

Bases: `Exception`

An exception to signal that a field should be omitted from a generated result.

This could span from omitting a field from a JSON Schema to omitting a field from a serialized result. Upcoming: more robust support for using PydanticOmit in custom serializers is still in development. Right now, this is primarily used in the JSON Schema generation process.

Example

```py
from typing import Callable

from pydantic_core import PydanticOmit

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class MyGenerateJsonSchema(GenerateJsonSchema):
    def handle_invalid_for_json_schema(self, schema, error_info) -> JsonSchemaValue:
        raise PydanticOmit


class Predicate(BaseModel):
    name: str = 'no-op'
    func: Callable = lambda x: x


instance_example = Predicate()

validation_schema = instance_example.model_json_schema(schema_generator=MyGenerateJsonSchema, mode='validation')
print(validation_schema)
'''
{'properties': {'name': {'default': 'no-op', 'title': 'Name', 'type': 'string'}}, 'title': 'Predicate', 'type': 'object'}
'''

```

For a more in depth example / explanation, see the [customizing JSON schema](../../concepts/json_schema/#customizing-the-json-schema-generation-process) docs.

## PydanticUseDefault

Bases: `Exception`

An exception to signal that standard validation either failed or should be skipped, and the default value should be used instead.

This warning can be raised in custom validation functions to redirect the flow of validation.

Example

```py
from pydantic_core import PydanticUseDefault
from datetime import datetime
from pydantic import BaseModel, field_validator


class Event(BaseModel):
    name: str = 'meeting'
    time: datetime

    @field_validator('name', mode='plain')
    def name_must_be_present(cls, v) -> str:
        if not v or not isinstance(v, str):
            raise PydanticUseDefault()
        return v


event1 = Event(name='party', time=datetime(2024, 1, 1, 12, 0, 0))
print(repr(event1))
# > Event(name='party', time=datetime.datetime(2024, 1, 1, 12, 0))
event2 = Event(time=datetime(2024, 1, 1, 12, 0, 0))
print(repr(event2))
# > Event(name='meeting', time=datetime.datetime(2024, 1, 1, 12, 0))

```

For an additional example, see the [validating partial json data](../../concepts/json/#partial-json-parsing) section of the Pydantic documentation.

## PydanticSerializationError

```python
PydanticSerializationError(message: str)

```

Bases: `ValueError`

An error raised when an issue occurs during serialization.

In custom serializers, this error can be used to indicate that serialization has failed.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `message` | `str` | The message associated with the error. | *required* |

## PydanticSerializationUnexpectedValue

```python
PydanticSerializationUnexpectedValue(message: str)

```

Bases: `ValueError`

An error raised when an unexpected value is encountered during serialization.

This error is often caught and coerced into a warning, as `pydantic-core` generally makes a best attempt at serializing values, in contrast with validation where errors are eagerly raised.

Example

```py
from pydantic import BaseModel, field_serializer
from pydantic_core import PydanticSerializationUnexpectedValue

class BasicPoint(BaseModel):
    x: int
    y: int

    @field_serializer('*')
    def serialize(self, v):
        if not isinstance(v, int):
            raise PydanticSerializationUnexpectedValue(f'Expected type `int`, got {type(v)} with value {v}')
        return v

point = BasicPoint(x=1, y=2)
# some sort of mutation
point.x = 'a'

print(point.model_dump())
'''
UserWarning: Pydantic serializer warnings:
PydanticSerializationUnexpectedValue(Expected type `int`, got <class 'str'> with value a)
return self.__pydantic_serializer__.to_python(
{'x': 'a', 'y': 2}
'''

```

This is often used internally in `pydantic-core` when unexpected types are encountered during serialization, but it can also be used by users in custom serializers, as seen above.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `message` | `str` | The message associated with the unexpected value. | *required* |

## Url

```python
Url(url: str)

```

Bases: `SupportsAllComparisons`

A URL type, internal logic uses the [url rust crate](https://docs.rs/url/latest/url/) originally developed by Mozilla.

## MultiHostUrl

```python
MultiHostUrl(url: str)

```

Bases: `SupportsAllComparisons`

A URL type with support for multiple hosts, as used by some databases for DSNs, e.g. `https://foo.com,bar.com/path`.

Internal URL logic uses the [url rust crate](https://docs.rs/url/latest/url/) originally developed by Mozilla.

## MultiHostHost

Bases: `TypedDict`

A host part of a multi-host URL.

### username

```python
username: str | None

```

The username part of this host, or `None`.

### password

```python
password: str | None

```

The password part of this host, or `None`.

### host

```python
host: str | None

```

The host part of this host, or `None`.

### port

```python
port: int | None

```

The port part of this host, or `None`.

## ArgsKwargs

```python
ArgsKwargs(
    args: tuple[Any, ...],
    kwargs: dict[str, Any] | None = None,
)

```

A construct used to store arguments and keyword arguments for a function call.

This data structure is generally used to store information for core schemas associated with functions (like in an arguments schema). This data structure is also currently used for some validation against dataclasses.

Example

```py
from pydantic.dataclasses import dataclass
from pydantic import model_validator


@dataclass
class Model:
    a: int
    b: int

    @model_validator(mode="before")
    @classmethod
    def no_op_validator(cls, values):
        print(values)
        return values

Model(1, b=2)
#> ArgsKwargs((1,), {"b": 2})

Model(1, 2)
#> ArgsKwargs((1, 2), {})

Model(a=1, b=2)
#> ArgsKwargs((), {"a": 1, "b": 2})

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `args` | `tuple[Any, ...]` | The arguments (inherently ordered) for a function call. | *required* | | `kwargs` | `dict[str, Any] | None` | The keyword arguments for a function call | `None` |

### args

```python
args: tuple[Any, ...]

```

The arguments (inherently ordered) for a function call.

### kwargs

```python
kwargs: dict[str, Any] | None

```

The keyword arguments for a function call.

## Some

Bases: `Generic[_T]`

Similar to Rust's [`Option::Some`](https://doc.rust-lang.org/std/option/enum.Option.html) type, this identifies a value as being present, and provides a way to access it.

Generally used in a union with `None` to different between "some value which could be None" and no value.

### value

```python
value: _T

```

Returns the value wrapped by `Some`.

## TzInfo

```python
TzInfo(seconds: float = 0.0)

```

Bases: `tzinfo`

An `pydantic-core` implementation of the abstract datetime.tzinfo class.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `seconds` | `float` | The offset from UTC in seconds. Defaults to 0.0 (UTC). | `0.0` |

### tzname

```python
tzname(dt: datetime | None) -> str | None

```

Return the time zone name corresponding to the datetime object *dt*, as a string.

For more info, see tzinfo.tzname.

### utcoffset

```python
utcoffset(dt: datetime | None) -> timedelta | None

```

Return offset of local time from UTC, as a timedelta object that is positive east of UTC. If local time is west of UTC, this should be negative.

More info can be found at tzinfo.utcoffset.

### dst

```python
dst(dt: datetime | None) -> timedelta | None

```

Return the daylight saving time (DST) adjustment, as a timedelta object or `None` if DST information isn’t known.

More info can be found attzinfo.dst.

### fromutc

```python
fromutc(dt: datetime) -> datetime

```

Adjust the date and time data associated datetime object *dt*, returning an equivalent datetime in self’s local time.

More info can be found at tzinfo.fromutc.

## ErrorTypeInfo

Bases: `TypedDict`

Gives information about errors.

### type

```python
type: ErrorType

```

The type of error that occurred, this should be a "slug" identifier that changes rarely or never.

### message_template_python

```python
message_template_python: str

```

String template to render a human readable error message from using context, when the input is Python.

### example_message_python

```python
example_message_python: str

```

Example of a human readable error message, when the input is Python.

### message_template_json

```python
message_template_json: NotRequired[str]

```

String template to render a human readable error message from using context, when the input is JSON data.

### example_message_json

```python
example_message_json: NotRequired[str]

```

Example of a human readable error message, when the input is JSON data.

### example_context

```python
example_context: dict[str, Any] | None

```

Example of context values.

## to_json

```python
to_json(
    value: Any,
    *,
    indent: int | None = None,
    ensure_ascii: bool = False,
    include: _IncEx | None = None,
    exclude: _IncEx | None = None,
    by_alias: bool = True,
    exclude_none: bool = False,
    round_trip: bool = False,
    timedelta_mode: Literal["iso8601", "float"] = "iso8601",
    temporal_mode: Literal[
        "iso8601", "seconds", "milliseconds"
    ] = "iso8601",
    bytes_mode: Literal["utf8", "base64", "hex"] = "utf8",
    inf_nan_mode: Literal[
        "null", "constants", "strings"
    ] = "constants",
    serialize_unknown: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    polymorphic_serialization: bool | None = None,
    context: Any | None = None
) -> bytes

```

Serialize a Python object to JSON including transforming and filtering data.

This is effectively a standalone version of SchemaSerializer.to_json.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `Any` | The Python object to serialize. | *required* | | `indent` | `int | None` | If None, the JSON will be compact, otherwise it will be pretty-printed with the indent provided. | `None` | | `ensure_ascii` | `bool` | If True, the output is guaranteed to have all incoming non-ASCII characters escaped. If False (the default), these characters will be output as-is. | `False` | | `include` | `_IncEx | None` | A set of fields to include, if None all fields are included. | `None` | | `exclude` | `_IncEx | None` | A set of fields to exclude, if None no fields are excluded. | `None` | | `by_alias` | `bool` | Whether to use the alias names of fields. | `True` | | `exclude_none` | `bool` | Whether to exclude fields that have a value of None. | `False` | | `round_trip` | `bool` | Whether to enable serialization and validation round-trip support. | `False` | | `timedelta_mode` | `Literal['iso8601', 'float']` | How to serialize timedelta objects, either 'iso8601' or 'float'. | `'iso8601'` | | `temporal_mode` | `Literal['iso8601', 'seconds', 'milliseconds']` | How to serialize datetime-like objects (datetime, date, time), either 'iso8601', 'seconds', or 'milliseconds'. iso8601 returns an ISO 8601 string; seconds returns the Unix timestamp in seconds as a float; milliseconds returns the Unix timestamp in milliseconds as a float. | `'iso8601'` | | `bytes_mode` | `Literal['utf8', 'base64', 'hex']` | How to serialize bytes objects, either 'utf8', 'base64', or 'hex'. | `'utf8'` | | `inf_nan_mode` | `Literal['null', 'constants', 'strings']` | How to serialize Infinity, -Infinity and NaN values, either 'null', 'constants', or 'strings'. | `'constants'` | | `serialize_unknown` | `bool` | Attempt to serialize unknown types, str(value) will be used, if that fails "\<Unserializable {value_type} object>" will be used. | `False` | | `fallback` | `Callable[[Any], Any] | None` | A function to call when an unknown value is encountered, if None a PydanticSerializationError error is raised. | `None` | | `serialize_as_any` | `bool` | Whether to serialize fields with duck-typing serialization behavior. | `False` | | `polymorphic_serialization` | `bool | None` | Whether to use model and dataclass polymorphic serialization for this call. | `None` | | `context` | `Any | None` | The context to use for serialization, this is passed to functional serializers as info.context. | `None` |

Raises:

| Type | Description | | --- | --- | | `PydanticSerializationError` | If serialization fails and no fallback function is provided. |

Returns:

| Type | Description | | --- | --- | | `bytes` | JSON bytes. |

## from_json

```python
from_json(
    data: str | bytes | bytearray,
    *,
    allow_inf_nan: bool = True,
    cache_strings: (
        bool | Literal["all", "keys", "none"]
    ) = True,
    allow_partial: (
        bool | Literal["off", "on", "trailing-strings"]
    ) = False
) -> Any

```

Deserialize JSON data to a Python object.

This is effectively a faster version of `json.loads()`, with some extra functionality.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `data` | `str | bytes | bytearray` | The JSON data to deserialize. | *required* | | `allow_inf_nan` | `bool` | Whether to allow Infinity, -Infinity and NaN values as json.loads() does by default. | `True` | | `cache_strings` | `bool | Literal['all', 'keys', 'none']` | Whether to cache strings to avoid constructing new Python objects, this should have a significant impact on performance while increasing memory usage slightly, all/True means cache all strings, keys means cache only dict keys, none/False means no caching. | `True` | | `allow_partial` | `bool | Literal['off', 'on', 'trailing-strings']` | Whether to allow partial deserialization, if True JSON data is returned if the end of the input is reached before the full object is deserialized, e.g. \["aa", "bb", "c would return ['aa', 'bb']. 'trailing-strings' means any final unfinished JSON string is included in the result. | `False` |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If deserialization fails. |

Returns:

| Type | Description | | --- | --- | | `Any` | The deserialized Python object. |

## to_jsonable_python

```python
to_jsonable_python(
    value: Any,
    *,
    include: _IncEx | None = None,
    exclude: _IncEx | None = None,
    by_alias: bool = True,
    exclude_none: bool = False,
    round_trip: bool = False,
    timedelta_mode: Literal["iso8601", "float"] = "iso8601",
    temporal_mode: Literal[
        "iso8601", "seconds", "milliseconds"
    ] = "iso8601",
    bytes_mode: Literal["utf8", "base64", "hex"] = "utf8",
    inf_nan_mode: Literal[
        "null", "constants", "strings"
    ] = "constants",
    serialize_unknown: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    serialize_as_any: bool = False,
    polymorphic_serialization: bool | None = None,
    context: Any | None = None
) -> Any

```

Serialize/marshal a Python object to a JSON-serializable Python object including transforming and filtering data.

This is effectively a standalone version of SchemaSerializer.to_python(mode='json').

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `value` | `Any` | The Python object to serialize. | *required* | | `include` | `_IncEx | None` | A set of fields to include, if None all fields are included. | `None` | | `exclude` | `_IncEx | None` | A set of fields to exclude, if None no fields are excluded. | `None` | | `by_alias` | `bool` | Whether to use the alias names of fields. | `True` | | `exclude_none` | `bool` | Whether to exclude fields that have a value of None. | `False` | | `round_trip` | `bool` | Whether to enable serialization and validation round-trip support. | `False` | | `timedelta_mode` | `Literal['iso8601', 'float']` | How to serialize timedelta objects, either 'iso8601' or 'float'. | `'iso8601'` | | `temporal_mode` | `Literal['iso8601', 'seconds', 'milliseconds']` | How to serialize datetime-like objects (datetime, date, time), either 'iso8601', 'seconds', or 'milliseconds'. iso8601 returns an ISO 8601 string; seconds returns the Unix timestamp in seconds as a float; milliseconds returns the Unix timestamp in milliseconds as a float. | `'iso8601'` | | `bytes_mode` | `Literal['utf8', 'base64', 'hex']` | How to serialize bytes objects, either 'utf8', 'base64', or 'hex'. | `'utf8'` | | `inf_nan_mode` | `Literal['null', 'constants', 'strings']` | How to serialize Infinity, -Infinity and NaN values, either 'null', 'constants', or 'strings'. | `'constants'` | | `serialize_unknown` | `bool` | Attempt to serialize unknown types, str(value) will be used, if that fails "\<Unserializable {value_type} object>" will be used. | `False` | | `fallback` | `Callable[[Any], Any] | None` | A function to call when an unknown value is encountered, if None a PydanticSerializationError error is raised. | `None` | | `serialize_as_any` | `bool` | Whether to serialize fields with duck-typing serialization behavior. | `False` | | `polymorphic_serialization` | `bool | None` | Whether to use model and dataclass polymorphic serialization for this call. | `None` | | `context` | `Any | None` | The context to use for serialization, this is passed to functional serializers as info.context. | `None` |

Raises:

| Type | Description | | --- | --- | | `PydanticSerializationError` | If serialization fails and no fallback function is provided. |

Returns:

| Type | Description | | --- | --- | | `Any` | The serialized Python object. |
