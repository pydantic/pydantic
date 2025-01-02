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

user = User.model_validate({'names': ['John', 'Doe']})  # (1)!
print(user)
#> first_name='John' last_name='Doe'
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
