An alias is an alternative name for a field, used when serializing and deserializing data.

You can specify an alias in the following ways:

* `alias` on the [`Field`][pydantic.fields.Field]
    * must be a `str`
* `validation_alias` on the [`Field`][pydantic.fields.Field]
    * can be an instance of `str`, [`AliasPath`][pydantic.aliases.AliasPath], or [`AliasChoices`][pydantic.aliases.AliasChoices]
* `serialization_alias` on the [`Field`][pydantic.fields.Field]
    * must be a `str`
* `alias_generator` on the [`Config`][pydantic.config.ConfigDict.alias_generator]
    * can be a callable or an instance of [`AliasGenerator`][pydantic.aliases.AliasGenerator]

For examples of how to use `alias`, `validation_alias`, and `serialization_alias`, see [Field aliases](../concepts/fields.md#field-aliases).

## `AliasPath` and `AliasChoices`

??? api "API Documentation"

    [`pydantic.aliases.AliasPath`][pydantic.aliases.AliasPath]<br>
    [`pydantic.aliases.AliasChoices`][pydantic.aliases.AliasChoices]<br>

Pydantic provides two special types for convenience when using `validation_alias`: `AliasPath` and `AliasChoices`.

The `AliasPath` is used to specify a path to a field using aliases. For example:

```python {lint="skip"}
from pydantic import BaseModel, Field, AliasPath


class User(BaseModel):
    first_name: str = Field(validation_alias=AliasPath('names', 0))
    last_name: str = Field(validation_alias=AliasPath('names', 1))
    address: str = Field(validation_alias=AliasPath('contact', 'address'))

user = User.model_validate({  # (1)!
    'names': ['John', 'Doe'],
    'contact': {'address': '221B Baker Street'}
})
print(user)
#> first_name='John' last_name='Doe' address='221B Baker Street'
```

1. We are using `model_validate` to validate a dictionary using the field aliases.

    You can see more details about [`model_validate`][pydantic.main.BaseModel.model_validate] in the API reference.

In the `'first_name'` field, we are using the alias `'names'` and the index `0` to specify the path to the first name.
In the `'last_name'` field, we are using the alias `'names'` and the index `1` to specify the path to the last name.

`AliasChoices` is used to specify a choice of aliases. For example:

```python {lint="skip"}
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

```python {lint="skip"}
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

## Using alias generators

You can use the `alias_generator` parameter of [`Config`][pydantic.config.ConfigDict.alias_generator] to specify
a callable (or group of callables, via `AliasGenerator`) that will generate aliases for all fields in a model.
This is useful if you want to use a consistent naming convention for all fields in a model, but do not
want to specify the alias for each field individually.

!!! note
    Pydantic offers three built-in alias generators that you can use out of the box:

    [`to_pascal`][pydantic.alias_generators.to_pascal]<br>
    [`to_camel`][pydantic.alias_generators.to_camel]<br>
    [`to_snake`][pydantic.alias_generators.to_snake]<br>

### Using a callable

Here's a basic example using a callable:

```python
from pydantic import BaseModel, ConfigDict


class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field_name: field_name.upper()
    )

    age: int
    height: float
    kind: str


t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'}
```

### Using an `AliasGenerator`

??? api "API Documentation"

    [`pydantic.aliases.AliasGenerator`][pydantic.aliases.AliasGenerator]<br>

`AliasGenerator` is a class that allows you to specify multiple alias generators for a model.
You can use an `AliasGenerator` to specify different alias generators for validation and serialization.

This is particularly useful if you need to use different naming conventions for loading and saving data,
but you don't want to specify the validation and serialization aliases for each field individually.

For example:

```python
from pydantic import AliasGenerator, BaseModel, ConfigDict


class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: field_name.upper(),
            serialization_alias=lambda field_name: field_name.title(),
        )
    )

    age: int
    height: float
    kind: str


t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'Age': 12, 'Height': 1.2, 'Kind': 'oak'}
```

## Alias Precedence

If you specify an `alias` on the [`Field`][pydantic.fields.Field], it will take precedence over the generated alias by default:

```python
from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class Voice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str
    language_code: str = Field(alias='lang')


voice = Voice(Name='Filiz', lang='tr-TR')
print(voice.language_code)
#> tr-TR
print(voice.model_dump(by_alias=True))
#> {'Name': 'Filiz', 'lang': 'tr-TR'}
```

### Alias Priority

You may set `alias_priority` on a field to change this behavior:

* `alias_priority=2` the alias will *not* be overridden by the alias generator.
* `alias_priority=1` the alias *will* be overridden by the alias generator.
* `alias_priority` not set:
    * alias is set: the alias will *not* be overridden by the alias generator.
    * alias is not set: the alias *will* be overridden by the alias generator.

The same precedence applies to `validation_alias` and `serialization_alias`.
See more about the different field aliases under [field aliases](../concepts/fields.md#field-aliases).

## Alias Configuration

You can use [`ConfigDict`](./config.md) settings or runtime validation/serialization
settings to control whether or not aliases are used.

### `ConfigDict` Settings

You can use [configuration settings](./config.md) to control, at the model level,
whether or not aliases are used for validation and serialization. If you would like to control
this behavior for nested models/surpassing the config-model boundary, use [runtime settings](#runtime-settings).

#### Validation

When validating data, you can enable population of attributes by attribute name, alias, or both.
**By default**, Pydantic uses aliases for validation. Further configuration is available via:

* [`ConfigDict.validate_by_alias`][pydantic.config.ConfigDict.validate_by_alias]: `True` by default
* [`ConfigDict.validate_by_name`][pydantic.config.ConfigDict.validate_by_name]: `False` by default

=== "`validate_by_alias`"

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')

        model_config = ConfigDict(validate_by_alias=True, validate_by_name=False)


    print(repr(Model(my_alias='foo')))  # (1)!
    #> Model(my_field='foo')
    ```

    1. The alias `my_alias` is used for validation.

=== "`validate_by_name`"

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')

        model_config = ConfigDict(validate_by_alias=False, validate_by_name=True)


    print(repr(Model(my_field='foo')))  # (1)!
    #> Model(my_field='foo')
    ```

    1. the attribute identifier `my_field` is used for validation.

=== "`validate_by_alias` and `validate_by_name`"

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')

        model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)


    print(repr(Model(my_alias='foo')))  # (1)!
    #> Model(my_field='foo')

    print(repr(Model(my_field='foo')))  # (2)!
    #> Model(my_field='foo')
    ```

    1. The alias `my_alias` is used for validation.
    2. the attribute identifier `my_field` is used for validation.

!!! warning
    You cannot set both `validate_by_alias` and `validate_by_name` to `False`.
    A [user error](../errors/usage_errors.md#validate-by-alias-and-name-false) is raised in this case.

#### Serialization

When serializing data, you can enable serialization by alias, which is disabled by default.
See the [`ConfigDict.serialize_by_alias`][pydantic.config.ConfigDict.serialize_by_alias] API documentation
for more details.

```python
from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    my_field: str = Field(serialization_alias='my_alias')

    model_config = ConfigDict(serialize_by_alias=True)


m = Model(my_field='foo')
print(m.model_dump())  # (1)!
#> {'my_alias': 'foo'}
```

1. The alias `my_alias` is used for serialization.

!!! note
    The fact that serialization by alias is disabled by default is notably inconsistent with the default for
    validation (where aliases are used by default). We anticipate changing this default in V3.

### Runtime Settings

You can use runtime alias flags to control alias use for validation and serialization
on a per-call basis. If you would like to control this behavior on a model level, use
[`ConfigDict` settings](#configdict-settings).

#### Validation

When validating data, you can enable population of attributes by attribute name, alias, or both.

The `by_alias` and `by_name` flags are available on the [`model_validate()`][pydantic.main.BaseModel.model_validate],
[`model_validate_json()`][pydantic.main.BaseModel.model_validate_json], and [`model_validate_strings()`][pydantic.main.BaseModel.model_validate_strings] methods, as well as the [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] validation methods.

By default:

* `by_alias` is `True`
* `by_name` is `False`

=== "`by_alias`"

    ```python
    from pydantic import BaseModel, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')


    m = Model.model_validate(
        {'my_alias': 'foo'},  # (1)!
        by_alias=True,
        by_name=False,
    )
    print(repr(m))
    #> Model(my_field='foo')
    ```

    1. The alias `my_alias` is used for validation.

=== "`by_name`"

    ```python
    from pydantic import BaseModel, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')


    m = Model.model_validate(
        {'my_field': 'foo'}, by_alias=False, by_name=True  # (1)!
    )
    print(repr(m))
    #> Model(my_field='foo')
    ```

    1. The attribute name `my_field` is used for validation.

=== "`validate_by_alias` and `validate_by_name`"

    ```python
    from pydantic import BaseModel, Field


    class Model(BaseModel):
        my_field: str = Field(validation_alias='my_alias')


    m = Model.model_validate(
        {'my_alias': 'foo'}, by_alias=True, by_name=True  # (1)!
    )
    print(repr(m))
    #> Model(my_field='foo')

    m = Model.model_validate(
        {'my_field': 'foo'}, by_alias=True, by_name=True  # (2)!
    )
    print(repr(m))
    #> Model(my_field='foo')
    ```

    1. The alias `my_alias` is used for validation.
    2. The attribute name `my_field` is used for validation.

!!! warning
    You cannot set both `by_alias` and `by_name` to `False`.
    A [user error](../errors/usage_errors.md#validate-by-alias-and-name-false) is raised in this case.

#### Serialization

When serializing data, you can enable serialization by alias via the `by_alias` flag
which is available on the [`model_dump()`][pydantic.main.BaseModel.model_dump] and
[`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] methods, as well as
the [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] ones.

By default, `by_alias` is `False`.

```py
from pydantic import BaseModel, Field


class Model(BaseModel):
    my_field: str = Field(serialization_alias='my_alias')


m = Model(my_field='foo')
print(m.model_dump(by_alias=True))  # (1)!
#> {'my_alias': 'foo'}
```

1. The alias `my_alias` is used for serialization.

!!! note
    The fact that serialization by alias is disabled by default is notably inconsistent with the default for
    validation (where aliases are used by default). We anticipate changing this default in V3.
