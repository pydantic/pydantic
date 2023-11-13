An alias is an alternative name for a field, used when serializing and deserializing data.

You can specify an alias in the following ways:

* `alias` on the [`Field`][pydantic.fields.Field]
* `validation_alias` on the [`Field`][pydantic.fields.Field]
* `serialization_alias` on the [`Field`][pydantic.fields.Field]
* `alias_generator` on the [`Config`][pydantic.config.ConfigDict.alias_generator]

## Alias Precedence

If you specify an `alias` on the [`Field`][pydantic.fields.Field], it will take precedence over the generated alias by default:

```py
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
* `alias_priority` not set, the alias will be overridden by the alias generator.

The same precedence applies to `validation_alias` and `serialization_alias`.
See more about the different field aliases under [field aliases](../concepts/fields.md#field-aliases).
