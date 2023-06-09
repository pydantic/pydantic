
The `Field` class is used to define fields in models.

TODO: Refactor the `Field customization` section in the `json_schema.md`.

## Alias fields

For validation and serialization, you can define an alias for a field.

There are three ways to define an alias:

* `Field(..., alias='foo')`
* `Field(..., validation_alias='foo')`
* `Field(..., serialization_alias='foo')`

The `alias` parameter is used for both validation _and_ serialization. If you want to use
_different_ aliases for validation and serialization respectively, you can use the`validation_alias`
and `serialization_alias` parameters, which will apply only in their respective use cases.

??? tip "VSCode users"
    On VSCode, if you use the [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
    extension, you'll not see a warning when instantiating a model with an alias field.

    ```py
    from pydantic import BaseModel, Field


    class User(BaseModel):
        name: str = Field(..., alias='username')


    user = User(username='johndoe')  # (1)!
    ```

    1. VSCode will NOT show a warning here.

    If you set `populate_by_name` to `True` in the [Model Config](/usage/model_config/#populate-by-name),
    VSCode will show a warning when instantiating a model with the `name` argument.

    ```py test="skip" lint="skip"
    class User(BaseModel):
        model_config = ConfigDict(populate_by_alias=True)

        name: str = Field(..., alias='username')


    user = User(name='johndoe')  # (1)!
    ```

    1. VSCode will show a warning here.

    To "trick" VSCode, you can use the `str` function to instantiate the model:

    ```py test="skip" lint="skip"
    class User(BaseModel):
        model_config = ConfigDict(populate_by_alias=True)

        name: str = Field(..., alias=str('username'))
    ```

    You can read more about it on [this issue](https://github.com/pydantic/pydantic/issues/5893).

    ### Validation Alias

    You shouldn't expect VSCode to use the `validation_alias` in the same way as it happens with `alias`.
    If you want to achieve the same behavior, you can replace:

    ```py test="skip" lint="skip"
    Field(validation_alias='myValidationAlias')
    ```
    By:
    ```py test="skip" lint="skip"
    Field(..., alias='myValidationAlias', serialization_alias='mySerializationAlias')
    ```

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
