
The `Field` class is used to define fields in models.

TODO: Refactor the `Field customization` section from the `json_schema.md`.

## Field aliases

For validation and serialization, you can define an alias for a field.

There are three ways to define an alias:

* `Field(..., alias='foo')`
* `Field(..., validation_alias='foo')`
* `Field(..., serialization_alias='foo')`

The `alias` parameter is used for both validation _and_ serialization. If you want to use
_different_ aliases for validation and serialization respectively, you can use the`validation_alias`
and `serialization_alias` parameters, which will apply only in their respective use cases.

Here is some example usage of the `alias` parameter:

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. The alias `'username'` is used for instance creation and validation.
2. We are using `model_dump` to convert the model into a serializable format.

    You can see more details about [`model_dump`](/api/main/#pydantic.main.BaseModel.model_dump) in the API reference.

    Note that the `by_alias` keyword argument defaults to `False`, and must be specified explicitly to dump
    models using the field (serialization) aliases.

    When `by_alias=True`, the alias `'username'` is also used during serialization.

If you want to use an alias _only_ for validation, you can use the `validation_alias` parameter:

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., validation_alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'name': 'johndoe'}
```

1. The validation alias `'username'` is used during validation.
2. The field name `'name'` is used during serialization.

If you only want to define an alias for _serialization_, you can use the `serialization_alias` parameter:

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(..., serialization_alias='username')


user = User(name='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. The field name `'name'` is used for validation.
2. The serialization alias `'username'` is used for serialization.

In case you use `alias` together with `validation_alias` or `serialization_alias` at the same time,
the `validation_alias` will have priority over `alias` for validation, and `serialization_alias` will have priority
over `alias` for serialization.

You can read more about [Alias Precedence](/usage/model_config/#alias-precedence) in the
[Model Config](/usage/model_config/) documentation.


??? tip "VSCode and Pyright users"
    In VSCode, if you use the [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
    extension, you won't see a warning when instantiating a model using a field's alias:

    ```py
    from pydantic import BaseModel, Field


    class User(BaseModel):
        name: str = Field(..., alias='username')


    user = User(username='johndoe')  # (1)!
    ```

    1. VSCode will NOT show a warning here.

    When the `'alias'` keyword argument is specified, even if you set `populate_by_name` to `True` in the
    [Model Config](/usage/model_config/#populate-by-name), VSCode will show a warning when instantiating
    a model using the field name (though it will work at runtime) — in this case, `'name'`:

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(..., alias='username')


    user = User(name='johndoe')  # (1)!
    ```

    1. VSCode will show a warning here.

    To "trick" VSCode into preferring the field name, you can use the `str` function to wrap the alias value:

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(..., alias='username')
    ```

     This is discussed in more detail in [this issue](https://github.com/pydantic/pydantic/issues/5893).

    ### Validation Alias

    Even though Pydantic treats `alias` and `validation_alias` the same when creating model instances, VSCode will not
    use the `validation_alias` in the class initializer signature. If you want VSCode to use the `validation_alias`
    in the class initializer, you can instead specify both an `alias` and `serialization_alias`, as the
    `serialization_alias` will override the `alias` during serialization:

    ```py
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(..., validation_alias='myValidationAlias')
    ```
    with:
    ```py
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(
            ..., alias='myValidationAlias', serialization_alias='my_serialization_alias'
        )


    m = MyModel(myValidationAlias=1)
    print(m.model_dump(by_alias=True))
    #> {'my_serialization_alias': 1}
    ```

    All of the above will likely also apply to other tools that respect the
    [`@typing.dataclass_transform`](https://docs.python.org/3/library/typing.html#typing.dataclass_transform)
    decorator, such as Pyright.

### `AliasPath` and `AliasChoices`

Pydantic provides two special types for convenience when using `validation_alias`: `AliasPath` and `AliasChoices`.

The `AliasPath` is used to specify a path to a field using aliases. For example:

```py lint="skip"
from pydantic import BaseModel, Field, AliasPath


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasPath('names', 0))
    last_name: str = Field(validation_alias=AliasPath('names', 1))

user = User.model_validate({'names': ['John', 'Doe']})  # (1)!
print(user)
#> first_name='John' last_name='Doe'
```

We are using `model_validate` to validate a dictionary using the field aliases.
You can see more details about [`model_validate`](/api/main/#pydantic.main.BaseModel.model_validate) in the API reference.

In the `'first_name'` field, we are using the alias `'names'` and the index `0` to specify the path to the first name.
In the `'last_name'` field, we are using the alias `'names'` and the index `1` to specify the path to the last name.

`AliasChoices` is used to specify a choice of aliases. For example:

```py lint="skip"
from pydantic import BaseModel, Field, AliasChoices


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', 'fname'))
    last_name: str = Field(validation_alias=AliasChoices('last_name', 'lname'))

user = User.model_validate({'fname': 'John', 'lname': 'Doe'})  # (1)!
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'first_name': 'John', 'lname': 'Doe'})  # (2)!
print(user)
#> first_name='John' last_name='Doe'
```

1. We are using the second alias choice for both fields.
2. We are using the first alias choice for the field `'first_name'` and the second alias choice
   for the field `'last_name'`.

You can also use `AliasChoices` with `AliasPath`:

```py lint="skip"
from pydantic import BaseModel, Field, AliasPath, AliasChoices


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasChoices('first_name', AliasPath('names', 0)))
    last_name: str = Field(validation_alias=AliasChoices('last_name', AliasPath('names', 1)))


user = User.model_validate({'first_name': 'John', 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John', 'Doe']})
print(user)
#> first_name='John' last_name='Doe'
user = User.model_validate({'names': ['John'], 'last_name': 'Doe'})
print(user)
#> first_name='John' last_name='Doe'
```

TODO: Document usage of other `Field` keyword arguments
