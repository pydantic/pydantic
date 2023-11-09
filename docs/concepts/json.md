!!! warning "🚧 Work in Progress"
    This page is a work in progress.

# JSON Parsing

Pydantic provides builtin JSON parsing, which helps achieve:

* Significant performance improvements without the cost of using a 3rd party library
* Support for custom errors
* Support for `strict` specifications

Here's an example of Pydantic's builtin JSON parsing, showcasing the support for `strict` specifications:

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Dog(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int


print(repr(Dog.model_validate_json('{"name": "Buddy", "age": 1}')))
#> Dog(name='Buddy', age=1)

try:
    print(Dog.model_validate_json('{"name": "Buddy", "age": "1"}'))  # (1)!
except ValidationError as e:
    print(e)
    """
    1 validation error for Dog
    age
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

1. The input for the `age` field is a string, but the `age` field has type `int`.
   This results in a validation error when `strict` mode is enabled.

In v2.5.0 and above, Pydantic uses [`jiter`](https://docs.rs/jiter/latest/jiter/),
a fast and iterable JSON parser, to parse JSON data. Using `jiter` compared to `serde` results in modest performance
improvements that will get even better in the future.

The `jiter` JSON parser is almost entirely compatible with the `serde` JSON parser,
with one noticeable enhancement being that `jiter` supports deserialization of `inf` and `NaN` values.
In the future, `jiter` is intended to enable support validation errors to include the location
in the original JSON input which contained the invalid value.
