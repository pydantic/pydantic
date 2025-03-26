
Pydantic will raise a [`ValidationError`][pydantic_core.ValidationError] whenever it finds an error in the data it's validating.

!!! note
    Validation code should not raise the [`ValidationError`][pydantic_core.ValidationError] itself,
    but rather raise a [`ValueError`][] or a [`AssertionError`][] (or subclass thereof) which will
    be caught and used to populate the final [`ValidationError`][pydantic_core.ValidationError].

    For more details, refer to the [dedicated section](../concepts/validators.md#raising-validation-errors)
    of the validators documentation.

That [`ValidationError`][pydantic_core.ValidationError] will contain information about all the errors and how they happened.

You can access these errors in several ways:

| Method                                                       | Description                                                                                    |
|--------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| [`errors()`][pydantic_core.ValidationError.errors]           | Returns a list of [`ErrorDetails`][pydantic_core.ErrorDetails] errors found in the input data. |
| [`error_count()`][pydantic_core.ValidationError.error_count] | Returns the number of errors.                                                                  |
| [`json()`][pydantic_core.ValidationError.json]               | Returns a JSON representation of the list errors.                                              |
| `str(e)`                                                     | Returns a human-readable representation of the errors.                                         |

The [`ErrorDetails`][pydantic_core.ErrorDetails] object is a dictionary. It contains the following:

| Property                                    | Description                                                                    |
|---------------------------------------------|--------------------------------------------------------------------------------|
| [`ctx`][pydantic_core.ErrorDetails.ctx]     | An optional object which contains values required to render the error message. |
| [`input`][pydantic_core.ErrorDetails.input] | The input provided for validation.                                             |
| [`loc`][pydantic_core.ErrorDetails.loc]     | The error's location as a list.                                                |
| [`msg`][pydantic_core.ErrorDetails.msg]     | A human-readable explanation of the error.                                     |
| [`type`][pydantic_core.ErrorDetails.type]   | A computer-readable identifier of the error type.                              |
| [`url`][pydantic_core.ErrorDetails.url]     | The documentation URL giving information about the error.                      |

The first item in the [`loc`][pydantic_core.ErrorDetails.loc] list will be the field where the error occurred, and if the field is a
[sub-model](../concepts/models.md#nested-models), subsequent items will be present to indicate the nested location of the error.

As a demonstration:

```python
from pydantic import BaseModel, Field, ValidationError, field_validator


class Location(BaseModel):
    lat: float = 0.1
    lng: float = 10.1


class Model(BaseModel):
    is_required: float
    gt_int: int = Field(gt=42)
    list_of_ints: list[int]
    a_float: float
    recursive_model: Location

    @field_validator('a_float', mode='after')
    @classmethod
    def validate_float(cls, value: float) -> float:
        if value > 2.0:
            raise ValueError('Invalid float value')
        return value


data = {
    'list_of_ints': ['1', 2, 'bad'],
    'a_float': 3.0,
    'recursive_model': {'lat': 4.2, 'lng': 'New York'},
    'gt_int': 21,
}

try:
    Model(**data)
except ValidationError as e:
    print(e)
    """
    5 validation errors for Model
    is_required
      Field required [type=missing, input_value={'list_of_ints': ['1', 2,...ew York'}, 'gt_int': 21}, input_type=dict]
    gt_int
      Input should be greater than 42 [type=greater_than, input_value=21, input_type=int]
    list_of_ints.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='bad', input_type=str]
    a_float
      Value error, Invalid float value [type=value_error, input_value=3.0, input_type=float]
    recursive_model.lng
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='New York', input_type=str]
    """

try:
    Model(**data)
except ValidationError as e:
    print(e.errors())
    """
    [
        {
            'type': 'missing',
            'loc': ('is_required',),
            'msg': 'Field required',
            'input': {
                'list_of_ints': ['1', 2, 'bad'],
                'a_float': 3.0,
                'recursive_model': {'lat': 4.2, 'lng': 'New York'},
                'gt_int': 21,
            },
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
        {
            'type': 'greater_than',
            'loc': ('gt_int',),
            'msg': 'Input should be greater than 42',
            'input': 21,
            'ctx': {'gt': 42},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        },
        {
            'type': 'int_parsing',
            'loc': ('list_of_ints', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'bad',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'value_error',
            'loc': ('a_float',),
            'msg': 'Value error, Invalid float value',
            'input': 3.0,
            'ctx': {'error': ValueError('Invalid float value')},
            'url': 'https://errors.pydantic.dev/2/v/value_error',
        },
        {
            'type': 'float_parsing',
            'loc': ('recursive_model', 'lng'),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'New York',
            'url': 'https://errors.pydantic.dev/2/v/float_parsing',
        },
    ]
    """
```

## Error messages

Pydantic attempts to provide useful default error messages for validation and usage errors, which can be found here:

* [Validation Errors](validation_errors.md): Errors that happen during data validation.
* [Usage Errors](usage_errors.md): Errors that happen when using Pydantic.

### Customize error messages

You can customize error messages by creating a custom error handler.

```python
from pydantic_core import ErrorDetails

from pydantic import BaseModel, HttpUrl, ValidationError

CUSTOM_MESSAGES = {
    'int_parsing': 'This is not an integer! 🤦',
    'url_scheme': 'Hey, use the right URL scheme! I wanted {expected_schemes}.',
}


def convert_errors(
    e: ValidationError, custom_messages: dict[str, str]
) -> list[ErrorDetails]:
    new_errors: list[ErrorDetails] = []
    for error in e.errors():
        custom_message = custom_messages.get(error['type'])
        if custom_message:
            ctx = error.get('ctx')
            error['msg'] = (
                custom_message.format(**ctx) if ctx else custom_message
            )
        new_errors.append(error)
    return new_errors


class Model(BaseModel):
    a: int
    b: HttpUrl


try:
    Model(a='wrong', b='ftp://example.com')
except ValidationError as e:
    errors = convert_errors(e, CUSTOM_MESSAGES)
    print(errors)
    """
    [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'This is not an integer! 🤦',
            'input': 'wrong',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'url_scheme',
            'loc': ('b',),
            'msg': "Hey, use the right URL scheme! I wanted 'http' or 'https'.",
            'input': 'ftp://example.com',
            'ctx': {'expected_schemes': "'http' or 'https'"},
            'url': 'https://errors.pydantic.dev/2/v/url_scheme',
        },
    ]
    """
```

A common use case would be to translate error messages. For example, in the above example,
we could translate the error messages replacing the `CUSTOM_MESSAGES` dictionary with a
dictionary of translations.

Another example is customizing the way that the `'loc'` value of an error is represented.

```python
from typing import Any, Union

from pydantic import BaseModel, ValidationError


def loc_to_dot_sep(loc: tuple[Union[str, int], ...]) -> str:
    path = ''
    for i, x in enumerate(loc):
        if isinstance(x, str):
            if i > 0:
                path += '.'
            path += x
        elif isinstance(x, int):
            path += f'[{x}]'
        else:
            raise TypeError('Unexpected type')
    return path


def convert_errors(e: ValidationError) -> list[dict[str, Any]]:
    new_errors: list[dict[str, Any]] = e.errors()
    for error in new_errors:
        error['loc'] = loc_to_dot_sep(error['loc'])
    return new_errors


class TestNestedModel(BaseModel):
    key: str
    value: str


class TestModel(BaseModel):
    items: list[TestNestedModel]


data = {'items': [{'key': 'foo', 'value': 'bar'}, {'key': 'baz'}]}

try:
    TestModel.model_validate(data)
except ValidationError as e:
    print(e.errors())  # (1)!
    """
    [
        {
            'type': 'missing',
            'loc': ('items', 1, 'value'),
            'msg': 'Field required',
            'input': {'key': 'baz'},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        }
    ]
    """
    pretty_errors = convert_errors(e)
    print(pretty_errors)  # (2)!
    """
    [
        {
            'type': 'missing',
            'loc': 'items[1].value',
            'msg': 'Field required',
            'input': {'key': 'baz'},
            'url': 'https://errors.pydantic.dev/2/v/missing',
        }
    ]
    """
```

1. By default, `e.errors()` produces a list of errors with `loc` values that take the form of tuples.
2. With our custom `loc_to_dot_sep` function, we've modified the form of the `loc` representation.
