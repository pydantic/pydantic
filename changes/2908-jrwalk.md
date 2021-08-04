Adds configuration logic to the `PydanticPluginConfig` constructor, enabling parsing of the configuration slots from `pyproject.toml` for `mypy>0.900`.
Adds test cases for parsing config from `pyproject.toml`, including a failing case for a non-boolean value (this matches the old `ConfigParser` behavior of raising a `ValueError` on failures in the `getboolean` method).
Increases the pinned version to `mypy==0.902` in the test suite, and includes formatting changes to prior test cases to match.
Adds documentation change reflecting `pyproject.toml` configuration for plugin.
