One of pydantic's most useful applications is to define default settings, and allow them to be overridden by
environment variables or keyword arguments (e.g. in unit tests).

```py
{!./examples/settings.py!}
```
_(This script is complete, it should run "as is")_

The following rules apply when finding and interpreting environment variables:

* When no custom environment variable name(s) are given, the environment variable name is built using the field
  name and prefix, eg to override `special_function` use `export my_prefix_special_function='foo.bar'`, the default
  prefix is an empty string. aliases are ignored for building the environment variable name.
* Custom environment variable names can be set using with `Config.fields.[field name].env` or `Field(..., env=...)`,
  in the above example `auth_key` and `api_key`'s environment variable setups are the equivalent.
* In these cases `env` can either be a string or a list of strings. When a list of strings order is important:
  in the case of `redis_dsn` `service_redis_dsn` would take precedence over `redis_url`.

<div id="alias-warning" style="height: 35px">
  <!-- this div provides an anchor to link to from the warning in env_settings.py -->
</div>

!!! warning
    Since **v1.0** *pydantic* does not consider field aliases when finding environment variables to populate settings
    models, use `env` instead as described above.

    To aid the transition from aliases to `env`, a warning will be raised when aliases are used on settings models
    without a custom env var name. If you really mean to use aliases, either ignore the warning or set `env` to
    suppress it.

By default `BaseSettings` considers field values in the following priority (where 3. has the highest priority
and overrides the other two):

1. The default values set in your `Settings` class.
2. Environment variables, e.g. `my_prefix_special_function` as described above.
3. Arguments passed to the `Settings` class on initialisation.

Complex types like `list`, `set`, `dict` and sub-models can be set by using JSON environment variables.

Case-sensitivity can be turned on through `Config`:

```py
{!./examples/settings_case_sensitive.py!}
```

When `case_sensitive` is `True`, the environment variable must be in all-caps,
so in this example `redis_host` could only be modified via `export REDIS_HOST`.

!!! note
    On Windows, python's `os` module always treats environment variables as case-insensitive, so the
    `case_sensitive` config setting will have no effect -- settings will always be updated ignoring case.
