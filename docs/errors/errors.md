
Pydantic will raise a [`ValidationError`][pydantic_core.ValidationError] whenever it finds an error in the data it's validating.

!!! note
    Validation code should not raise `ValidationError` itself, but rather raise a `ValueError` or
    `AssertionError` (or subclass thereof) which will be caught and used to populate
    `ValidationError`.

One exception will be raised regardless of the number of errors found, that `ValidationError` will
contain information about all the errors and how they happened.

You can access these errors in several ways:

| Method            | Description                                            |
|-------------------|--------------------------------------------------------|
| `e.errors()`      | Returns a list of errors found in the input data.      |
| `e.error_count()` | Returns the number of errors found in `errors`.        |
| `e.json()`        | Returns a JSON representation of `errors`.             |
| `str(e)`          | Returns a human-readable representation of the errors. |

Each error object contains:

| Property | Description                                                                    |
|----------|--------------------------------------------------------------------------------|
| `ctx`    | An optional object which contains values required to render the error message. |
| `input`  | The input provided for validation.                                             |
| `loc`    | The error's location as a list.                                                |
| `msg`    | A human-readable explanation of the error.                                     |
| `type`   | A computer-readable identifier of the error type.                              |
| `url`    | The URL to further information about the error.                                |

The first item in the `loc` list will be the field where the error occurred, and if the field is a
[sub-model](../concepts/models.md#nested-models), subsequent items will be present to indicate the nested location of the error.

As a demonstration:

```python
from typing import List

from pydantic import BaseModel, ValidationError, conint


class Location(BaseModel):
    lat: float = 0.1
    lng: float = 10.1


class Model(BaseModel):
    is_required: float
    gt_int: conint(gt=42)
    list_of_ints: List[int] = None
    a_float: float = None
    recursive_model: Location = None


data = dict(
    list_of_ints=['1', 2, 'bad'],
    a_float='not a float',
    recursive_model={'lat': 4.2, 'lng': 'New York'},
    gt_int=21,
)

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
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='not a float', input_type=str]
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
                'a_float': 'not a float',
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
            'type': 'float_parsing',
            'loc': ('a_float',),
            'msg': 'Input should be a valid number, unable to parse string as a number',
            'input': 'not a float',
            'url': 'https://errors.pydantic.dev/2/v/float_parsing',
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

### Custom Errors

In your custom data types or validators you should use `ValueError` or `AssertionError` to raise errors.

See [validators](../concepts/validators.md) for more details on use of the `@validator` decorator.

```python
from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    foo: str

    @field_validator('foo')
    def value_must_equal_bar(cls, v):
        if v != 'bar':
            raise ValueError('value must be "bar"')

        return v


try:
    Model(foo='ber')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    foo
      Value error, value must be "bar" [type=value_error, input_value='ber', input_type=str]
    """
    print(e.errors())
    """
    [
        {
            'type': 'value_error',
            'loc': ('foo',),
            'msg': 'Value error, value must be "bar"',
            'input': 'ber',
            'ctx': {'error': ValueError('value must be "bar"')},
            'url': 'https://errors.pydantic.dev/2/v/value_error',
        }
    ]
    """
```

You can also use [`PydanticCustomError`][pydantic_core.PydanticCustomError], to fully control the error structure:

```python
from pydantic_core import PydanticCustomError

from pydantic import BaseModel, ValidationError, field_validator


class Model(BaseModel):
    foo: str

    @field_validator('foo')
    def value_must_equal_bar(cls, v):
        if v != 'bar':
            raise PydanticCustomError(
                'not_a_bar',
                'value is not "bar", got "{wrong_value}"',
                dict(wrong_value=v),
            )
        return v


try:
    Model(foo='ber')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    foo
      value is not "bar", got "ber" [type=not_a_bar, input_value='ber', input_type=str]
    """
```

## Error messages

Pydantic attempts to provide useful default error messages for validation and usage errors.

We've provided documentation for default error codes in the following sections:

- [Validation Errors](validation_errors.md)
- [Usage Errors](usage_errors.md)

### Customize error messages

You can customize error messages by creating a custom error handler.

```python
from typing import Dict, List

from pydantic_core import ErrorDetails

from pydantic import BaseModel, HttpUrl, ValidationError

CUSTOM_MESSAGES = {
    'int_parsing': 'This is not an integer! 🤦',
    'url_scheme': 'Hey, use the right URL scheme! I wanted {expected_schemes}.',
}


def convert_errors(
    e: ValidationError, custom_messages: Dict[str, str]
) -> List[ErrorDetails]:
    new_errors: List[ErrorDetails] = []
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
from typing import Any, Dict, List, Tuple, Union

from pydantic import BaseModel, ValidationError


def loc_to_dot_sep(loc: Tuple[Union[str, int], ...]) -> str:
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


def convert_errors(e: ValidationError) -> List[Dict[str, Any]]:
    new_errors: List[Dict[str, Any]] = e.errors()
    for error in new_errors:
        error['loc'] = loc_to_dot_sep(error['loc'])
    return new_errors


class TestNestedModel(BaseModel):
    key: str
    value: str


class TestModel(BaseModel):
    items: List[TestNestedModel]


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

1. By default, `e.errors()` produces a List of errors with `loc` values that take the form of tuples.
2. With our custom `loc_to_dot_sep` function, we've modified the form of the `loc` representation.
