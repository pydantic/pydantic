One of pydantic's most useful applications is settings management.

If you create a model that inherits from `BaseSettings`, the model initialiser will attempt to determine
the values of any fields not passed as keyword arguments by reading from the environment. (Default values
will still be used if the matching environment variable is not set.)

This makes it easy to:

* Create a clearly-defined, type-hinted application configuration class
* Automatically read modifications to the configuration from environment variables
* Manually override specific settings in the initialiser where desired (e.g. in unit tests)

For example:

```py
{!.tmp_examples/settings_main.py!}
```
_(This script is complete, it should run "as is")_

## Environment variable names

The following rules are used to determine which environment variable(s) are read for a given field:

* By default, the environment variable name is built by concatenating the prefix and field name.
    * For example, to override `special_function` above, you could use:

            export my_prefix_special_function='foo.bar'

    * Note 1: The default prefix is an empty string.
    * Note 2: Field aliases are ignored when building the environment variable name.

* Custom environment variable names can be set in two ways:
    * `Config.fields['field_name']['env']` (see `auth_key` and `redis_dsn` above)
    * `Field(..., env=...)` (see `api_key` above)
* When specifying custom environment variable names, either a string or a list of strings may be provided.
    * When specifying a list of strings, order matters: the first detected value is used.
    * For example, for `redis_dsn` above, `service_redis_dsn` would take precedence over `redis_url`.

!!! warning
    Since **v1.0** *pydantic* does not consider field aliases when finding environment variables to populate settings
    models, use `env` instead as described above.

    To aid the transition from aliases to `env`, a warning will be raised when aliases are used on settings models
    without a custom env var name. If you really mean to use aliases, either ignore the warning or set `env` to
    suppress it.

Case-sensitivity can be turned on through the `Config`:

```py
{!.tmp_examples/settings_case_sensitive.py!}
```

When `case_sensitive` is `True`, the environment variable names must match field names (optionally with a prefix),
so in this example
`redis_host` could only be modified via `export redis_host`. If you want to name environment variables
all upper-case, you should name attribute all upper-case too. You can still name environment variables anything
you like through `Field(..., env=...)`.

!!! note
    On Windows, python's `os` module always treats environment variables as case-insensitive, so the
    `case_sensitive` config setting will have no effect - settings will always be updated ignoring case.

## Parsing environment variable values

For most simple field types (such as `int`, `float`, `str`, etc.),
the environment variable value is parsed the same way it would
be if passed directly to the initialiser (as a string).

Complex types like `list`, `set`, `dict`, and sub-models are populated from the environment
by treating the environment variable's value as a JSON-encoded string.

## Dotenv (.env) support

!!! note
    dotenv file parsing requires [python-dotenv](https://pypi.org/project/python-dotenv/) to be installed.
    This can be done with either `pip install python-dotenv` or `pip install pydantic[dotenv]`.

Dotenv files (generally named `.env`) are a common pattern that make it easy to use environment variables in a
platform-independent manner.

A dotenv file follows the same general principles of all environment variables,
and looks something like:

```bash
# ignore comment
ENVIRONMENT="production"
REDIS_ADDRESS=localhost:6379
MEANING_OF_LIFE=42
MY_VAR='Hello world'
```

Once you have your `.env` file filled with variables, *pydantic* supports loading it in two ways:

**1.** setting `env_file` (and `env_file_encoding` if you don't want the default encoding of your OS) on `Config`
in a `BaseSettings` class:

```py
class Settings(BaseSettings):
    ...

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
```

**2.** instantiating a `BaseSettings` derived class with the `_env_file` keyword argument
(and the `_env_file_encoding` if needed):

```py
settings = Settings(_env_file='prod.env', _env_file_encoding='utf-8')
```

In either case, the value of the passed argument can be any valid path or filename, either absolute or relative to the
current working directory. From there, *pydantic* will handle everything for you by loading in your variables and
validating them.

Even when using a dotenv file, *pydantic* will still read environment variables as well as the dotenv file,
**environment variables will always take priority over values loaded from a dotenv file**.

Passing a file path via the `_env_file` keyword argument on instantiation (method 2) will override
the value (if any) set on the `Config` class. If the above snippets were used in conjunction, `prod.env` would be loaded
while `.env` would be ignored.

You can also use the keyword argument override to tell Pydantic not to load any file at all (even if one is set in
the `Config` class) by passing `None` as the instantiation keyword argument, e.g. `settings = Settings(_env_file=None)`.

Because python-dotenv is used to parse the file, bash-like semantics such as `export` can be used which
(depending on your OS and environment) may allow your dotenv file to also be used with `source`,
see [python-dotenv's documentation](https://saurabh-kumar.com/python-dotenv/#usages) for more details.

## Field value priority

In the case where a value is specified for the same `Settings` field in multiple ways,
the selected value is determined as follows (in descending order of priority):

1. Arguments passed to the `Settings` class initialiser.
2. Environment variables, e.g. `my_prefix_special_function` as described above.
3. Variables loaded from a dotenv (`.env`) file.
4. The default field values for the `Settings` model.
