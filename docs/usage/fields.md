
The `Field` class is used to define fields in models.

TODO: Refactor the `Field customization` section in the `json_schema.md`.

## Alias fields

For validation and serialization, you can define an alias for a field.

There are three ways to define an alias:

* `Field(..., alias='foo')`
* `Field(..., validation_alias='foo')`
* `Field(..., serialization_alias='foo')`

The `alias` parameter is used for both _validation_ and _serialization_. The `validation_alias` and `serialization_alias`
parameters are used for _validation_ and _serialization_ respectively.

```py test="skip"
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}  (3)
```

1. The `username` is used for validation.
2. We are using `model_dump` to serialize the model.

    Check more about [`model_dump`](/api/main/#pydantic.main.BaseModel.model_dump) in the API reference.

3. The `username` is used for serialization.

If you only want to define an alias for _validation_, you can use the `validation_alias` parameter:

```py test="skip"
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., validation_alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))
#> {'name': 'johndoe'}  (2)
```

1. The `username` is used for validation.
2. The `name` is used for serialization.

If you only want to define an alias for _serialization_, you can use the `serialization_alias` parameter:

```py test="skip"
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., serialization_alias='username')


user = User(name='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))
#> {'username': 'johndoe'}  (2)
```

1. The `name` is used for validation.
2. The `username` is used for serialization.

In case you use `alias` and `validation_alias` or `serialization_alias` at the same time, the `validation_alias`
will have priority over `alias` for _validation_, and `serialization_alias` will have priority over `alias` for
_serialization_.

You can read more about [Alias Precedence](/usage/model_config/#alias-precedence) in the [Model Config](/usage/model_config/) section.
