There are some situations where you want Pydantic to throw an error instead of coercing data.
For example, input to an `int` field could be `123` or the string `"123"`, which would be converted to `123`.
While this is useful in many scenarios (think: UUIDs, URL parameters, environment variables, user input),
there are some situations where it's not desirable.

The [Conversion Table](conversion_table.md) provides more details on how Pydantic converts data in both strict and
lax modes.

## Strict mode for fields

For individual fields on a model, you can [set `strict=True` on the field](../api/fields.md#pydantic.fields.Field).
Only the fields for which `strict=True` is set will be affected.

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str = Field(strict=True)
    age: int = Field(strict=False)


user = User(name='John', age='42')
print(user)
#> name='John' age=42


class AnotherUser(BaseModel):
    name: str = Field(strict=True)
    age: int = Field(strict=True)


try:
    anotheruser = AnotherUser(name='John', age='42')
except ValidationError as e:
    print(e)
    """
    1 validation error for AnotherUser
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

## Strict mode for models

For all fields on a model, you can
[set `model_config = ConfigDict(strict=True)`](../api/config.md#pydantic.config.ConfigDict) in the config for the model.
When set, all fields on the model will be validated in strict mode.

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class User(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int


try:
    user = User(name='John', age='42')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

!!! note
    Note that, when using `strict=True` in config on a model, you can still override the strictness
    of individual fields by setting `strict=False` on individual fields.

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(strict=True)

        name: str
        age: int = Field(strict=False)
    ```
