??? api "API Documentation"
    [`pydantic.fields.Field`][pydantic.fields.Field]<br>

In this section, we will go through the available mechanisms to customize Pydantic model fields:
default values, JSON Schema metadata, constraints, etc.

To do so, the [`Field()`][pydantic.fields.Field] function is used a lot, and behaves the same way as
the standard library [`field()`][dataclasses.field] function for dataclasses:

```python
from pydantic import BaseModel, Field


class Model(BaseModel):
    name: str = Field(frozen=True)
```

!!! note
    Even though `name` is assigned a value, it is still required and has no default value. If you want
    to emphasize on the fact that a value must be provided, you can use the [ellipsis][Ellipsis]:

    ```python {lint="skip" test="skip"}
    class Model(BaseModel):
        name: str = Field(..., frozen=True)
    ```

    However, its usage is discouraged as it doesn't play well with static type checkers.

## The annotated pattern

To apply constraints or attach [`Field()`][pydantic.fields.Field] functions to a model field, Pydantic
supports the [`Annotated`][typing.Annotated] typing construct to attach metadata to an annotation:

```python
from typing import Annotated

from pydantic import BaseModel, Field, WithJsonSchema


class Model(BaseModel):
    name: Annotated[str, Field(strict=True), WithJsonSchema({'extra': 'data'})]
```

As far as static type checkers are concerned, `name` is still typed as `str`, but Pydantic leverages
the available metadata to add validation logic, type constraints, etc.

Using this pattern has some advantages:

* Using the `f: <type> = Field(...)` form can be confusing and might trick users into thinking `f`
  has a default value, while in reality it is still required.
* You can provide an arbitrary amount of metadata elements for a field. As shown in the example above,
  the [`Field()`][pydantic.fields.Field] function only supports a limited set of constraints/metadata,
  and you may have to use different Pydantic utilities such as [`WithJsonSchema`][pydantic.WithJsonSchema]
  in some cases.
* Types can be made reusable (see the documentation on [custom types](./types.md#using-the-annotated-pattern)
  using this pattern).

However, note that certain arguments to the [`Field()`][pydantic.fields.Field] function (namely, `default`,
`default_factory`, and `alias`) are taken into account by static type checkers to synthesize a correct
`__init__` method. The annotated pattern is *not* understood by them, so you should use the normal
assignment form instead.

!!! tip
    The annotated pattern can also be used to add metadata to specific parts of the type. For instance,
    [validation constraints](#field-constraints) can be added this way:

    ```python
    from typing import Annotated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        int_list: list[Annotated[int, Field(gt=0)]]
        # Valid: [1, 3]
        # Invalid: [-1, 2]
    ```

    Be careful not mixing *field* and *type* metadata:

    ```python {test="skip" lint="skip"}
    class Model(BaseModel):
        field_bad: Annotated[int, Field(deprecated=True)] | None = None  # (1)!
        field_ok: Annotated[int | None, Field(deprecated=True)] = None  # (2)!
    ```

      1. The [`Field()`][pydantic.fields.Field] function is applied to `int` type, hence the
         `deprecated` flag won't have any effect. While this may be confusing given that the name of
         the [`Field()`][pydantic.fields.Field] function would imply it should apply to the field,
         the API was designed when this function was the only way to provide metadata. You can
         alternatively make use of the [`annotated_types`](https://github.com/annotated-types/annotated-types)
         library which is now supported by Pydantic.

      2. The [`Field()`][pydantic.fields.Field] function is applied to the "top-level" union type,
         hence the `deprecated` flag will be applied to the field.

## Default values

Default values for fields can be provided using the normal assignment syntax or by providing a value
to the `default` argument:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    # Both fields aren't required:
    name: str = 'John Doe'
    age: int = Field(default=20)
```

!!! warning
    [In Pydantic V1](../migration.md#required-optional-and-nullable-fields), a type annotated as [`Any`][typing.Any]
    or wrapped by [`Optional`][typing.Optional] would be given an implicit default of `None` even if no
    default was explicitly specified. This is no longer the case in Pydantic V2.

You can also pass a callable to the `default_factory` argument that will be called to generate a default value:

```python
from uuid import uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
```

<!-- markdownlint-disable-next-line no-empty-links -->
[](){#default-factory-validated-data}

The default factory can also take a single required argument, in which case the already validated data will be passed as a dictionary.

```python
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    email: EmailStr
    username: str = Field(default_factory=lambda data: data['email'])


user = User(email='user@example.com')
print(user.username)
#> user@example.com
```

The `data` argument will *only* contain the already validated data, based on the [order of model fields](./models.md#field-ordering)
(the above example would fail if `username` were to be defined before `email`).

## Validate default values

By default, Pydantic will *not* validate default values. The `validate_default` field parameter
(or the [`validate_default`][pydantic.ConfigDict.validate_default] configuration value) can be used
to enable this behavior:

```python
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

### Mutable default values

A common source of bugs in Python is to use a mutable object as a default value for a function or method argument,
as the same instance ends up being reused in each call.

The [`dataclasses`][dataclasses] module actually raises an error in this case, indicating that you should use
a [default factory](https://docs.python.org/3/library/dataclasses.html#default-factory-functions) instead.

While the same thing can be done in Pydantic, it is not required. In the event that the default value is not hashable,
Pydantic will create a deep copy of the default value when creating each instance of the model:

```python
from pydantic import BaseModel


class Model(BaseModel):
    item_counts: list[dict[str, int]] = [{}]


m1 = Model()
m1.item_counts[0]['a'] = 1
print(m1.item_counts)
#> [{'a': 1}]

m2 = Model()
print(m2.item_counts)
#> [{}]
```

## Field aliases

!!! tip
    Read more about aliases in the [dedicated section](./alias.md).

For validation and serialization, you can define an alias for a field.

There are three ways to define an alias:

* `Field(alias='foo')`
* `Field(validation_alias='foo')`
* `Field(serialization_alias='foo')`

The `alias` parameter is used for both validation *and* serialization. If you want to use
*different* aliases for validation and serialization respectively, you can use the `validation_alias`
and `serialization_alias` parameters, which will apply only in their respective use cases.

Here is an example of using the `alias` parameter:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. The alias `'username'` is used for instance creation and validation.
2. We are using [`model_dump()`][pydantic.main.BaseModel.model_dump] to convert the model into a serializable format.

    Note that the `by_alias` keyword argument defaults to `False`, and must be specified explicitly to dump
    models using the field (serialization) aliases.

    You can also use [`ConfigDict.serialize_by_alias`][pydantic.config.ConfigDict.serialize_by_alias] to
    configure this behavior at the model level.

    When `by_alias=True`, the alias `'username'` used during serialization.

If you want to use an alias *only* for validation, you can use the `validation_alias` parameter:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(validation_alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'name': 'johndoe'}
```

1. The validation alias `'username'` is used during validation.
2. The field name `'name'` is used during serialization.

If you only want to define an alias for *serialization*, you can use the `serialization_alias` parameter:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(serialization_alias='username')


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

    If you provide a value for the [`alias_generator`][pydantic.config.ConfigDict.alias_generator] model setting, you can control the order of precedence for field alias and generated aliases via the `alias_priority` field parameter. You can read more about alias precedence [here](../concepts/alias.md#alias-precedence).

??? tip "Static type checking/IDE support"
    If you provide a value for the `alias` field parameter, static type checkers will use this alias instead
    of the actual field name to synthesize the `__init__` method:

    ```python
    from pydantic import BaseModel, Field


    class User(BaseModel):
        name: str = Field(alias='username')


    user = User(username='johndoe')  # (1)!
    ```

    1. Accepted by type checkers.

    This means that when using the [`validate_by_name`][pydantic.config.ConfigDict.validate_by_name] model setting (which allows both the field name and alias to be used during model validation), type checkers will error when the actual field name is used:

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(validate_by_name=True)

        name: str = Field(alias='username')


    user = User(name='johndoe')  # (1)!
    ```

    1. *Not* accepted by type checkers.

    If you still want type checkers to use the field name and not the alias, the [annotated pattern](#the-annotated-pattern)
    can be used (which is only understood by Pydantic):

    ```python
    from typing import Annotated

    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

        name: Annotated[str, Field(alias='username')]


    user = User(name='johndoe')  # (1)!
    user = User(username='johndoe')  # (2)!
    ```

    1. Accepted by type checkers.
    2. *Not* accepted by type checkers.

    <h3>Validation Alias</h3>

    Even though Pydantic treats `alias` and `validation_alias` the same when creating model instances, type checkers
    only understand the `alias` field parameter. As a workaround, you can instead specify both an `alias` and
    `serialization_alias` (identical to the field name), as the `serialization_alias` will override the `alias` during
    serialization:

    ```python
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(validation_alias='myValidationAlias')
    ```

    with:

    ```python
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(
            alias='myValidationAlias',
            serialization_alias='my_field',
        )


    m = MyModel(myValidationAlias=1)
    print(m.model_dump(by_alias=True))
    #> {'my_field': 1}
    ```

<!-- markdownlint-disable-next-line no-empty-links -->
[](){#field-constraints}

## Numeric Constraints

There are some keyword arguments that can be used to constrain numeric values:

* `gt` - greater than
* `lt` - less than
* `ge` - greater than or equal to
* `le` - less than or equal to
* `multiple_of` - a multiple of the given number
* `allow_inf_nan` - allow `'inf'`, `'-inf'`, `'nan'` values

Here's an example:

```python
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

    * `gt` and `lt` constraints will be translated to `exclusiveMinimum` and `exclusiveMaximum`.
    * `ge` and `le` constraints will be translated to `minimum` and `maximum`.
    * `multiple_of` constraint will be translated to `multipleOf`.

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

    ```python
    from typing import Annotated, Optional

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

```python
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

    * `min_length` constraint will be translated to `minLength`.
    * `max_length` constraint will be translated to `maxLength`.
    * `pattern` constraint will be translated to `pattern`.

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

```python
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

```python
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

## Field Representation

The parameter `repr` can be used to control whether the field should be included in the string
representation of the model.

```python
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

```python
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

1. See more about [Validating data] in the [Models] page.

The following example shows how to use the `discriminator` keyword argument with a `Discriminator` instance:

```python
from typing import Annotated, Literal, Union

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

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(strict=True)
    age: int = Field(strict=False)  # (1)!


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

```python
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

```python
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
* The [deprecated](https://json-schema.org/draft/2020-12/json-schema-validation#section-9.3) keyword
  being set in the generated JSON schema.

This parameter accepts different types, described below.

### `deprecated` as a string

The value will be used as the deprecation message.

```python
from typing import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated='This is deprecated')]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

### `deprecated` via the `@warnings.deprecated` decorator

The [`@warnings.deprecated`][warnings.deprecated] decorator (or the
[`typing_extensions` backport][typing_extensions.deprecated] on Python
3.12 and lower) can be used as an instance.

<!-- TODO: tabs should be auto-generated if using Ruff (https://github.com/pydantic/pydantic/issues/10083) -->

=== "Python 3.9 and above"

    ```python
    from typing import Annotated

    from typing_extensions import deprecated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        deprecated_field: Annotated[int, deprecated('This is deprecated')]

        # Or explicitly using `Field`:
        alt_form: Annotated[int, Field(deprecated=deprecated('This is deprecated'))]
    ```

=== "Python 3.13 and above"

    ```python {requires="3.13"}
    from typing import Annotated
    from warnings import deprecated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        deprecated_field: Annotated[int, deprecated('This is deprecated')]

        # Or explicitly using `Field`:
        alt_form: Annotated[int, Field(deprecated=deprecated('This is deprecated'))]
    ```

!!! note "Support for `category` and `stacklevel`"
    The current implementation of this feature does not take into account the `category` and `stacklevel`
    arguments to the `deprecated` decorator. This might land in a future version of Pydantic.

### `deprecated` as a boolean

```python
from typing import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated=True)]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

!!! warning "Accessing a deprecated field in validators"
    When accessing a deprecated field inside a validator, the deprecation warning will be emitted. You can use
    [`catch_warnings`][warnings.catch_warnings] to explicitly ignore it:

    ```python
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
    [`computed_field`][pydantic.fields.computed_field]<br>

The [`computed_field`][pydantic.fields.computed_field] decorator can be used to include [`property`][] or
[`cached_property`][functools.cached_property] attributes when serializing a model or dataclass.
The property will also be taken into account in the JSON Schema (in serialization mode).

!!! note
    Properties can be useful for fields that are computed from other fields, or for fields that
    are expensive to be computed (and thus, are cached if using [`cached_property`][functools.cached_property]).

    However, note that Pydantic will *not* perform any additional logic on the wrapped property
    (validation, cache invalidation, etc.).

Here's an example of the JSON schema (in serialization mode) generated for a model with a computed field:

```python
from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property  # (1)!
    def volume(self) -> float:
        return self.width * self.height * self.depth


print(Box.model_json_schema(mode='serialization'))
"""
{
    'properties': {
        'width': {'title': 'Width', 'type': 'number'},
        'height': {'title': 'Height', 'type': 'number'},
        'depth': {'title': 'Depth', 'type': 'number'},
        'volume': {'readOnly': True, 'title': 'Volume', 'type': 'number'},
    },
    'required': ['width', 'height', 'depth', 'volume'],
    'title': 'Box',
    'type': 'object',
}
"""
```

1. If not specified, [`computed_field`][pydantic.fields.computed_field] will implicitly convert the method
   to a [`property`][]. However, it is preferable to explicitly use the [`@property`][property] decorator
   for type checking purposes.

Here's an example using the `model_dump` method with a computed field:

```python
from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property
    def volume(self) -> float:
        return self.width * self.height * self.depth


b = Box(width=1, height=2, depth=3)
print(b.model_dump())
#> {'width': 1.0, 'height': 2.0, 'depth': 3.0, 'volume': 6.0}
```

As with regular fields, computed fields can be marked as being deprecated:

```python
from typing_extensions import deprecated

from pydantic import BaseModel, computed_field


class Box(BaseModel):
    width: float
    height: float
    depth: float

    @computed_field
    @property
    @deprecated("'volume' is deprecated")
    def volume(self) -> float:
        return self.width * self.height * self.depth
```

[Discriminated Unions]: ../concepts/unions.md#discriminated-unions
[Validating data]: models.md#validating-data
[Models]: models.md
[init-only field]: https://docs.python.org/3/library/dataclasses.html#init-only-variables
[frozen dataclass documentation]: https://docs.python.org/3/library/dataclasses.html#frozen-instances
[Customizing JSON Schema]: json_schema.md#field-level-customization
