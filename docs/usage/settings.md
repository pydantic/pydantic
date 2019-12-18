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

When `case_sensitive` is `True`, the environment variable must be exactly the same as attribute, so in this example
`redis_host` could only be modified via `export redis_host`. And if you want to name environment variables
all upper-case, you should name attribute all upper-case too. I can still name environment variable anything
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

## Field value priority

In the case where a value is specified for the same `Settings` field in multiple ways,
the selected value is determined as follows (in descending order of priority):

1. Arguments passed to the `Settings` class initialiser.
2. Environment variables, e.g. `my_prefix_special_function` as described above.
3. The default field values for the `Settings` model.
