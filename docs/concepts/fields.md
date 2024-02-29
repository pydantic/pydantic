??? api "API Documentation"
    [`pydantic.fields.Field`][pydantic.fields.Field]<br>

The [`Field`][pydantic.fields.Field] function is used to customize and add metadata to fields of models.

## Default values

The `default` parameter is used to define a default value for a field.

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(default='John Doe')


user = User()
print(user)
#> name='John Doe'
```

You can also use `default_factory` to define a callable that will be called to generate a default value.

```py
from uuid import uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
```

!!! info
    The `default` and `default_factory` parameters are mutually exclusive.

!!! note
    If you use `typing.Optional`, it doesn't mean that the field has a default value of `None`!

## Using `Annotated`

The [`Field`][pydantic.fields.Field] function can also be used together with [`Annotated`][annotated].

```py
from uuid import uuid4

from typing_extensions import Annotated

from pydantic import BaseModel, Field


class User(BaseModel):
    id: Annotated[str, Field(default_factory=lambda: uuid4().hex)]
```

!!! note
    Defaults can be set outside [`Annotated`][annotated] as the assigned value or with `Field.default_factory` inside
    [`Annotated`][annotated]. The `Field.default` argument is not supported inside [`Annotated`][annotated].


## Field aliases

For validation and serialization, you can define an alias for a field.

There are three ways to define an alias:

* `Field(..., alias='foo')`
* `Field(..., validation_alias='foo')`
* `Field(..., serialization_alias='foo')`

The `alias` parameter is used for both validation _and_ serialization. If you want to use
_different_ aliases for validation and serialization respectively, you can use the`validation_alias`
and `serialization_alias` parameters, which will apply only in their respective use cases.

Here is an example of using the `alias` parameter:

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

    You can see more details about [`model_dump`][pydantic.main.BaseModel.model_dump] in the API reference.

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

!!! note "Alias precedence and priority"
    In case you use `alias` together with `validation_alias` or `serialization_alias` at the same time,
    the `validation_alias` will have priority over `alias` for validation, and `serialization_alias` will have priority
    over `alias` for serialization.

    You may also set `alias_priority` on a field to change this behavior.

    You can read more about [Alias Precedence](../concepts/alias.md#alias-precedence) in the
    [Model Config][pydantic.config.ConfigDict] documentation.


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
    [Model Config][pydantic.config.ConfigDict.populate_by_name], VSCode will show a warning when instantiating
    a model using the field name (though it will work at runtime) — in this case, `'name'`:

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(..., alias='username')


    user = User(name='johndoe')  # (1)!
    ```

    1. VSCode will show a warning here.

    To "trick" VSCode into preferring the field name, you can use the `str` function to wrap the alias value.
    With this approach, though, a warning is shown when instantiating a model using the alias for the field:

    ```py
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(..., alias=str('username'))  # noqa: UP018


    user = User(name='johndoe')  # (1)!
    user = User(username='johndoe')  # (2)!
    ```

    1. Now VSCode will NOT show a warning
    2. VSCode will show a warning here, though

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
            ...,
            alias='myValidationAlias',
            serialization_alias='my_serialization_alias',
        )


    m = MyModel(myValidationAlias=1)
    print(m.model_dump(by_alias=True))
    #> {'my_serialization_alias': 1}
    ```

    All of the above will likely also apply to other tools that respect the
    [`@typing.dataclass_transform`](https://docs.python.org/3/library/typing.html#typing.dataclass_transform)
    decorator, such as Pyright.

For more information on alias usage, see the [Alias] concepts page.

## Numeric Constraints

There are some keyword arguments that can be used to constrain numeric values:

* `gt` - greater than
* `lt` - less than
* `ge` - greater than or equal to
* `le` - less than or equal to
* `multiple_of` - a multiple of the given number
* `allow_inf_nan` - allow `'inf'`, `'-inf'`, `'nan'` values

Here's an example:

```py
from pydantic import BaseModel, Field


class Foo(BaseModel):
    positive: int = Field(gt=0)
    non_negative: int = Field(ge=0)
    negative: int = Field(lt=0)
    non_positive: int = Field(le=0)
    even: int = Field(multiple_of=2)
    love_for_pydantic: float = Field(allow_inf_nan=True)


foo = Foo(
    positive=1,
    non_negative=0,
    negative=-1,
    non_positive=0,
    even=2,
    love_for_pydantic=float('inf'),
)
print(foo)
"""
positive=1 non_negative=0 negative=-1 non_positive=0 even=2 love_for_pydantic=inf
"""
```

??? info "JSON Schema"
    In the generated JSON schema:

    - `gt` and `lt` constraints will be translated to `exclusiveMinimum` and `exclusiveMaximum`.
    - `ge` and `le` constraints will be translated to `minimum` and `maximum`.
    - `multiple_of` constraint will be translated to `multipleOf`.

    The above snippet will generate the following JSON Schema:

    ```json
    {
      "title": "Foo",
      "type": "object",
      "properties": {
        "positive": {
          "title": "Positive",
          "type": "integer",
          "exclusiveMinimum": 0
        },
        "non_negative": {
          "title": "Non Negative",
          "type": "integer",
          "minimum": 0
        },
        "negative": {
          "title": "Negative",
          "type": "integer",
          "exclusiveMaximum": 0
        },
        "non_positive": {
          "title": "Non Positive",
          "type": "integer",
          "maximum": 0
        },
        "even": {
          "title": "Even",
          "type": "integer",
          "multipleOf": 2
        },
        "love_for_pydantic": {
          "title": "Love For Pydantic",
          "type": "number"
        }
      },
      "required": [
        "positive",
        "non_negative",
        "negative",
        "non_positive",
        "even",
        "love_for_pydantic"
      ]
    }
    ```

    See the [JSON Schema Draft 2020-12] for more details.

!!! warning "Constraints on compound types"
    In case you use field constraints with compound types, an error can happen in some cases. To avoid potential issues,
    you can use `Annotated`:

    ```py
    from typing import Optional

    from typing_extensions import Annotated

    from pydantic import BaseModel, Field


    class Foo(BaseModel):
        positive: Optional[Annotated[int, Field(gt=0)]]
        # Can error in some cases, not recommended:
        non_negative: Optional[int] = Field(ge=0)
    ```

## String Constraints

??? api "API Documentation"
    [`pydantic.types.StringConstraints`][pydantic.types.StringConstraints]<br>

There are fields that can be used to constrain strings:

* `min_length`: Minimum length of the string.
* `max_length`: Maximum length of the string.
* `pattern`: A regular expression that the string must match.

Here's an example:

```py
from pydantic import BaseModel, Field


class Foo(BaseModel):
    short: str = Field(min_length=3)
    long: str = Field(max_length=10)
    regex: str = Field(pattern=r'^\d*$')  # (1)!


foo = Foo(short='foo', long='foobarbaz', regex='123')
print(foo)
#> short='foo' long='foobarbaz' regex='123'
```

1. Only digits are allowed.

??? info "JSON Schema"
    In the generated JSON schema:

    - `min_length` constraint will be translated to `minLength`.
    - `max_length` constraint will be translated to `maxLength`.
    - `pattern` constraint will be translated to `pattern`.

    The above snippet will generate the following JSON Schema:

    ```json
    {
      "title": "Foo",
      "type": "object",
      "properties": {
        "short": {
          "title": "Short",
          "type": "string",
          "minLength": 3
        },
        "long": {
          "title": "Long",
          "type": "string",
          "maxLength": 10
        },
        "regex": {
          "title": "Regex",
          "type": "string",
          "pattern": "^\\d*$"
        }
      },
      "required": [
        "short",
        "long",
        "regex"
      ]
    }
    ```

## Decimal Constraints

There are fields that can be used to constrain decimals:

* `max_digits`: Maximum number of digits within the `Decimal`. It does not include a zero before the decimal point or
  trailing decimal zeroes.
* `decimal_places`: Maximum number of decimal places allowed. It does not include trailing decimal zeroes.

Here's an example:

```py
from decimal import Decimal

from pydantic import BaseModel, Field


class Foo(BaseModel):
    precise: Decimal = Field(max_digits=5, decimal_places=2)


foo = Foo(precise=Decimal('123.45'))
print(foo)
#> precise=Decimal('123.45')
```

## Dataclass Constraints

There are fields that can be used to constrain dataclasses:

* `init`: Whether the field should be included in the `__init__` of the dataclass.
* `init_var`: Whether the field should be seen as an [init-only field] in the dataclass.
* `kw_only`: Whether the field should be a keyword-only argument in the constructor of the dataclass.

Here's an example:

```py
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


@dataclass
class Foo:
    bar: str
    baz: str = Field(init_var=True)
    qux: str = Field(kw_only=True)


class Model(BaseModel):
    foo: Foo


model = Model(foo=Foo('bar', baz='baz', qux='qux'))
print(model.model_dump())  # (1)!
#> {'foo': {'bar': 'bar', 'qux': 'qux'}}
```

1. The `baz` field is not included in the `model_dump()` output, since it is an init-only field.

## Validate Default Values

The parameter `validate_default` can be used to control whether the default value of the field should be validated.

By default, the default value of the field is not validated.

```py
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    age: int = Field(default='twelve', validate_default=True)


try:
    user = User()
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='twelve', input_type=str]
    """
```

## Field Representation

The parameter `repr` can be used to control whether the field should be included in the string
representation of the model.

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(repr=True)  # (1)!
    age: int = Field(repr=False)


user = User(name='John', age=42)
print(user)
#> name='John'
```

1. This is the default value.

## Discriminator

The parameter `discriminator` can be used to control the field that will be used to discriminate between different
models in a union. It takes either the name of a field or a `Discriminator` instance. The `Discriminator`
approach can be useful when the discriminator fields aren't the same for all the models in the `Union`.

The following example shows how to use `discriminator` with a field name:

```py requires="3.8"
from typing import Literal, Union

from pydantic import BaseModel, Field


class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int


class Dog(BaseModel):
    pet_type: Literal['dog']
    age: int


class Model(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator='pet_type')


print(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}}))  # (1)!
#> pet=Cat(pet_type='cat', age=12)
```

1. See more about [Helper Functions] in the [Models] page.

The following example shows how to use the `discriminator` keyword argument with a `Discriminator` instance:

```py requires="3.8"
from typing import Literal, Union

from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Field, Tag


class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int


class Dog(BaseModel):
    pet_kind: Literal['dog']
    age: int


def pet_discriminator(v):
    if isinstance(v, dict):
        return v.get('pet_type', v.get('pet_kind'))
    return getattr(v, 'pet_type', getattr(v, 'pet_kind', None))


class Model(BaseModel):
    pet: Union[Annotated[Cat, Tag('cat')], Annotated[Dog, Tag('dog')]] = Field(
        discriminator=Discriminator(pet_discriminator)
    )


print(repr(Model.model_validate({'pet': {'pet_type': 'cat', 'age': 12}})))
#> Model(pet=Cat(pet_type='cat', age=12))

print(repr(Model.model_validate({'pet': {'pet_kind': 'dog', 'age': 12}})))
#> Model(pet=Dog(pet_kind='dog', age=12))
```

You can also take advantage of `Annotated` to define your discriminated unions.
See the [Discriminated Unions] docs for more details.

## Strict Mode

The `strict` parameter on a [`Field`][pydantic.fields.Field] specifies whether the field should be validated in "strict mode".
In strict mode, Pydantic throws an error during validation instead of coercing data on the field where `strict=True`.

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(strict=True)  # (1)!
    age: int = Field(strict=False)


user = User(name='John', age='42')  # (2)!
print(user)
#> name='John' age=42
```

1. This is the default value.
2. The `age` field is not validated in the strict mode. Therefore, it can be assigned a string.

See [Strict Mode](strict_mode.md) for more details.

See [Conversion Table](conversion_table.md) for more details on how Pydantic converts data in both strict and lax modes.

## Immutability

The parameter `frozen` is used to emulate the frozen dataclass behaviour. It is used to prevent the field from being
assigned a new value after the model is created (immutability).

See the [frozen dataclass documentation] for more details.

```py
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str = Field(frozen=True)
    age: int


user = User(name='John', age=42)

try:
    user.name = 'Jane'  # (1)!
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Field is frozen [type=frozen_field, input_value='Jane', input_type=str]
    """
```

1. Since `name` field is frozen, the assignment is not allowed.

## Exclude

The `exclude` parameter can be used to control which fields should be excluded from the
model when exporting the model.

See the following example:

```py
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    age: int = Field(exclude=True)


user = User(name='John', age=42)
print(user.model_dump())  # (1)!
#> {'name': 'John'}
```

1. The `age` field is not included in the `model_dump()` output, since it is excluded.

See the [Serialization] section for more details.

## Deprecated fields

The `deprecated` parameter can be used to mark a field as being deprecated. Doing so will result in:

* a runtime deprecation warning emitted when accessing the field.
* `"deprecated": true` being set in the generated JSON schema.

You can set the `deprecated` parameter as one of:

* A string, which will be used as the deprecation message.
* An instance of the `warnings.deprecated` decorator (or the `typing_extensions` backport).
* A boolean, which will be used to mark the field as deprecated without a default `'deprecated'` deprecation message.

### `deprecated` as a string

```py
from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated='This is deprecated')]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

### `deprecated` via the `warnings.deprecated` decorator

```py test="skip"
from typing_extensions import Annotated, deprecated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, deprecated('This is deprecated')]

    # Or explicitly using `Field`:
    alt_form: Annotated[int, Field(deprecated=deprecated('This is deprecated'))]
```

### `deprecated` as a boolean

```py
from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated=True)]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```


!!! note "Support for `category` and `stacklevel`"
    The current implementation of this feature does not take into account the `category` and `stacklevel`
    arguments to the `deprecated` decorator. This might land in a future version of Pydantic.

!!! warning "Accessing a deprecated field in validators"
    When accessing a deprecated field inside a validator, the deprecation warning will be emitted. You can use
    [`catch_warnings`][warnings.catch_warnings] to explicitly ignore it:

    ```py
    import warnings

    from typing_extensions import Self

    from pydantic import BaseModel, Field, model_validator


    class Model(BaseModel):
        deprecated_field: int = Field(deprecated='This is deprecated')

        @model_validator(mode='after')
        def validate_model(self) -> Self:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', DeprecationWarning)
                self.deprecated_field = self.deprecated_field * 2
    ```

## Customizing JSON Schema

Some field parameters are used exclusively to customize the generated JSON schema. The parameters in question are:

* `title`
* `description`
* `examples`
* `json_schema_extra`

Read more about JSON schema customization / modification with fields in the [Customizing JSON Schema] section of the JSON schema docs.

## The `computed_field` decorator

??? api "API Documentation"
    [`pydantic.fields.computed_field`][pydantic.fields.computed_field]<br>

The `computed_field` decorator can be used to include `property` or `cached_property` attributes when serializing a
model or dataclass. This can be useful for fields that are computed from other fields, or for fields that
are expensive to computed (and thus, are cached).

Here's an example:

```py
from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    def volume(self) -> float:
        return self.width * self.height * self.depth


b = Box(width=1, height=2, depth=3)
print(b.model_dump())
#> {'width': 1.0, 'height': 2.0, 'depth': 3.0, 'volume': 6.0}
```

As with regular fields, computed fields can be marked as being deprecated:

```py
from typing_extensions import deprecated

from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @deprecated("'volume' is deprecated")
    def volume(self) -> float:
        return self.width * self.height * self.depth
```


[JSON Schema Draft 2020-12]: https://json-schema.org/understanding-json-schema/reference/numeric.html#numeric-types
[Discriminated Unions]: ../concepts/unions.md#discriminated-unions
[Helper Functions]: models.md#helper-functions
[Models]: models.md
[init-only field]: https://docs.python.org/3/library/dataclasses.html#init-only-variables
[frozen dataclass documentation]: https://docs.python.org/3/library/dataclasses.html#frozen-instances
[Validate Assignment]: models.md#validate-assignment
[Serialization]: serialization.md#model-and-field-level-include-and-exclude
[Customizing JSON Schema]: json_schema.md#field-level-customization
[annotated]: https://docs.python.org/3/library/typing.html#typing.Annotated
[Alias]: ../concepts/alias.md
