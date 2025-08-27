This module contains related classes and functions for validation.

## ModelAfterValidatorWithoutInfo

```python
ModelAfterValidatorWithoutInfo = Callable[
    [_ModelType], _ModelType
]

```

A `@model_validator` decorated function signature. This is used when `mode='after'` and the function does not have info argument.

## ModelAfterValidator

```python
ModelAfterValidator = Callable[
    [_ModelType, ValidationInfo[Any]], _ModelType
]

```

A `@model_validator` decorated function signature. This is used when `mode='after'`.

## AfterValidator

```python
AfterValidator(
    func: (
        NoInfoValidatorFunction | WithInfoValidatorFunction
    ),
)

```

Usage Documentation

[field *after* validators](../../concepts/validators/#field-after-validator)

A metadata class that indicates that a validation should be applied **after** the inner validation logic.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `func` | `NoInfoValidatorFunction | WithInfoValidatorFunction` | The validator function. |

Example

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ValidationError

MyInt = Annotated[int, AfterValidator(lambda v: v + 1)]

class Model(BaseModel):
    a: MyInt

print(Model(a=1).a)
#> 2

try:
    Model(a='a')
except ValidationError as e:
    print(e.json(indent=2))
    '''
    [
      {
        "type": "int_parsing",
        "loc": [
          "a"
        ],
        "msg": "Input should be a valid integer, unable to parse string as an integer",
        "input": "a",
        "url": "https://errors.pydantic.dev/2/v/int_parsing"
      }
    ]
    '''

```

## BeforeValidator

```python
BeforeValidator(
    func: (
        NoInfoValidatorFunction | WithInfoValidatorFunction
    ),
    json_schema_input_type: Any = PydanticUndefined,
)

```

Usage Documentation

[field *before* validators](../../concepts/validators/#field-before-validator)

A metadata class that indicates that a validation should be applied **before** the inner validation logic.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `func` | `NoInfoValidatorFunction | WithInfoValidatorFunction` | The validator function. | | `json_schema_input_type` | `Any` | The input type used to generate the appropriate JSON Schema (in validation mode). The actual input type is Any. |

Example

```python
from typing import Annotated

from pydantic import BaseModel, BeforeValidator

MyInt = Annotated[int, BeforeValidator(lambda v: v + 1)]

class Model(BaseModel):
    a: MyInt

print(Model(a=1).a)
#> 2

try:
    Model(a='a')
except TypeError as e:
    print(e)
    #> can only concatenate str (not "int") to str

```

## PlainValidator

```python
PlainValidator(
    func: (
        NoInfoValidatorFunction | WithInfoValidatorFunction
    ),
    json_schema_input_type: Any = Any,
)

```

Usage Documentation

[field *plain* validators](../../concepts/validators/#field-plain-validator)

A metadata class that indicates that a validation should be applied **instead** of the inner validation logic.

Note

Before v2.9, `PlainValidator` wasn't always compatible with JSON Schema generation for `mode='validation'`. You can now use the `json_schema_input_type` argument to specify the input type of the function to be used in the JSON schema when `mode='validation'` (the default). See the example below for more details.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `func` | `NoInfoValidatorFunction | WithInfoValidatorFunction` | The validator function. | | `json_schema_input_type` | `Any` | The input type used to generate the appropriate JSON Schema (in validation mode). The actual input type is Any. |

Example

```python
from typing import Annotated, Union

from pydantic import BaseModel, PlainValidator

def validate(v: object) -> int:
    if not isinstance(v, (int, str)):
        raise ValueError(f'Expected int or str, go {type(v)}')

    return int(v) + 1

MyInt = Annotated[
    int,
    PlainValidator(validate, json_schema_input_type=Union[str, int]),  # (1)!
]

class Model(BaseModel):
    a: MyInt

print(Model(a='1').a)
#> 2

print(Model(a=1).a)
#> 2

```

1. In this example, we've specified the `json_schema_input_type` as `Union[str, int]` which indicates to the JSON schema generator that in validation mode, the input type for the `a` field can be either a str or an int.

## WrapValidator

```python
WrapValidator(
    func: (
        NoInfoWrapValidatorFunction
        | WithInfoWrapValidatorFunction
    ),
    json_schema_input_type: Any = PydanticUndefined,
)

```

Usage Documentation

[field *wrap* validators](../../concepts/validators/#field-wrap-validator)

A metadata class that indicates that a validation should be applied **around** the inner validation logic.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `func` | `NoInfoWrapValidatorFunction | WithInfoWrapValidatorFunction` | The validator function. | | `json_schema_input_type` | `Any` | The input type used to generate the appropriate JSON Schema (in validation mode). The actual input type is Any. |

```python
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ValidationError, WrapValidator

def validate_timestamp(v, handler):
    if v == 'now':
        # we don't want to bother with further validation, just return the new value
        return datetime.now()
    try:
        return handler(v)
    except ValidationError:
        # validation failed, in this case we want to return a default value
        return datetime(2000, 1, 1)

MyTimestamp = Annotated[datetime, WrapValidator(validate_timestamp)]

class Model(BaseModel):
    a: MyTimestamp

print(Model(a='now').a)
#> 2032-01-02 03:04:05.000006
print(Model(a='invalid').a)
#> 2000-01-01 00:00:00

```

## ModelWrapValidatorHandler

Bases: `ValidatorFunctionWrapHandler`, `Protocol[_ModelTypeCo]`

`@model_validator` decorated function handler argument type. This is used when `mode='wrap'`.

## ModelWrapValidatorWithoutInfo

Bases: `Protocol[_ModelType]`

A `@model_validator` decorated function signature. This is used when `mode='wrap'` and the function does not have info argument.

## ModelWrapValidator

Bases: `Protocol[_ModelType]`

A `@model_validator` decorated function signature. This is used when `mode='wrap'`.

## FreeModelBeforeValidatorWithoutInfo

Bases: `Protocol`

A `@model_validator` decorated function signature. This is used when `mode='before'` and the function does not have info argument.

## ModelBeforeValidatorWithoutInfo

Bases: `Protocol`

A `@model_validator` decorated function signature. This is used when `mode='before'` and the function does not have info argument.

## FreeModelBeforeValidator

Bases: `Protocol`

A `@model_validator` decorated function signature. This is used when `mode='before'`.

## ModelBeforeValidator

Bases: `Protocol`

A `@model_validator` decorated function signature. This is used when `mode='before'`.

## InstanceOf

```python
InstanceOf()

```

Generic type for annotating a type that is an instance of a given class.

Example

```python
from pydantic import BaseModel, InstanceOf

class Foo:
    ...

class Bar(BaseModel):
    foo: InstanceOf[Foo]

Bar(foo=Foo())
try:
    Bar(foo=42)
except ValidationError as e:
    print(e)
    """
    [
    │   {
    │   │   'type': 'is_instance_of',
    │   │   'loc': ('foo',),
    │   │   'msg': 'Input should be an instance of Foo',
    │   │   'input': 42,
    │   │   'ctx': {'class': 'Foo'},
    │   │   'url': 'https://errors.pydantic.dev/0.38.0/v/is_instance_of'
    │   }
    ]
    """

```

## SkipValidation

```python
SkipValidation()

```

If this is applied as an annotation (e.g., via `x: Annotated[int, SkipValidation]`), validation will be skipped. You can also use `SkipValidation[int]` as a shorthand for `Annotated[int, SkipValidation]`.

This can be useful if you want to use a type annotation for documentation/IDE/type-checking purposes, and know that it is safe to skip validation for one or more of the fields.

Because this converts the validation schema to `any_schema`, subsequent annotation-applied transformations may not have the expected effects. Therefore, when used, this annotation should generally be the final annotation applied to a type.

## ValidateAs

```python
ValidateAs(
    from_type: type[_FromTypeT],
    /,
    instantiation_hook: Callable[[_FromTypeT], Any],
)

```

A helper class to validate a custom type from a type that is natively supported by Pydantic.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `from_type` | `type[_FromTypeT]` | The type natively supported by Pydantic to use to perform validation. | *required* | | `instantiation_hook` | `Callable[[_FromTypeT], Any]` | A callable taking the validated type as an argument, and returning the populated custom type. | *required* |

Example

```python
from typing import Annotated

from pydantic import BaseModel, TypeAdapter, ValidateAs

class MyCls:
    def __init__(self, a: int) -> None:
        self.a = a

    def __repr__(self) -> str:
        return f"MyCls(a={self.a})"

class Model(BaseModel):
    a: int


ta = TypeAdapter(
    Annotated[MyCls, ValidateAs(Model, lambda v: MyCls(a=v.a))]
)

print(ta.validate_python({'a': 1}))
#> MyCls(a=1)

```

Source code in `pydantic/functional_validators.py`

```python
def __init__(self, from_type: type[_FromTypeT], /, instantiation_hook: Callable[[_FromTypeT], Any]) -> None:
    self.from_type = from_type
    self.instantiation_hook = instantiation_hook

```

## field_validator

```python
field_validator(
    field: str,
    /,
    *fields: str,
    mode: Literal["wrap"],
    check_fields: bool | None = ...,
    json_schema_input_type: Any = ...,
) -> Callable[[_V2WrapValidatorType], _V2WrapValidatorType]

```

```python
field_validator(
    field: str,
    /,
    *fields: str,
    mode: Literal["before", "plain"],
    check_fields: bool | None = ...,
    json_schema_input_type: Any = ...,
) -> Callable[
    [_V2BeforeAfterOrPlainValidatorType],
    _V2BeforeAfterOrPlainValidatorType,
]

```

```python
field_validator(
    field: str,
    /,
    *fields: str,
    mode: Literal["after"] = ...,
    check_fields: bool | None = ...,
) -> Callable[
    [_V2BeforeAfterOrPlainValidatorType],
    _V2BeforeAfterOrPlainValidatorType,
]

```

```python
field_validator(
    field: str,
    /,
    *fields: str,
    mode: FieldValidatorModes = "after",
    check_fields: bool | None = None,
    json_schema_input_type: Any = PydanticUndefined,
) -> Callable[[Any], Any]

```

Usage Documentation

[field validators](../../concepts/validators/#field-validators)

Decorate methods on the class indicating that they should be used to validate fields.

Example usage:

```python
from typing import Any

from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
)

class Model(BaseModel):
    a: str

    @field_validator('a')
    @classmethod
    def ensure_foobar(cls, v: Any):
        if 'foobar' not in v:
            raise ValueError('"foobar" not found in a')
        return v

print(repr(Model(a='this is foobar good')))
#> Model(a='this is foobar good')

try:
    Model(a='snap')
except ValidationError as exc_info:
    print(exc_info)
    '''
    1 validation error for Model
    a
      Value error, "foobar" not found in a [type=value_error, input_value='snap', input_type=str]
    '''

```

For more in depth examples, see [Field Validators](../../concepts/validators/#field-validators).

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `str` | The first field the field_validator should be called on; this is separate from fields to ensure an error is raised if you don't pass at least one. | *required* | | `*fields` | `str` | Additional field(s) the field_validator should be called on. | `()` | | `mode` | `FieldValidatorModes` | Specifies whether to validate the fields before or after validation. | `'after'` | | `check_fields` | `bool | None` | Whether to check that the fields actually exist on the model. | `None` | | `json_schema_input_type` | `Any` | The input type of the function. This is only used to generate the appropriate JSON Schema (in validation mode) and can only specified when mode is either 'before', 'plain' or 'wrap'. | `PydanticUndefined` |

Returns:

| Type | Description | | --- | --- | | `Callable[[Any], Any]` | A decorator that can be used to decorate a function to be used as a field_validator. |

Raises:

| Type | Description | | --- | --- | | `PydanticUserError` | If @field_validator is used bare (with no fields). If the args passed to @field_validator as fields are not strings. If @field_validator applied to instance methods. |

Source code in `pydantic/functional_validators.py`

````python
def field_validator(
    field: str,
    /,
    *fields: str,
    mode: FieldValidatorModes = 'after',
    check_fields: bool | None = None,
    json_schema_input_type: Any = PydanticUndefined,
) -> Callable[[Any], Any]:
    """!!! abstract "Usage Documentation"
        [field validators](../concepts/validators.md#field-validators)

    Decorate methods on the class indicating that they should be used to validate fields.

    Example usage:
    ```python
    from typing import Any

    from pydantic import (
        BaseModel,
        ValidationError,
        field_validator,
    )

    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def ensure_foobar(cls, v: Any):
            if 'foobar' not in v:
                raise ValueError('"foobar" not found in a')
            return v

    print(repr(Model(a='this is foobar good')))
    #> Model(a='this is foobar good')

    try:
        Model(a='snap')
    except ValidationError as exc_info:
        print(exc_info)
        '''
        1 validation error for Model
        a
          Value error, "foobar" not found in a [type=value_error, input_value='snap', input_type=str]
        '''
    ```

    For more in depth examples, see [Field Validators](../concepts/validators.md#field-validators).

    Args:
        field: The first field the `field_validator` should be called on; this is separate
            from `fields` to ensure an error is raised if you don't pass at least one.
        *fields: Additional field(s) the `field_validator` should be called on.
        mode: Specifies whether to validate the fields before or after validation.
        check_fields: Whether to check that the fields actually exist on the model.
        json_schema_input_type: The input type of the function. This is only used to generate
            the appropriate JSON Schema (in validation mode) and can only specified
            when `mode` is either `'before'`, `'plain'` or `'wrap'`.

    Returns:
        A decorator that can be used to decorate a function to be used as a field_validator.

    Raises:
        PydanticUserError:
            - If `@field_validator` is used bare (with no fields).
            - If the args passed to `@field_validator` as fields are not strings.
            - If `@field_validator` applied to instance methods.
    """
    if isinstance(field, FunctionType):
        raise PydanticUserError(
            '`@field_validator` should be used with fields and keyword arguments, not bare. '
            "E.g. usage should be `@validator('<field_name>', ...)`",
            code='validator-no-fields',
        )

    if mode not in ('before', 'plain', 'wrap') and json_schema_input_type is not PydanticUndefined:
        raise PydanticUserError(
            f"`json_schema_input_type` can't be used when mode is set to {mode!r}",
            code='validator-input-type',
        )

    if json_schema_input_type is PydanticUndefined and mode == 'plain':
        json_schema_input_type = Any

    fields = field, *fields
    if not all(isinstance(field, str) for field in fields):
        raise PydanticUserError(
            '`@field_validator` fields should be passed as separate string args. '
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`",
            code='validator-invalid-fields',
        )

    def dec(
        f: Callable[..., Any] | staticmethod[Any, Any] | classmethod[Any, Any, Any],
    ) -> _decorators.PydanticDescriptorProxy[Any]:
        if _decorators.is_instance_method_from_sig(f):
            raise PydanticUserError(
                '`@field_validator` cannot be applied to instance methods', code='validator-instance-method'
            )

        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)

        dec_info = _decorators.FieldValidatorDecoratorInfo(
            fields=fields, mode=mode, check_fields=check_fields, json_schema_input_type=json_schema_input_type
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec

````

## model_validator

```python
model_validator(*, mode: Literal["wrap"]) -> Callable[
    [_AnyModelWrapValidator[_ModelType]],
    PydanticDescriptorProxy[ModelValidatorDecoratorInfo],
]

```

```python
model_validator(*, mode: Literal["before"]) -> Callable[
    [_AnyModelBeforeValidator],
    PydanticDescriptorProxy[ModelValidatorDecoratorInfo],
]

```

```python
model_validator(*, mode: Literal["after"]) -> Callable[
    [_AnyModelAfterValidator[_ModelType]],
    PydanticDescriptorProxy[ModelValidatorDecoratorInfo],
]

```

```python
model_validator(
    *, mode: Literal["wrap", "before", "after"]
) -> Any

```

Usage Documentation

[Model Validators](../../concepts/validators/#model-validators)

Decorate model methods for validation purposes.

Example usage:

```python
from typing_extensions import Self

from pydantic import BaseModel, ValidationError, model_validator

class Square(BaseModel):
    width: float
    height: float

    @model_validator(mode='after')
    def verify_square(self) -> Self:
        if self.width != self.height:
            raise ValueError('width and height do not match')
        return self

s = Square(width=1, height=1)
print(repr(s))
#> Square(width=1.0, height=1.0)

try:
    Square(width=1, height=2)
except ValidationError as e:
    print(e)
    '''
    1 validation error for Square
      Value error, width and height do not match [type=value_error, input_value={'width': 1, 'height': 2}, input_type=dict]
    '''

```

For more in depth examples, see [Model Validators](../../concepts/validators/#model-validators).

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `mode` | `Literal['wrap', 'before', 'after']` | A required string literal that specifies the validation mode. It can be one of the following: 'wrap', 'before', or 'after'. | *required* |

Returns:

| Type | Description | | --- | --- | | `Any` | A decorator that can be used to decorate a function to be used as a model validator. |

Source code in `pydantic/functional_validators.py`

````python
def model_validator(
    *,
    mode: Literal['wrap', 'before', 'after'],
) -> Any:
    """!!! abstract "Usage Documentation"
        [Model Validators](../concepts/validators.md#model-validators)

    Decorate model methods for validation purposes.

    Example usage:
    ```python
    from typing_extensions import Self

    from pydantic import BaseModel, ValidationError, model_validator

    class Square(BaseModel):
        width: float
        height: float

        @model_validator(mode='after')
        def verify_square(self) -> Self:
            if self.width != self.height:
                raise ValueError('width and height do not match')
            return self

    s = Square(width=1, height=1)
    print(repr(s))
    #> Square(width=1.0, height=1.0)

    try:
        Square(width=1, height=2)
    except ValidationError as e:
        print(e)
        '''
        1 validation error for Square
          Value error, width and height do not match [type=value_error, input_value={'width': 1, 'height': 2}, input_type=dict]
        '''
    ```

    For more in depth examples, see [Model Validators](../concepts/validators.md#model-validators).

    Args:
        mode: A required string literal that specifies the validation mode.
            It can be one of the following: 'wrap', 'before', or 'after'.

    Returns:
        A decorator that can be used to decorate a function to be used as a model validator.
    """

    def dec(f: Any) -> _decorators.PydanticDescriptorProxy[Any]:
        # auto apply the @classmethod decorator (except for *after* validators, which should be instance methods):
        if mode != 'after':
            f = _decorators.ensure_classmethod_based_on_signature(f)
        dec_info = _decorators.ModelValidatorDecoratorInfo(mode=mode)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec

````
