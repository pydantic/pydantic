# Settings Management

[Pydantic Settings](https://github.com/pydantic/pydantic-settings) provides optional Pydantic features for loading a settings or config class from environment variables or secrets files.

## Installation

Installation is as simple as:

```bash
pip install pydantic-settings

```

## Usage

If you create a model that inherits from `BaseSettings`, the model initialiser will attempt to determine the values of any fields not passed as keyword arguments by reading from the environment. (Default values will still be used if the matching environment variable is not set.)

This makes it easy to:

- Create a clearly-defined, type-hinted application configuration class
- Automatically read modifications to the configuration from environment variables
- Manually override specific settings in the initialiser where desired (e.g. in unit tests)

For example:

```py
from collections.abc import Callable
from typing import Any

from pydantic import (
    AliasChoices,
    AmqpDsn,
    BaseModel,
    Field,
    ImportString,
    PostgresDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings, SettingsConfigDict


class SubModel(BaseModel):
    foo: str = 'bar'
    apple: int = 1


class Settings(BaseSettings):
    auth_key: str = Field(validation_alias='my_auth_key')  # (1)!

    api_key: str = Field(alias='my_api_key')  # (2)!

    redis_dsn: RedisDsn = Field(
        'redis://user:pass@localhost:6379/1',
        validation_alias=AliasChoices('service_redis_dsn', 'redis_url'),  # (3)!
    )
    pg_dsn: PostgresDsn = 'postgres://user:pass@localhost:5432/foobar'
    amqp_dsn: AmqpDsn = 'amqp://user:pass@localhost:5672/'

    special_function: ImportString[Callable[[Any], Any]] = 'math.cos'  # (4)!

    # to override domains:
    # export my_prefix_domains='["foo.com", "bar.com"]'
    domains: set[str] = set()

    # to override more_settings:
    # export my_prefix_more_settings='{"foo": "x", "apple": 1}'
    more_settings: SubModel = SubModel()

    model_config = SettingsConfigDict(env_prefix='my_prefix_')  # (5)!


print(Settings().model_dump())
"""
{
    'auth_key': 'xxx',
    'api_key': 'xxx',
    'redis_dsn': RedisDsn('redis://user:pass@localhost:6379/1'),
    'pg_dsn': PostgresDsn('postgres://user:pass@localhost:5432/foobar'),
    'amqp_dsn': AmqpDsn('amqp://user:pass@localhost:5672/'),
    'special_function': math.cos,
    'domains': set(),
    'more_settings': {'foo': 'bar', 'apple': 1},
}
"""

```

1. The environment variable name is overridden using `validation_alias`. In this case, the environment variable `my_auth_key` will be read instead of `auth_key`.

   Check the [`Field` documentation](../fields/) for more information.

1. The environment variable name is overridden using `alias`. In this case, the environment variable `my_api_key` will be used for both validation and serialization instead of `api_key`.

   Check the [`Field` documentation](../fields/#field-aliases) for more information.

1. The AliasChoices class allows to have multiple environment variable names for a single field. The first environment variable that is found will be used.

   Check the [documentation on alias choices](../alias/#aliaspath-and-aliaschoices) for more information.

1. The ImportString class allows to import an object from a string. In this case, the environment variable `special_function` will be read and the function math.cos will be imported.

1. The `env_prefix` config setting allows to set a prefix for all environment variables.

   Check the [Environment variable names documentation](#environment-variable-names) for more information.

## Validation of default values

Unlike pydantic `BaseModel`, default values of `BaseSettings` fields are validated by default. You can disable this behaviour by setting `validate_default=False` either in `model_config` or on field level by `Field(validate_default=False)`:

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(validate_default=False)

    # default won't be validated
    foo: int = 'test'


print(Settings())
#> foo='test'


class Settings1(BaseSettings):
    # default won't be validated
    foo: int = Field('test', validate_default=False)


print(Settings1())
#> foo='test'

```

Check the [validation of default values](../fields/#validate-default-values) for more information.

## Environment variable names

By default, the environment variable name is the same as the field name.

You can change the prefix for all environment variables by setting the `env_prefix` config setting, or via the `_env_prefix` keyword argument on instantiation:

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='my_prefix_')

    auth_key: str = 'xxx'  # will be read from `my_prefix_auth_key`

```

Note

The default `env_prefix` is `''` (empty string). `env_prefix` is not only for env settings but also for dotenv files, secrets, and other sources.

If you want to change the environment variable name for a single field, you can use an alias.

There are two ways to do this:

- Using `Field(alias=...)` (see `api_key` above)
- Using `Field(validation_alias=...)` (see `auth_key` above)

Check the [`Field` aliases documentation](../fields/#field-aliases) for more information about aliases.

`env_prefix` does not apply to fields with alias. It means the environment variable name is the same as field alias:

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='my_prefix_')

    foo: str = Field('xxx', alias='FooAlias')  # (1)!

```

1. `env_prefix` will be ignored and the value will be read from `FooAlias` environment variable.

### Case-sensitivity

By default, environment variable names are case-insensitive.

If you want to make environment variable names case-sensitive, you can set the `case_sensitive` config setting:

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    redis_host: str = 'localhost'

```

When `case_sensitive` is `True`, the environment variable names must match field names (optionally with a prefix), so in this example `redis_host` could only be modified via `export redis_host`. If you want to name environment variables all upper-case, you should name attribute all upper-case too. You can still name environment variables anything you like through `Field(validation_alias=...)`.

Case-sensitivity can also be set via the `_case_sensitive` keyword argument on instantiation.

In case of nested models, the `case_sensitive` setting will be applied to all nested models.

```py
import os

from pydantic import BaseModel, ValidationError

from pydantic_settings import BaseSettings


class RedisSettings(BaseModel):
    host: str
    port: int


class Settings(BaseSettings, case_sensitive=True):
    redis: RedisSettings


os.environ['redis'] = '{"host": "localhost", "port": 6379}'
print(Settings().model_dump())
#> {'redis': {'host': 'localhost', 'port': 6379}}
os.environ['redis'] = '{"HOST": "localhost", "port": 6379}'  # (1)!
try:
    Settings()
except ValidationError as e:
    print(e)
    """
    1 validation error for Settings
    redis.host
      Field required [type=missing, input_value={'HOST': 'localhost', 'port': 6379}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2/v/missing
    """

```

1. Note that the `host` field is not found because the environment variable name is `HOST` (all upper-case).

Note

On Windows, Python's `os` module always treats environment variables as case-insensitive, so the `case_sensitive` config setting will have no effect - settings will always be updated ignoring case.

## Parsing environment variable values

By default environment variables are parsed verbatim, including if the value is empty. You can choose to ignore empty environment variables by setting the `env_ignore_empty` config setting to `True`. This can be useful if you would prefer to use the default value for a field rather than an empty value from the environment.

For most simple field types (such as `int`, `float`, `str`, etc.), the environment variable value is parsed the same way it would be if passed directly to the initialiser (as a string).

Complex types like `list`, `set`, `dict`, and sub-models are populated from the environment by treating the environment variable's value as a JSON-encoded string.

Another way to populate nested complex variables is to configure your model with the `env_nested_delimiter` config setting, then use an environment variable with a name pointing to the nested module fields. What it does is simply explodes your variable into nested models or dicts. So if you define a variable `FOO__BAR__BAZ=123` it will convert it into `FOO={'BAR': {'BAZ': 123}}` If you have multiple variables with the same structure they will be merged.

Note

Sub model has to inherit from `pydantic.BaseModel`, Otherwise `pydantic-settings` will initialize sub model, collects values for sub model fields separately, and you may get unexpected results.

As an example, given the following environment variables:

```bash
# your environment
export V0=0
export SUB_MODEL='{"v1": "json-1", "v2": "json-2"}'
export SUB_MODEL__V2=nested-2
export SUB_MODEL__V3=3
export SUB_MODEL__DEEP__V4=v4

```

You could load them into the following settings model:

```py
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSubModel(BaseModel):  # (1)!
    v4: str


class SubModel(BaseModel):  # (2)!
    v1: str
    v2: bytes
    v3: int
    deep: DeepSubModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')

    v0: str
    sub_model: SubModel


print(Settings().model_dump())
"""
{
    'v0': '0',
    'sub_model': {'v1': 'json-1', 'v2': b'nested-2', 'v3': 3, 'deep': {'v4': 'v4'}},
}
"""

```

1. Sub model has to inherit from `pydantic.BaseModel`.
1. Sub model has to inherit from `pydantic.BaseModel`.

`env_nested_delimiter` can be configured via the `model_config` as shown above, or via the `_env_nested_delimiter` keyword argument on instantiation.

By default environment variables are split by `env_nested_delimiter` into arbitrarily deep nested fields. You can limit the depth of the nested fields with the `env_nested_max_split` config setting. A common use case this is particularly useful is for two-level deep settings, where the `env_nested_delimiter` (usually a single `_`) may be a substring of model field names. For example:

```bash
# your environment
export GENERATION_LLM_PROVIDER='anthropic'
export GENERATION_LLM_API_KEY='your-api-key'
export GENERATION_LLM_API_VERSION='2024-03-15'

```

You could load them into the following settings model:

```py
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    provider: str = 'openai'
    api_key: str
    api_type: str = 'azure'
    api_version: str = '2023-03-15-preview'


class GenerationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='_', env_nested_max_split=1, env_prefix='GENERATION_'
    )

    llm: LLMConfig
    ...


print(GenerationConfig().model_dump())
"""
{
    'llm': {
        'provider': 'anthropic',
        'api_key': 'your-api-key',
        'api_type': 'azure',
        'api_version': '2024-03-15',
    }
}
"""

```

Without `env_nested_max_split=1` set, `GENERATION_LLM_API_KEY` would be parsed as `llm.api.key` instead of `llm.api_key` and it would raise a `ValidationError`.

Nested environment variables take precedence over the top-level environment variable JSON (e.g. in the example above, `SUB_MODEL__V2` trumps `SUB_MODEL`).

You may also populate a complex type by providing your own source class.

```py
import json
import os
from typing import Any

from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class MyCustomSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == 'numbers':
            return [int(x) for x in value.split(',')]
        return json.loads(value)


class Settings(BaseSettings):
    numbers: list[int]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (MyCustomSource(settings_cls),)


os.environ['numbers'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3]}

```

### Disabling JSON parsing

pydantic-settings by default parses complex types from environment variables as JSON strings. If you want to disable this behavior for a field and parse the value in your own validator, you can annotate the field with [`NoDecode`](../../api/pydantic_settings/#pydantic_settings.NoDecode):

```py
import os
from typing import Annotated

from pydantic import field_validator

from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    numbers: Annotated[list[int], NoDecode]  # (1)!

    @field_validator('numbers', mode='before')
    @classmethod
    def decode_numbers(cls, v: str) -> list[int]:
        return [int(x) for x in v.split(',')]


os.environ['numbers'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3]}

```

1. The `NoDecode` annotation disables JSON parsing for the `numbers` field. The `decode_numbers` field validator will be called to parse the value.

You can also disable JSON parsing for all fields by setting the `enable_decoding` config setting to `False`:

```py
import os

from pydantic import field_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(enable_decoding=False)

    numbers: list[int]

    @field_validator('numbers', mode='before')
    @classmethod
    def decode_numbers(cls, v: str) -> list[int]:
        return [int(x) for x in v.split(',')]


os.environ['numbers'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3]}

```

You can force JSON parsing for a field by annotating it with [`ForceDecode`](../../api/pydantic_settings/#pydantic_settings.ForceDecode). This will bypass the `enable_decoding` config setting:

```py
import os
from typing import Annotated

from pydantic import field_validator

from pydantic_settings import BaseSettings, ForceDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(enable_decoding=False)

    numbers: Annotated[list[int], ForceDecode]
    numbers1: list[int]  # (1)!

    @field_validator('numbers1', mode='before')
    @classmethod
    def decode_numbers1(cls, v: str) -> list[int]:
        return [int(x) for x in v.split(',')]


os.environ['numbers'] = '["1","2","3"]'
os.environ['numbers1'] = '1,2,3'
print(Settings().model_dump())
#> {'numbers': [1, 2, 3], 'numbers1': [1, 2, 3]}

```

1. The `numbers1` field is not annotated with `ForceDecode`, so it will not be parsed as JSON. and we have to provide a custom validator to parse the value.

## Nested model default partial updates

By default, Pydantic settings does not allow partial updates to nested model default objects. This behavior can be overriden by setting the `nested_model_default_partial_update` flag to `True`, which will allow partial updates on nested model default object fields.

```py
import os

from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class SubModel(BaseModel):
    val: int = 0
    flag: bool = False


class SettingsPartialUpdate(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__', nested_model_default_partial_update=True
    )

    nested_model: SubModel = SubModel(val=1)


class SettingsNoPartialUpdate(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__', nested_model_default_partial_update=False
    )

    nested_model: SubModel = SubModel(val=1)


# Apply a partial update to the default object using environment variables
os.environ['NESTED_MODEL__FLAG'] = 'True'

# When partial update is enabled, the existing SubModel instance is updated
# with nested_model.flag=True change
assert SettingsPartialUpdate().model_dump() == {
    'nested_model': {'val': 1, 'flag': True}
}

# When partial update is disabled, a new SubModel instance is instantiated
# with nested_model.flag=True change
assert SettingsNoPartialUpdate().model_dump() == {
    'nested_model': {'val': 0, 'flag': True}
}

```

## Dotenv (.env) support

Dotenv files (generally named `.env`) are a common pattern that make it easy to use environment variables in a platform-independent manner.

A dotenv file follows the same general principles of all environment variables, and it looks like this:

.env

```bash
# ignore comment
ENVIRONMENT="production"
REDIS_ADDRESS=localhost:6379
MEANING_OF_LIFE=42
MY_VAR='Hello world'

```

Once you have your `.env` file filled with variables, *pydantic* supports loading it in two ways:

1. Setting the `env_file` (and `env_file_encoding` if you don't want the default encoding of your OS) on `model_config` in the `BaseSettings` class:

   ```py
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

   ```

1. Instantiating the `BaseSettings` derived class with the `_env_file` keyword argument (and the `_env_file_encoding` if needed):

   ```py
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


   settings = Settings(_env_file='prod.env', _env_file_encoding='utf-8')

   ```

   In either case, the value of the passed argument can be any valid path or filename, either absolute or relative to the current working directory. From there, *pydantic* will handle everything for you by loading in your variables and validating them.

Note

If a filename is specified for `env_file`, Pydantic will only check the current working directory and won't check any parent directories for the `.env` file.

Even when using a dotenv file, *pydantic* will still read environment variables as well as the dotenv file, **environment variables will always take priority over values loaded from a dotenv file**.

Passing a file path via the `_env_file` keyword argument on instantiation (method 2) will override the value (if any) set on the `model_config` class. If the above snippets were used in conjunction, `prod.env` would be loaded while `.env` would be ignored.

If you need to load multiple dotenv files, you can pass multiple file paths as a tuple or list. The files will be loaded in order, with each file overriding the previous one.

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=('.env', '.env.prod')
    )

```

You can also use the keyword argument override to tell Pydantic not to load any file at all (even if one is set in the `model_config` class) by passing `None` as the instantiation keyword argument, e.g. `settings = Settings(_env_file=None)`.

Because python-dotenv is used to parse the file, bash-like semantics such as `export` can be used which (depending on your OS and environment) may allow your dotenv file to also be used with `source`, see [python-dotenv's documentation](https://saurabh-kumar.com/python-dotenv/#usages) for more details.

Pydantic settings consider `extra` config in case of dotenv file. It means if you set the `extra=forbid` (*default*) on `model_config` and your dotenv file contains an entry for a field that is not defined in settings model, it will raise `ValidationError` in settings construction.

For compatibility with pydantic 1.x BaseSettings you should use `extra=ignore`:

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

```

Note

Pydantic settings loads all the values from dotenv file and passes it to the model, regardless of the model's `env_prefix`. So if you provide extra values in a dotenv file, whether they start with `env_prefix` or not, a `ValidationError` will be raised.

## Command Line Support

Pydantic settings provides integrated CLI support, making it easy to quickly define CLI applications using Pydantic models. There are two primary use cases for Pydantic settings CLI:

1. When using a CLI to override fields in Pydantic models.
1. When using Pydantic models to define CLIs.

By default, the experience is tailored towards use case #1 and builds on the foundations established in [parsing environment variables](#parsing-environment-variable-values). If your use case primarily falls into #2, you will likely want to enable most of the defaults outlined at the end of [creating CLI applications](#creating-cli-applications).

### The Basics

To get started, let's revisit the example presented in [parsing environment variables](#parsing-environment-variable-values) but using a Pydantic settings CLI:

```py
import sys

from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSubModel(BaseModel):
    v4: str


class SubModel(BaseModel):
    v1: str
    v2: bytes
    v3: int
    deep: DeepSubModel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(cli_parse_args=True)

    v0: str
    sub_model: SubModel


sys.argv = [
    'example.py',
    '--v0=0',
    '--sub_model={"v1": "json-1", "v2": "json-2"}',
    '--sub_model.v2=nested-2',
    '--sub_model.v3=3',
    '--sub_model.deep.v4=v4',
]

print(Settings().model_dump())
"""
{
    'v0': '0',
    'sub_model': {'v1': 'json-1', 'v2': b'nested-2', 'v3': 3, 'deep': {'v4': 'v4'}},
}
"""

```

To enable CLI parsing, we simply set the `cli_parse_args` flag to a valid value, which retains similar connotations as defined in `argparse`.

Note that a CLI settings source is [**the topmost source**](#field-value-priority) by default unless its [priority value is customised](#customise-settings-sources):

```py
import os
import sys

from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
)


class Settings(BaseSettings):
    my_foo: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, CliSettingsSource(settings_cls, cli_parse_args=True)


os.environ['MY_FOO'] = 'from environment'

sys.argv = ['example.py', '--my_foo=from cli']

print(Settings().model_dump())
#> {'my_foo': 'from environment'}

```

#### Lists

CLI argument parsing of lists supports intermixing of any of the below three styles:

- JSON style `--field='[1,2]'`
- Argparse style `--field 1 --field 2`
- Lazy style `--field=1,2`

```py
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True):
    my_list: list[int]


sys.argv = ['example.py', '--my_list', '[1,2]']
print(Settings().model_dump())
#> {'my_list': [1, 2]}

sys.argv = ['example.py', '--my_list', '1', '--my_list', '2']
print(Settings().model_dump())
#> {'my_list': [1, 2]}

sys.argv = ['example.py', '--my_list', '1,2']
print(Settings().model_dump())
#> {'my_list': [1, 2]}

```

#### Dictionaries

CLI argument parsing of dictionaries supports intermixing of any of the below two styles:

- JSON style `--field='{"k1": 1, "k2": 2}'`
- Environment variable style `--field k1=1 --field k2=2`

These can be used in conjunction with list forms as well, e.g:

- `--field k1=1,k2=2 --field k3=3 --field '{"k4": 4}'` etc.

```py
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True):
    my_dict: dict[str, int]


sys.argv = ['example.py', '--my_dict', '{"k1":1,"k2":2}']
print(Settings().model_dump())
#> {'my_dict': {'k1': 1, 'k2': 2}}

sys.argv = ['example.py', '--my_dict', 'k1=1', '--my_dict', 'k2=2']
print(Settings().model_dump())
#> {'my_dict': {'k1': 1, 'k2': 2}}

```

#### Literals and Enums

CLI argument parsing of literals and enums are converted into CLI choices.

```py
import sys
from enum import IntEnum
from typing import Literal

from pydantic_settings import BaseSettings


class Fruit(IntEnum):
    pear = 0
    kiwi = 1
    lime = 2


class Settings(BaseSettings, cli_parse_args=True):
    fruit: Fruit
    pet: Literal['dog', 'cat', 'bird']


sys.argv = ['example.py', '--fruit', 'lime', '--pet', 'cat']
print(Settings().model_dump())
#> {'fruit': <Fruit.lime: 2>, 'pet': 'cat'}

```

#### Aliases

Pydantic field aliases are added as CLI argument aliases. Aliases of length one are converted into short options.

```py
import sys

from pydantic import AliasChoices, AliasPath, Field

from pydantic_settings import BaseSettings


class User(BaseSettings, cli_parse_args=True):
    first_name: str = Field(
        validation_alias=AliasChoices('f', 'fname', AliasPath('name', 0))
    )
    last_name: str = Field(
        validation_alias=AliasChoices('l', 'lname', AliasPath('name', 1))
    )


sys.argv = ['example.py', '--fname', 'John', '--lname', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '-f', 'John', '-l', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '--name', 'John,Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

sys.argv = ['example.py', '--name', 'John', '--lname', 'Doe']
print(User().model_dump())
#> {'first_name': 'John', 'last_name': 'Doe'}

```

### Subcommands and Positional Arguments

Subcommands and positional arguments are expressed using the `CliSubCommand` and `CliPositionalArg` annotations. The subcommand annotation can only be applied to required fields (i.e. fields that do not have a default value). Furthermore, subcommands must be a valid type derived from either a pydantic `BaseModel` or pydantic.dataclasses `dataclass`.

Parsed subcommands can be retrieved from model instances using the `get_subcommand` utility function. If a subcommand is not required, set the `is_required` flag to `False` to disable raising an error if no subcommand is found.

Note

CLI settings subcommands are limited to a single subparser per model. In other words, all subcommands for a model are grouped under a single subparser; it does not allow for multiple subparsers with each subparser having its own set of subcommands. For more information on subparsers, see [argparse subcommands](https://docs.python.org/3/library/argparse.html#sub-commands).

Note

`CliSubCommand` and `CliPositionalArg` are always case sensitive.

```py
import sys

from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    CliPositionalArg,
    CliSubCommand,
    SettingsError,
    get_subcommand,
)


class Init(BaseModel):
    directory: CliPositionalArg[str]


class Clone(BaseModel):
    repository: CliPositionalArg[str]
    directory: CliPositionalArg[str]


class Git(BaseSettings, cli_parse_args=True, cli_exit_on_error=False):
    clone: CliSubCommand[Clone]
    init: CliSubCommand[Init]


# Run without subcommands
sys.argv = ['example.py']
cmd = Git()
assert cmd.model_dump() == {'clone': None, 'init': None}

try:
    # Will raise an error since no subcommand was provided
    get_subcommand(cmd).model_dump()
except SettingsError as err:
    assert str(err) == 'Error: CLI subcommand is required {clone, init}'

# Will not raise an error since subcommand is not required
assert get_subcommand(cmd, is_required=False) is None


# Run the clone subcommand
sys.argv = ['example.py', 'clone', 'repo', 'dest']
cmd = Git()
assert cmd.model_dump() == {
    'clone': {'repository': 'repo', 'directory': 'dest'},
    'init': None,
}

# Returns the subcommand model instance (in this case, 'clone')
assert get_subcommand(cmd).model_dump() == {
    'directory': 'dest',
    'repository': 'repo',
}

```

The `CliSubCommand` and `CliPositionalArg` annotations also support union operations and aliases. For unions of Pydantic models, it is important to remember the [nuances](https://docs.pydantic.dev/latest/concepts/unions/) that can arise during validation. Specifically, for unions of subcommands that are identical in content, it is recommended to break them out into separate `CliSubCommand` fields to avoid any complications. Lastly, the derived subcommand names from unions will be the names of the Pydantic model classes themselves.

When assigning aliases to `CliSubCommand` or `CliPositionalArg` fields, only a single alias can be assigned. For non-union subcommands, aliasing will change the displayed help text and subcommand name. Conversely, for union subcommands, aliasing will have no tangible effect from the perspective of the CLI settings source. Lastly, for positional arguments, aliasing will change the CLI help text displayed for the field.

```py
import sys
from typing import Union

from pydantic import BaseModel, Field

from pydantic_settings import (
    BaseSettings,
    CliPositionalArg,
    CliSubCommand,
    get_subcommand,
)


class Alpha(BaseModel):
    """Apha Help"""

    cmd_alpha: CliPositionalArg[str] = Field(alias='alpha-cmd')


class Beta(BaseModel):
    """Beta Help"""

    opt_beta: str = Field(alias='opt-beta')


class Gamma(BaseModel):
    """Gamma Help"""

    opt_gamma: str = Field(alias='opt-gamma')


class Root(BaseSettings, cli_parse_args=True, cli_exit_on_error=False):
    alpha_or_beta: CliSubCommand[Union[Alpha, Beta]] = Field(alias='alpha-or-beta-cmd')
    gamma: CliSubCommand[Gamma] = Field(alias='gamma-cmd')


sys.argv = ['example.py', 'Alpha', 'hello']
assert get_subcommand(Root()).model_dump() == {'cmd_alpha': 'hello'}

sys.argv = ['example.py', 'Beta', '--opt-beta=hey']
assert get_subcommand(Root()).model_dump() == {'opt_beta': 'hey'}

sys.argv = ['example.py', 'gamma-cmd', '--opt-gamma=hi']
assert get_subcommand(Root()).model_dump() == {'opt_gamma': 'hi'}

```

### Creating CLI Applications

The `CliApp` class provides two utility methods, `CliApp.run` and `CliApp.run_subcommand`, that can be used to run a Pydantic `BaseSettings`, `BaseModel`, or `pydantic.dataclasses.dataclass` as a CLI application. Primarily, the methods provide structure for running `cli_cmd` methods associated with models.

`CliApp.run` can be used in directly providing the `cli_args` to be parsed, and will run the model `cli_cmd` method (if defined) after instantiation:

```py
from pydantic_settings import BaseSettings, CliApp


class Settings(BaseSettings):
    this_foo: str

    def cli_cmd(self) -> None:
        # Print the parsed data
        print(self.model_dump())
        #> {'this_foo': 'is such a foo'}

        # Update the parsed data showing cli_cmd ran
        self.this_foo = 'ran the foo cli cmd'


s = CliApp.run(Settings, cli_args=['--this_foo', 'is such a foo'])
print(s.model_dump())
#> {'this_foo': 'ran the foo cli cmd'}

```

Similarly, the `CliApp.run_subcommand` can be used in recursive fashion to run the `cli_cmd` method of a subcommand:

```py
from pydantic import BaseModel

from pydantic_settings import CliApp, CliPositionalArg, CliSubCommand


class Init(BaseModel):
    directory: CliPositionalArg[str]

    def cli_cmd(self) -> None:
        print(f'git init "{self.directory}"')
        #> git init "dir"
        self.directory = 'ran the git init cli cmd'


class Clone(BaseModel):
    repository: CliPositionalArg[str]
    directory: CliPositionalArg[str]

    def cli_cmd(self) -> None:
        print(f'git clone from "{self.repository}" into "{self.directory}"')
        self.directory = 'ran the clone cli cmd'


class Git(BaseModel):
    clone: CliSubCommand[Clone]
    init: CliSubCommand[Init]

    def cli_cmd(self) -> None:
        CliApp.run_subcommand(self)


cmd = CliApp.run(Git, cli_args=['init', 'dir'])
assert cmd.model_dump() == {
    'clone': None,
    'init': {'directory': 'ran the git init cli cmd'},
}

```

Note

Unlike `CliApp.run`, `CliApp.run_subcommand` requires the subcommand model to have a defined `cli_cmd` method.

For `BaseModel` and `pydantic.dataclasses.dataclass` types, `CliApp.run` will internally use the following `BaseSettings` configuration defaults:

- `nested_model_default_partial_update=True`
- `case_sensitive=True`
- `cli_hide_none_type=True`
- `cli_avoid_json=True`
- `cli_enforce_required=True`
- `cli_implicit_flags=True`
- `cli_kebab_case=True`

### Asynchronous CLI Commands

Pydantic settings supports running asynchronous CLI commands via `CliApp.run` and `CliApp.run_subcommand`. With this feature, you can define async def methods within your Pydantic models (including subcommands) and have them executed just like their synchronous counterparts. Specifically:

1. Asynchronous methods are supported: You can now mark your cli_cmd or similar CLI entrypoint methods as async def and have CliApp execute them.
1. Subcommands may also be asynchronous: If you have nested CLI subcommands, the final (lowest-level) subcommand methods can likewise be asynchronous.
1. Limit asynchronous methods to final subcommands: Defining parent commands as asynchronous is not recommended, because it can result in additional threads and event loops being created. For best performance and to avoid unnecessary resource usage, only implement your deepest (child) subcommands as async def.

Below is a simple example demonstrating an asynchronous top-level command:

```py
from pydantic_settings import BaseSettings, CliApp


class AsyncSettings(BaseSettings):
    async def cli_cmd(self) -> None:
        print('Hello from an async CLI method!')
        #> Hello from an async CLI method!


# If an event loop is already running, a new thread will be used;
# otherwise, asyncio.run() is used to execute this async method.
assert CliApp.run(AsyncSettings, cli_args=[]).model_dump() == {}

```

#### Asynchronous Subcommands

As mentioned above, you can also define subcommands as async. However, only do so for the leaf (lowest-level) subcommand to avoid spawning new threads and event loops unnecessarily in parent commands:

```py
from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliPositionalArg,
    CliSubCommand,
)


class Clone(BaseModel):
    repository: CliPositionalArg[str]
    directory: CliPositionalArg[str]

    async def cli_cmd(self) -> None:
        # Perform async tasks here, e.g. network or I/O operations
        print(f'Cloning async from "{self.repository}" into "{self.directory}"')
        #> Cloning async from "repo" into "dir"


class Git(BaseSettings):
    clone: CliSubCommand[Clone]

    def cli_cmd(self) -> None:
        # Run the final subcommand (clone/init). It is recommended to define async methods only at the deepest level.
        CliApp.run_subcommand(self)


CliApp.run(Git, cli_args=['clone', 'repo', 'dir']).model_dump() == {
    'repository': 'repo',
    'directory': 'dir',
}

```

When executing a subcommand with an asynchronous cli_cmd, Pydantic settings automatically detects whether the current thread already has an active event loop. If so, the async command is run in a fresh thread to avoid conflicts. Otherwise, it uses asyncio.run() in the current thread. This handling ensures your asynchronous subcommands "just work" without additional manual setup.

### Serializing CLI Arguments

An instantiated Pydantic model can be serialized into its CLI arguments using the `CliApp.serialize` method.

```py
from pydantic import BaseModel

from pydantic_settings import CliApp


class Nested(BaseModel):
    that: int


class Settings(BaseModel):
    this: str
    nested: Nested


print(CliApp.serialize(Settings(this='hello', nested=Nested(that=123))))
#> ['--this', 'hello', '--nested.that', '123']

```

### Mutually Exclusive Groups

CLI mutually exclusive groups can be created by inheriting from the `CliMutuallyExclusiveGroup` class.

Note

A `CliMutuallyExclusiveGroup` cannot be used in a union or contain nested models.

```py
from typing import Optional

from pydantic import BaseModel

from pydantic_settings import CliApp, CliMutuallyExclusiveGroup, SettingsError


class Circle(CliMutuallyExclusiveGroup):
    radius: Optional[float] = None
    diameter: Optional[float] = None
    perimeter: Optional[float] = None


class Settings(BaseModel):
    circle: Circle


try:
    CliApp.run(
        Settings,
        cli_args=['--circle.radius=1', '--circle.diameter=2'],
        cli_exit_on_error=False,
    )
except SettingsError as e:
    print(e)
    """
    error parsing CLI: argument --circle.diameter: not allowed with argument --circle.radius
    """

```

### Customizing the CLI Experience

The below flags can be used to customise the CLI experience to your needs.

#### Change the Displayed Program Name

Change the default program name displayed in the help text usage by setting `cli_prog_name`. By default, it will derive the name of the currently executing program from `sys.argv[0]`, just like argparse.

```py
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_prog_name='appdantic'):
    pass


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: appdantic [-h]

options:
  -h, --help  show this help message and exit
"""

```

#### CLI Boolean Flags

Change whether boolean fields should be explicit or implicit by default using the `cli_implicit_flags` setting. By default, boolean fields are "explicit", meaning a boolean value must be explicitly provided on the CLI, e.g. `--flag=True`. Conversely, boolean fields that are "implicit" derive the value from the flag itself, e.g. `--flag,--no-flag`, which removes the need for an explicit value to be passed.

Additionally, the provided `CliImplicitFlag` and `CliExplicitFlag` annotations can be used for more granular control when necessary.

```py
from pydantic_settings import BaseSettings, CliExplicitFlag, CliImplicitFlag


class ExplicitSettings(BaseSettings, cli_parse_args=True):
    """Boolean fields are explicit by default."""

    explicit_req: bool
    """
    --explicit_req bool   (required)
    """

    explicit_opt: bool = False
    """
    --explicit_opt bool   (default: False)
    """

    # Booleans are explicit by default, so must override implicit flags with annotation
    implicit_req: CliImplicitFlag[bool]
    """
    --implicit_req, --no-implicit_req (required)
    """

    implicit_opt: CliImplicitFlag[bool] = False
    """
    --implicit_opt, --no-implicit_opt (default: False)
    """


class ImplicitSettings(BaseSettings, cli_parse_args=True, cli_implicit_flags=True):
    """With cli_implicit_flags=True, boolean fields are implicit by default."""

    # Booleans are implicit by default, so must override explicit flags with annotation
    explicit_req: CliExplicitFlag[bool]
    """
    --explicit_req bool   (required)
    """

    explicit_opt: CliExplicitFlag[bool] = False
    """
    --explicit_opt bool   (default: False)
    """

    implicit_req: bool
    """
    --implicit_req, --no-implicit_req (required)
    """

    implicit_opt: bool = False
    """
    --implicit_opt, --no-implicit_opt (default: False)
    """

```

#### Ignore and Retrieve Unknown Arguments

Change whether to ignore unknown CLI arguments and only parse known ones using `cli_ignore_unknown_args`. By default, the CLI does not ignore any args. Ignored arguments can then be retrieved using the `CliUnknownArgs` annotation.

```py
import sys

from pydantic_settings import BaseSettings, CliUnknownArgs


class Settings(BaseSettings, cli_parse_args=True, cli_ignore_unknown_args=True):
    good_arg: str
    ignored_args: CliUnknownArgs


sys.argv = ['example.py', '--bad-arg=bad', 'ANOTHER_BAD_ARG', '--good_arg=hello world']
print(Settings().model_dump())
#> {'good_arg': 'hello world', 'ignored_args': ['--bad-arg=bad', 'ANOTHER_BAD_ARG']}

```

#### CLI Kebab Case for Arguments

Change whether CLI arguments should use kebab case by enabling `cli_kebab_case`. By default, `cli_kebab_case=True` will ignore enum fields, and is equivalent to `cli_kebab_case='no_enums'`. To apply kebab case to everything, including enums, use `cli_kebab_case='all'`.

```py
import sys

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_kebab_case=True):
    my_option: str = Field(description='will show as kebab case on CLI')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--my-option str]

options:
  -h, --help       show this help message and exit
  --my-option str  will show as kebab case on CLI (required)
"""

```

#### Change Whether CLI Should Exit on Error

Change whether the CLI internal parser will exit on error or raise a `SettingsError` exception by using `cli_exit_on_error`. By default, the CLI internal parser will exit on error.

```py
import sys

from pydantic_settings import BaseSettings, SettingsError


class Settings(BaseSettings, cli_parse_args=True, cli_exit_on_error=False): ...


try:
    sys.argv = ['example.py', '--bad-arg']
    Settings()
except SettingsError as e:
    print(e)
    #> error parsing CLI: unrecognized arguments: --bad-arg

```

#### Enforce Required Arguments at CLI

Pydantic settings is designed to pull values in from various sources when instantating a model. This means a field that is required is not strictly required from any single source (e.g. the CLI). Instead, all that matters is that one of the sources provides the required value.

However, if your use case [aligns more with #2](#command-line-support), using Pydantic models to define CLIs, you will likely want required fields to be *strictly required at the CLI*. We can enable this behavior by using `cli_enforce_required`.

Note

A required `CliPositionalArg` field is always strictly required (enforced) at the CLI.

```py
import os
import sys

from pydantic import Field

from pydantic_settings import BaseSettings, SettingsError


class Settings(
    BaseSettings,
    cli_parse_args=True,
    cli_enforce_required=True,
    cli_exit_on_error=False,
):
    my_required_field: str = Field(description='a top level required field')


os.environ['MY_REQUIRED_FIELD'] = 'hello from environment'

try:
    sys.argv = ['example.py']
    Settings()
except SettingsError as e:
    print(e)
    #> error parsing CLI: the following arguments are required: --my_required_field

```

#### Change the None Type Parse String

Change the CLI string value that will be parsed (e.g. "null", "void", "None", etc.) into `None` by setting `cli_parse_none_str`. By default it will use the `env_parse_none_str` value if set. Otherwise, it will default to "null" if `cli_avoid_json` is `False`, and "None" if `cli_avoid_json` is `True`.

```py
import sys
from typing import Optional

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_parse_none_str='void'):
    v1: Optional[int] = Field(description='the top level v0 option')


sys.argv = ['example.py', '--v1', 'void']
print(Settings().model_dump())
#> {'v1': None}

```

#### Hide None Type Values

Hide `None` values from the CLI help text by enabling `cli_hide_none_type`.

```py
import sys
from typing import Optional

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_hide_none_type=True):
    v0: Optional[str] = Field(description='the top level v0 option')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--v0 str]

options:
  -h, --help  show this help message and exit
  --v0 str    the top level v0 option (required)
"""

```

#### Avoid Adding JSON CLI Options

Avoid adding complex fields that result in JSON strings at the CLI by enabling `cli_avoid_json`.

```py
import sys

from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings


class SubModel(BaseModel):
    v1: int = Field(description='the sub model v1 option')


class Settings(BaseSettings, cli_parse_args=True, cli_avoid_json=True):
    sub_model: SubModel = Field(
        description='The help summary for SubModel related options'
    )


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--sub_model.v1 int]

options:
  -h, --help          show this help message and exit

sub_model options:
  The help summary for SubModel related options

  --sub_model.v1 int  the sub model v1 option (required)
"""

```

#### Use Class Docstring for Group Help Text

By default, when populating the group help text for nested models it will pull from the field descriptions. Alternatively, we can also configure CLI settings to pull from the class docstring instead.

Note

If the field is a union of nested models the group help text will always be pulled from the field description; even if `cli_use_class_docs_for_groups` is set to `True`.

```py
import sys

from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings


class SubModel(BaseModel):
    """The help text from the class docstring."""

    v1: int = Field(description='the sub model v1 option')


class Settings(BaseSettings, cli_parse_args=True, cli_use_class_docs_for_groups=True):
    """My application help text."""

    sub_model: SubModel = Field(description='The help text from the field description')


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h] [--sub_model JSON] [--sub_model.v1 int]

My application help text.

options:
  -h, --help          show this help message and exit

sub_model options:
  The help text from the class docstring.

  --sub_model JSON    set sub_model from JSON string
  --sub_model.v1 int  the sub model v1 option (required)
"""

```

#### Change the CLI Flag Prefix Character

Change The CLI flag prefix character used in CLI optional arguments by settings `cli_flag_prefix_char`.

```py
import sys

from pydantic import AliasChoices, Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings, cli_parse_args=True, cli_flag_prefix_char='+'):
    my_arg: str = Field(validation_alias=AliasChoices('m', 'my-arg'))


sys.argv = ['example.py', '++my-arg', 'hi']
print(Settings().model_dump())
#> {'my_arg': 'hi'}

sys.argv = ['example.py', '+m', 'hi']
print(Settings().model_dump())
#> {'my_arg': 'hi'}

```

#### Suppressing Fields from CLI Help Text

To suppress a field from the CLI help text, the `CliSuppress` annotation can be used for field types, or the `CLI_SUPPRESS` string constant can be used for field descriptions.

```py
import sys

from pydantic import Field

from pydantic_settings import CLI_SUPPRESS, BaseSettings, CliSuppress


class Settings(BaseSettings, cli_parse_args=True):
    """Suppress fields from CLI help text."""

    field_a: CliSuppress[int] = 0
    field_b: str = Field(default=1, description=CLI_SUPPRESS)


try:
    sys.argv = ['example.py', '--help']
    Settings()
except SystemExit as e:
    print(e)
    #> 0
"""
usage: example.py [-h]

Suppress fields from CLI help text.

options:
  -h, --help          show this help message and exit
"""

```

#### CLI Shortcuts for Arguments

Add alternative CLI argument names (shortcuts) for fields using the `cli_shortcuts` option in `SettingsConfigDict`. This allows you to define additional names for CLI arguments, which can be especially useful for providing more user-friendly or shorter aliases for deeply nested or verbose field names.

The `cli_shortcuts` option takes a dictionary mapping the target field name (using dot notation for nested fields) to one or more shortcut names. If multiple fields share the same shortcut, the first matching field will take precedence.

**Flat Example:**

```py
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    option: str = Field(default='foo')
    list_option: str = Field(default='fizz')

    model_config = SettingsConfigDict(
        cli_shortcuts={'option': 'option2', 'list_option': ['list_option2']}
    )


# Now you can use the shortcuts on the CLI:
# --option2 sets 'option', --list_option2 sets 'list_option'

```

**Nested Example:**

```py
from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class TwiceNested(BaseModel):
    option: str = Field(default='foo')


class Nested(BaseModel):
    twice_nested_option: TwiceNested = TwiceNested()
    option: str = Field(default='foo')


class Settings(BaseSettings):
    nested: Nested = Nested()
    model_config = SettingsConfigDict(
        cli_shortcuts={
            'nested.option': 'option2',
            'nested.twice_nested_option.option': 'twice_nested_option',
        }
    )


# Now you can use --option2 to set nested.option and --twice_nested_option to set nested.twice_nested_option.option

```

If a shortcut collides (is mapped to multiple fields), it will apply to the first matching field in the model.

### Integrating with Existing Parsers

A CLI settings source can be integrated with existing parsers by overriding the default CLI settings source with a user defined one that specifies the `root_parser` object.

```py
import sys
from argparse import ArgumentParser

from pydantic_settings import BaseSettings, CliApp, CliSettingsSource

parser = ArgumentParser()
parser.add_argument('--food', choices=['pear', 'kiwi', 'lime'])


class Settings(BaseSettings):
    name: str = 'Bob'


# Set existing `parser` as the `root_parser` object for the user defined settings source
cli_settings = CliSettingsSource(Settings, root_parser=parser)

# Parse and load CLI settings from the command line into the settings source.
sys.argv = ['example.py', '--food', 'kiwi', '--name', 'waldo']
s = CliApp.run(Settings, cli_settings_source=cli_settings)
print(s.model_dump())
#> {'name': 'waldo'}

# Load CLI settings from pre-parsed arguments. i.e., the parsing occurs elsewhere and we
# just need to load the pre-parsed args into the settings source.
parsed_args = parser.parse_args(['--food', 'kiwi', '--name', 'ralph'])
s = CliApp.run(Settings, cli_args=parsed_args, cli_settings_source=cli_settings)
print(s.model_dump())
#> {'name': 'ralph'}

```

A `CliSettingsSource` connects with a `root_parser` object by using parser methods to add `settings_cls` fields as command line arguments. The `CliSettingsSource` internal parser representation is based on the `argparse` library, and therefore, requires parser methods that support the same attributes as their `argparse` counterparts. The available parser methods that can be customised, along with their argparse counterparts (the defaults), are listed below:

- `parse_args_method` - (`argparse.ArgumentParser.parse_args`)
- `add_argument_method` - (`argparse.ArgumentParser.add_argument`)
- `add_argument_group_method` - (`argparse.ArgumentParser.add_argument_group`)
- `add_parser_method` - (`argparse._SubParsersAction.add_parser`)
- `add_subparsers_method` - (`argparse.ArgumentParser.add_subparsers`)
- `formatter_class` - (`argparse.RawDescriptionHelpFormatter`)

For a non-argparse parser the parser methods can be set to `None` if not supported. The CLI settings will only raise an error when connecting to the root parser if a parser method is necessary but set to `None`.

Note

The `formatter_class` is only applied to subcommands. The `CliSettingsSource` never touches or modifies any of the external parser settings to avoid breaking changes. Since subcommands reside on their own internal parser trees, we can safely apply the `formatter_class` settings without breaking the external parser logic.

## Secrets

Placing secret values in files is a common pattern to provide sensitive configuration to an application.

A secret file follows the same principal as a dotenv file except it only contains a single value and the file name is used as the key. A secret file will look like the following:

/var/run/database_password

```text
super_secret_database_password

```

Once you have your secret files, *pydantic* supports loading it in two ways:

1. Setting the `secrets_dir` on `model_config` in a `BaseSettings` class to the directory where your secret files are stored.

   ```py
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
       model_config = SettingsConfigDict(secrets_dir='/var/run')

       database_password: str

   ```

1. Instantiating the `BaseSettings` derived class with the `_secrets_dir` keyword argument:

   ```text
   settings = Settings(_secrets_dir='/var/run')

   ```

In either case, the value of the passed argument can be any valid directory, either absolute or relative to the current working directory. **Note that a non existent directory will only generate a warning**. From there, *pydantic* will handle everything for you by loading in your variables and validating them.

Even when using a secrets directory, *pydantic* will still read environment variables from a dotenv file or the environment, **a dotenv file and environment variables will always take priority over values loaded from the secrets directory**.

Passing a file path via the `_secrets_dir` keyword argument on instantiation (method 2) will override the value (if any) set on the `model_config` class.

If you need to load settings from multiple secrets directories, you can pass multiple paths as a tuple or list. Just like for `env_file`, values from subsequent paths override previous ones.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # files in '/run/secrets' take priority over '/var/run'
    model_config = SettingsConfigDict(secrets_dir=('/var/run', '/run/secrets'))

    database_password: str

```

If any of `secrets_dir` is missing, it is ignored, and warning is shown. If any of `secrets_dir` is a file, error is raised.

### Use Case: Docker Secrets

Docker Secrets can be used to provide sensitive configuration to an application running in a Docker container. To use these secrets in a *pydantic* application the process is simple. More information regarding creating, managing and using secrets in Docker see the official [Docker documentation](https://docs.docker.com/engine/reference/commandline/secret/).

First, define your `Settings` class with a `SettingsConfigDict` that specifies the secrets directory.

```py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(secrets_dir='/run/secrets')

    my_secret_data: str

```

Note

By default [Docker uses `/run/secrets`](https://docs.docker.com/engine/swarm/secrets/#how-docker-manages-secrets) as the target mount point. If you want to use a different location, change `Config.secrets_dir` accordingly.

Then, create your secret via the Docker CLI

```bash
printf "This is a secret" | docker secret create my_secret_data -

```

Last, run your application inside a Docker container and supply your newly created secret

```bash
docker service create --name pydantic-with-secrets --secret my_secret_data pydantic-app:latest

```

## AWS Secrets Manager

You must set one parameter:

- `secret_id`: The AWS secret id

You must have the same naming convention in the key value in secret as in the field name. For example, if the key in secret is named `SqlServerPassword`, the field name must be the same. You can use an alias too.

In AWS Secrets Manager, nested models are supported with the `--` separator in the key name. For example, `SqlServer--Password`.

Arrays (e.g. `MySecret--0`, `MySecret--1`) are not supported.

```py
import os

from pydantic import BaseModel

from pydantic_settings import (
    AWSSecretsManagerSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class SubModel(BaseModel):
    a: str


class AWSSecretsManagerSettings(BaseSettings):
    foo: str
    bar: int
    sub: SubModel

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        aws_secrets_manager_settings = AWSSecretsManagerSettingsSource(
            settings_cls,
            os.environ['AWS_SECRETS_MANAGER_SECRET_ID'],
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            aws_secrets_manager_settings,
        )

```

## Azure Key Vault

You must set two parameters:

- `url`: For example, `https://my-resource.vault.azure.net/`.
- `credential`: If you use `DefaultAzureCredential`, in local you can execute `az login` to get your identity credentials. The identity must have a role assignment (the recommended one is `Key Vault Secrets User`), so you can access the secrets.

You must have the same naming convention in the field name as in the Key Vault secret name. For example, if the secret is named `SqlServerPassword`, the field name must be the same. You can use an alias too.

In Key Vault, nested models are supported with the `--` separator. For example, `SqlServer--Password`.

Key Vault arrays (e.g. `MySecret--0`, `MySecret--1`) are not supported.

```py
import os

from azure.identity import DefaultAzureCredential
from pydantic import BaseModel

from pydantic_settings import (
    AzureKeyVaultSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class SubModel(BaseModel):
    a: str


class AzureKeyVaultSettings(BaseSettings):
    foo: str
    bar: int
    sub: SubModel

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        az_key_vault_settings = AzureKeyVaultSettingsSource(
            settings_cls,
            os.environ['AZURE_KEY_VAULT_URL'],
            DefaultAzureCredential(),
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            az_key_vault_settings,
        )

```

### Snake case conversion

The Azure Key Vault source accepts a `snake_case_convertion` option, disabled by default, to convert Key Vault secret names by mapping them to Python's snake_case field names, without the need to use aliases.

```py
import os

from azure.identity import DefaultAzureCredential

from pydantic_settings import (
    AzureKeyVaultSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class AzureKeyVaultSettings(BaseSettings):
    my_setting: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        az_key_vault_settings = AzureKeyVaultSettingsSource(
            settings_cls,
            os.environ['AZURE_KEY_VAULT_URL'],
            DefaultAzureCredential(),
            snake_case_conversion=True,
        )
        return (az_key_vault_settings,)

```

This setup will load Azure Key Vault secrets (e.g., `MySetting`, `mySetting`, `my-secret` or `MY-SECRET`), mapping them to the snake case version (`my_setting` in this case).

### Dash to underscore mapping

The Azure Key Vault source accepts a `dash_to_underscore` option, disabled by default, to support Key Vault kebab-case secret names by mapping them to Python's snake_case field names. When enabled, dashes (`-`) in secret names are mapped to underscores (`_`) in field names during validation.

This mapping applies only to *field names*, not to aliases.

```py
import os

from azure.identity import DefaultAzureCredential
from pydantic import Field

from pydantic_settings import (
    AzureKeyVaultSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
)


class AzureKeyVaultSettings(BaseSettings):
    field_with_underscore: str
    field_with_alias: str = Field(..., alias='Alias-With-Dashes')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        az_key_vault_settings = AzureKeyVaultSettingsSource(
            settings_cls,
            os.environ['AZURE_KEY_VAULT_URL'],
            DefaultAzureCredential(),
            dash_to_underscore=True,
        )
        return (az_key_vault_settings,)

```

This setup will load Azure Key Vault secrets named `field-with-underscore` and `Alias-With-Dashes`, mapping them to the `field_with_underscore` and `field_with_alias` fields, respectively.

Tip

Alternatively, you can configure an [alias_generator](../alias/#using-alias-generators) to map PascalCase secrets.

## Google Cloud Secret Manager

Google Cloud Secret Manager allows you to store, manage, and access sensitive information as secrets in Google Cloud Platform. This integration lets you retrieve secrets directly from GCP Secret Manager for use in your Pydantic settings.

### Installation

The Google Cloud Secret Manager integration requires additional dependencies:

```bash
pip install "pydantic-settings[gcp-secret-manager]"

```

### Basic Usage

To use Google Cloud Secret Manager, you need to:

1. Create a `GoogleSecretManagerSettingsSource`. (See [GCP Authentication](#gcp-authentication) for authentication options.)
1. Add this source to your settings customization pipeline

```py
from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    GoogleSecretManagerSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class Database(BaseModel):
    password: str
    user: str


class Settings(BaseSettings):
    database: Database

    model_config = SettingsConfigDict(env_nested_delimiter='__')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Create the GCP Secret Manager settings source
        gcp_settings = GoogleSecretManagerSettingsSource(
            settings_cls,
            # If not provided, will use google.auth.default()
            # to get credentials from the environemnt
            # credentials=your_credentials,
            # If not provided, will use google.auth.default()
            # to get project_id from the environemnt
            project_id='your-gcp-project-id',
        )

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            gcp_settings,
        )

```

### GCP Authentication

The `GoogleSecretManagerSettingsSource` supports several authentication methods:

1. **Default credentials** - If you don't provide credentials or project ID, it will use [`google.auth.default()`](https://google-auth.readthedocs.io/en/master/reference/google.auth.html#google.auth.default) to obtain them. This works with:
1. Service account credentials from `GOOGLE_APPLICATION_CREDENTIALS` environment variable
1. User credentials from `gcloud auth application-default login`
1. Compute Engine, GKE, Cloud Run, or Cloud Functions default service accounts
1. **Explicit credentials** - You can also provide `credentials` directly. e.g. `sa_credentials = google.oauth2.service_account.Credentials.from_service_account_file('path/to/service-account.json')` and then `GoogleSecretManagerSettingsSource(credentials=sa_credentials)`

### Nested Models

For nested models, Secret Manager supports the `env_nested_delimiter` setting as long as it complies with the [naming rules](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create-a-secret). In the example above, you would create secrets named `database__password` and `database__user` in Secret Manager.

### Important Notes

1. **Case Sensitivity**: By default, secret names are case-sensitive.
1. **Secret Naming**: Create secrets in Google Secret Manager with names that match your field names (including any prefix). According the [Secret Manager documentation](https://cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create-a-secret), a secret name can contain uppercase and lowercase letters, numerals, hyphens, and underscores. The maximum allowed length for a name is 255 characters.
1. **Secret Versions**: The GoogleSecretManagerSettingsSource uses the "latest" version of secrets.

For more details on creating and managing secrets in Google Cloud Secret Manager, see the [official Google Cloud documentation](https://cloud.google.com/secret-manager/docs).

## Other settings source

Other settings sources are available for common configuration files:

- `JsonConfigSettingsSource` using `json_file` and `json_file_encoding` arguments
- `PyprojectTomlConfigSettingsSource` using *(optional)* `pyproject_toml_depth` and *(optional)* `pyproject_toml_table_header` arguments
- `TomlConfigSettingsSource` using `toml_file` argument
- `YamlConfigSettingsSource` using `yaml_file` and yaml_file_encoding arguments

You can also provide multiple files by providing a list of path:

```py
toml_file = ['config.default.toml', 'config.custom.toml']

```

To use them, you can use the same mechanism described [here](#customise-settings-sources)

```py
from pydantic import BaseModel

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Nested(BaseModel):
    nested_field: str


class Settings(BaseSettings):
    foobar: str
    nested: Nested
    model_config = SettingsConfigDict(toml_file='config.toml')

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)

```

This will be able to read the following "config.toml" file, located in your working directory:

```toml
foobar = "Hello"
[nested]
nested_field = "world!"

```

### pyproject.toml

"pyproject.toml" is a standardized file for providing configuration values in Python projects. [PEP 518](https://peps.python.org/pep-0518/#tool-table) defines a `[tool]` table that can be used to provide arbitrary tool configuration. While encouraged to use the `[tool]` table, `PyprojectTomlConfigSettingsSource` can be used to load variables from any location with in "pyproject.toml" file.

This is controlled by providing `SettingsConfigDict(pyproject_toml_table_header=tuple[str, ...])` where the value is a tuple of header parts. By default, `pyproject_toml_table_header=('tool', 'pydantic-settings')` which will load variables from the `[tool.pydantic-settings]` table.

```python
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Example loading values from the table used by default."""

    field: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)


class SomeTableSettings(Settings):
    """Example loading values from a user defined table."""

    model_config = SettingsConfigDict(
        pyproject_toml_table_header=('tool', 'some-table')
    )


class RootSettings(Settings):
    """Example loading values from the root of a pyproject.toml file."""

    model_config = SettingsConfigDict(extra='ignore', pyproject_toml_table_header=())

```

This will be able to read the following "pyproject.toml" file, located in your working directory, resulting in `Settings(field='default-table')`, `SomeTableSettings(field='some-table')`, & `RootSettings(field='root')`:

```toml
field = "root"

[tool.pydantic-settings]
field = "default-table"

[tool.some-table]
field = "some-table"

```

By default, `PyprojectTomlConfigSettingsSource` will only look for a "pyproject.toml" in the your current working directory. However, there are two options to change this behavior.

- `SettingsConfigDict(pyproject_toml_depth=<int>)` can be provided to check `<int>` number of directories **up** in the directory tree for a "pyproject.toml" if one is not found in the current working directory. By default, no parent directories are checked.
- An explicit file path can be provided to the source when it is instantiated (e.g. `PyprojectTomlConfigSettingsSource(settings_cls, Path('~/.config').resolve() / 'pyproject.toml')`). If a file path is provided this way, it will be treated as absolute (no other locations are checked).

```python
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class DiscoverSettings(BaseSettings):
    """Example of discovering a pyproject.toml in parent directories in not in `Path.cwd()`."""

    model_config = SettingsConfigDict(pyproject_toml_depth=2)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (PyprojectTomlConfigSettingsSource(settings_cls),)


class ExplicitFilePathSettings(BaseSettings):
    """Example of explicitly providing the path to the file to load."""

    field: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            PyprojectTomlConfigSettingsSource(
                settings_cls, Path('~/.config').resolve() / 'pyproject.toml'
            ),
        )

```

## Field value priority

In the case where a value is specified for the same `Settings` field in multiple ways, the selected value is determined as follows (in descending order of priority):

1. If `cli_parse_args` is enabled, arguments passed in at the CLI.
1. Arguments passed to the `Settings` class initialiser.
1. Environment variables, e.g. `my_prefix_special_function` as described above.
1. Variables loaded from a dotenv (`.env`) file.
1. Variables loaded from the secrets directory.
1. The default field values for the `Settings` model.

## Customise settings sources

If the default order of priority doesn't match your needs, it's possible to change it by overriding the `settings_customise_sources` method of your `Settings` .

`settings_customise_sources` takes four callables as arguments and returns any number of callables as a tuple. In turn these callables are called to build the inputs to the fields of the settings class.

Each callable should take an instance of the settings class as its sole argument and return a `dict`.

### Changing Priority

The order of the returned callables decides the priority of inputs; first item is the highest priority.

```py
from pydantic import PostgresDsn

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class Settings(BaseSettings):
    database_dsn: PostgresDsn

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, init_settings, file_secret_settings


print(Settings(database_dsn='postgres://postgres@localhost:5432/kwargs_db'))
#> database_dsn=PostgresDsn('postgres://postgres@localhost:5432/kwargs_db')

```

By flipping `env_settings` and `init_settings`, environment variables now have precedence over `__init__` kwargs.

### Adding sources

As explained earlier, *pydantic* ships with multiples built-in settings sources. However, you may occasionally need to add your own custom sources, `settings_customise_sources` makes this very easy:

```py
import json
from pathlib import Path
from typing import Any

from pydantic.fields import FieldInfo

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class JsonConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source class that loads variables from a JSON file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.json`
    """

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        encoding = self.config.get('env_file_encoding')
        file_content_json = json.loads(
            Path('tests/example_test_config.json').read_text(encoding)
        )
        field_value = file_content_json.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    foobar: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            JsonConfigSettingsSource(settings_cls),
            env_settings,
            file_secret_settings,
        )


print(Settings())
#> foobar='test'

```

#### Accessing the result of previous sources

Each source of settings can access the output of the previous ones.

```python
from typing import Any

from pydantic.fields import FieldInfo

from pydantic_settings import PydanticBaseSettingsSource


class MyCustomSource(PydanticBaseSettingsSource):
    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]: ...

    def __call__(self) -> dict[str, Any]:
        # Retrieve the aggregated settings from previous sources
        current_state = self.current_state
        current_state.get('some_setting')

        # Retrive settings from all sources individually
        # self.settings_sources_data["SettingsSourceName"]: dict[str, Any]
        settings_sources_data = self.settings_sources_data
        settings_sources_data['SomeSettingsSource'].get('some_setting')

        # Your code here...

```

### Removing sources

You might also want to disable a source:

```py
from pydantic import ValidationError

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource


class Settings(BaseSettings):
    my_api_key: str

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # here we choose to ignore arguments from init_settings
        return env_settings, file_secret_settings


try:
    Settings(my_api_key='this is ignored')
except ValidationError as exc_info:
    print(exc_info)
    """
    1 validation error for Settings
    my_api_key
      Field required [type=missing, input_value={}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2/v/missing
    """

```

## In-place reloading

In case you want to reload in-place an existing setting, you can do it by using its `__init__` method :

```py
import os

from pydantic import Field

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    foo: str = Field('foo')


mutable_settings = Settings()

print(mutable_settings.foo)
#> foo

os.environ['foo'] = 'bar'
print(mutable_settings.foo)
#> foo

mutable_settings.__init__()
print(mutable_settings.foo)
#> bar

os.environ.pop('foo')
mutable_settings.__init__()
print(mutable_settings.foo)
#> foo

```
