## BaseSettings

```python
BaseSettings(
    __pydantic_self__,
    _case_sensitive: bool | None = None,
    _nested_model_default_partial_update: (
        bool | None
    ) = None,
    _env_prefix: str | None = None,
    _env_file: DotenvType | None = ENV_FILE_SENTINEL,
    _env_file_encoding: str | None = None,
    _env_ignore_empty: bool | None = None,
    _env_nested_delimiter: str | None = None,
    _env_parse_none_str: str | None = None,
    _env_parse_enums: bool | None = None,
    _cli_prog_name: str | None = None,
    _cli_parse_args: (
        bool | list[str] | tuple[str, ...] | None
    ) = None,
    _cli_settings_source: (
        CliSettingsSource[Any] | None
    ) = None,
    _cli_parse_none_str: str | None = None,
    _cli_hide_none_type: bool | None = None,
    _cli_avoid_json: bool | None = None,
    _cli_enforce_required: bool | None = None,
    _cli_use_class_docs_for_groups: bool | None = None,
    _cli_exit_on_error: bool | None = None,
    _cli_prefix: str | None = None,
    _cli_flag_prefix_char: str | None = None,
    _cli_implicit_flags: bool | None = None,
    _cli_ignore_unknown_args: bool | None = None,
    _cli_kebab_case: bool | None = None,
    _secrets_dir: PathType | None = None,
    **values: Any
)

```

Bases: `BaseModel`

Base class for settings, allowing values to be overridden by environment variables.

This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose), Heroku and any 12 factor app design.

All the below attributes can be set via `model_config`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `_case_sensitive` | `bool | None` | Whether environment and CLI variable names should be read with case-sensitivity. Defaults to None. | `None` | | `_nested_model_default_partial_update` | `bool | None` | Whether to allow partial updates on nested model default object fields. Defaults to False. | `None` | | `_env_prefix` | `str | None` | Prefix for all environment variables. Defaults to None. | `None` | | `_env_file` | `DotenvType | None` | The env file(s) to load settings values from. Defaults to Path(''), which means that the value from model_config['env_file'] should be used. You can also pass None to indicate that environment variables should not be loaded from an env file. | `ENV_FILE_SENTINEL` | | `_env_file_encoding` | `str | None` | The env file encoding, e.g. 'latin-1'. Defaults to None. | `None` | | `_env_ignore_empty` | `bool | None` | Ignore environment variables where the value is an empty string. Default to False. | `None` | | `_env_nested_delimiter` | `str | None` | The nested env values delimiter. Defaults to None. | `None` | | `_env_parse_none_str` | `str | None` | The env string value that should be parsed (e.g. "null", "void", "None", etc.) into None type(None). Defaults to None type(None), which means no parsing should occur. | `None` | | `_env_parse_enums` | `bool | None` | Parse enum field names to values. Defaults to None., which means no parsing should occur. | `None` | | `_cli_prog_name` | `str | None` | The CLI program name to display in help text. Defaults to None if \_cli_parse_args is None. Otherwse, defaults to sys.argv[0]. | `None` | | `_cli_parse_args` | `bool | list[str] | tuple[str, ...] | None` | The list of CLI arguments to parse. Defaults to None. If set to True, defaults to sys.argv[1:]. | `None` | | `_cli_settings_source` | `CliSettingsSource[Any] | None` | Override the default CLI settings source with a user defined instance. Defaults to None. | `None` | | `_cli_parse_none_str` | `str | None` | The CLI string value that should be parsed (e.g. "null", "void", "None", etc.) into None type(None). Defaults to \_env_parse_none_str value if set. Otherwise, defaults to "null" if \_cli_avoid_json is False, and "None" if \_cli_avoid_json is True. | `None` | | `_cli_hide_none_type` | `bool | None` | Hide None values in CLI help text. Defaults to False. | `None` | | `_cli_avoid_json` | `bool | None` | Avoid complex JSON objects in CLI help text. Defaults to False. | `None` | | `_cli_enforce_required` | `bool | None` | Enforce required fields at the CLI. Defaults to False. | `None` | | `_cli_use_class_docs_for_groups` | `bool | None` | Use class docstrings in CLI group help text instead of field descriptions. Defaults to False. | `None` | | `_cli_exit_on_error` | `bool | None` | Determines whether or not the internal parser exits with error info when an error occurs. Defaults to True. | `None` | | `_cli_prefix` | `str | None` | The root parser command line arguments prefix. Defaults to "". | `None` | | `_cli_flag_prefix_char` | `str | None` | The flag prefix character to use for CLI optional arguments. Defaults to '-'. | `None` | | `_cli_implicit_flags` | `bool | None` | Whether bool fields should be implicitly converted into CLI boolean flags. (e.g. --flag, --no-flag). Defaults to False. | `None` | | `_cli_ignore_unknown_args` | `bool | None` | Whether to ignore unknown CLI args and parse only known ones. Defaults to False. | `None` | | `_cli_kebab_case` | `bool | None` | CLI args use kebab case. Defaults to False. | `None` | | `_secrets_dir` | `PathType | None` | The secret files directory or a sequence of directories. Defaults to None. | `None` |

Source code in `pydantic_settings/main.py`

```python
def __init__(
    __pydantic_self__,
    _case_sensitive: bool | None = None,
    _nested_model_default_partial_update: bool | None = None,
    _env_prefix: str | None = None,
    _env_file: DotenvType | None = ENV_FILE_SENTINEL,
    _env_file_encoding: str | None = None,
    _env_ignore_empty: bool | None = None,
    _env_nested_delimiter: str | None = None,
    _env_parse_none_str: str | None = None,
    _env_parse_enums: bool | None = None,
    _cli_prog_name: str | None = None,
    _cli_parse_args: bool | list[str] | tuple[str, ...] | None = None,
    _cli_settings_source: CliSettingsSource[Any] | None = None,
    _cli_parse_none_str: str | None = None,
    _cli_hide_none_type: bool | None = None,
    _cli_avoid_json: bool | None = None,
    _cli_enforce_required: bool | None = None,
    _cli_use_class_docs_for_groups: bool | None = None,
    _cli_exit_on_error: bool | None = None,
    _cli_prefix: str | None = None,
    _cli_flag_prefix_char: str | None = None,
    _cli_implicit_flags: bool | None = None,
    _cli_ignore_unknown_args: bool | None = None,
    _cli_kebab_case: bool | None = None,
    _secrets_dir: PathType | None = None,
    **values: Any,
) -> None:
    # Uses something other than `self` the first arg to allow "self" as a settable attribute
    super().__init__(
        **__pydantic_self__._settings_build_values(
            values,
            _case_sensitive=_case_sensitive,
            _nested_model_default_partial_update=_nested_model_default_partial_update,
            _env_prefix=_env_prefix,
            _env_file=_env_file,
            _env_file_encoding=_env_file_encoding,
            _env_ignore_empty=_env_ignore_empty,
            _env_nested_delimiter=_env_nested_delimiter,
            _env_parse_none_str=_env_parse_none_str,
            _env_parse_enums=_env_parse_enums,
            _cli_prog_name=_cli_prog_name,
            _cli_parse_args=_cli_parse_args,
            _cli_settings_source=_cli_settings_source,
            _cli_parse_none_str=_cli_parse_none_str,
            _cli_hide_none_type=_cli_hide_none_type,
            _cli_avoid_json=_cli_avoid_json,
            _cli_enforce_required=_cli_enforce_required,
            _cli_use_class_docs_for_groups=_cli_use_class_docs_for_groups,
            _cli_exit_on_error=_cli_exit_on_error,
            _cli_prefix=_cli_prefix,
            _cli_flag_prefix_char=_cli_flag_prefix_char,
            _cli_implicit_flags=_cli_implicit_flags,
            _cli_ignore_unknown_args=_cli_ignore_unknown_args,
            _cli_kebab_case=_cli_kebab_case,
            _secrets_dir=_secrets_dir,
        )
    )

```

### settings_customise_sources

```python
settings_customise_sources(
    settings_cls: type[BaseSettings],
    init_settings: PydanticBaseSettingsSource,
    env_settings: PydanticBaseSettingsSource,
    dotenv_settings: PydanticBaseSettingsSource,
    file_secret_settings: PydanticBaseSettingsSource,
) -> tuple[PydanticBaseSettingsSource, ...]

```

Define the sources and their order for loading the settings values.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `settings_cls` | `type[BaseSettings]` | The Settings class. | *required* | | `init_settings` | `PydanticBaseSettingsSource` | The InitSettingsSource instance. | *required* | | `env_settings` | `PydanticBaseSettingsSource` | The EnvSettingsSource instance. | *required* | | `dotenv_settings` | `PydanticBaseSettingsSource` | The DotEnvSettingsSource instance. | *required* | | `file_secret_settings` | `PydanticBaseSettingsSource` | The SecretsSettingsSource instance. | *required* |

Returns:

| Type | Description | | --- | --- | | `tuple[PydanticBaseSettingsSource, ...]` | A tuple containing the sources and their order for loading the settings values. |

Source code in `pydantic_settings/main.py`

```python
@classmethod
def settings_customise_sources(
    cls,
    settings_cls: type[BaseSettings],
    init_settings: PydanticBaseSettingsSource,
    env_settings: PydanticBaseSettingsSource,
    dotenv_settings: PydanticBaseSettingsSource,
    file_secret_settings: PydanticBaseSettingsSource,
) -> tuple[PydanticBaseSettingsSource, ...]:
    """
    Define the sources and their order for loading the settings values.

    Args:
        settings_cls: The Settings class.
        init_settings: The `InitSettingsSource` instance.
        env_settings: The `EnvSettingsSource` instance.
        dotenv_settings: The `DotEnvSettingsSource` instance.
        file_secret_settings: The `SecretsSettingsSource` instance.

    Returns:
        A tuple containing the sources and their order for loading the settings values.
    """
    return init_settings, env_settings, dotenv_settings, file_secret_settings

```

## CliApp

A utility class for running Pydantic `BaseSettings`, `BaseModel`, or `pydantic.dataclasses.dataclass` as CLI applications.

### run

```python
run(
    model_cls: type[T],
    cli_args: (
        list[str]
        | Namespace
        | SimpleNamespace
        | dict[str, Any]
        | None
    ) = None,
    cli_settings_source: (
        CliSettingsSource[Any] | None
    ) = None,
    cli_exit_on_error: bool | None = None,
    cli_cmd_method_name: str = "cli_cmd",
    **model_init_data: Any
) -> T

```

Runs a Pydantic `BaseSettings`, `BaseModel`, or `pydantic.dataclasses.dataclass` as a CLI application. Running a model as a CLI application requires the `cli_cmd` method to be defined in the model class.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model_cls` | `type[T]` | The model class to run as a CLI application. | *required* | | `cli_args` | `list[str] | Namespace | SimpleNamespace | dict[str, Any] | None` | The list of CLI arguments to parse. If cli_settings_source is specified, this may also be a namespace or dictionary of pre-parsed CLI arguments. Defaults to sys.argv[1:]. | `None` | | `cli_settings_source` | `CliSettingsSource[Any] | None` | Override the default CLI settings source with a user defined instance. Defaults to None. | `None` | | `cli_exit_on_error` | `bool | None` | Determines whether this function exits on error. If model is subclass of BaseSettings, defaults to BaseSettings cli_exit_on_error value. Otherwise, defaults to True. | `None` | | `cli_cmd_method_name` | `str` | The CLI command method name to run. Defaults to "cli_cmd". | `'cli_cmd'` | | `model_init_data` | `Any` | The model init data. | `{}` |

Returns:

| Type | Description | | --- | --- | | `T` | The ran instance of model. |

Raises:

| Type | Description | | --- | --- | | `SettingsError` | If model_cls is not subclass of BaseModel or pydantic.dataclasses.dataclass. | | `SettingsError` | If model_cls does not have a cli_cmd entrypoint defined. |

Source code in `pydantic_settings/main.py`

```python
@staticmethod
def run(
    model_cls: type[T],
    cli_args: list[str] | Namespace | SimpleNamespace | dict[str, Any] | None = None,
    cli_settings_source: CliSettingsSource[Any] | None = None,
    cli_exit_on_error: bool | None = None,
    cli_cmd_method_name: str = 'cli_cmd',
    **model_init_data: Any,
) -> T:
    """
    Runs a Pydantic `BaseSettings`, `BaseModel`, or `pydantic.dataclasses.dataclass` as a CLI application.
    Running a model as a CLI application requires the `cli_cmd` method to be defined in the model class.

    Args:
        model_cls: The model class to run as a CLI application.
        cli_args: The list of CLI arguments to parse. If `cli_settings_source` is specified, this may
            also be a namespace or dictionary of pre-parsed CLI arguments. Defaults to `sys.argv[1:]`.
        cli_settings_source: Override the default CLI settings source with a user defined instance.
            Defaults to `None`.
        cli_exit_on_error: Determines whether this function exits on error. If model is subclass of
            `BaseSettings`, defaults to BaseSettings `cli_exit_on_error` value. Otherwise, defaults to
            `True`.
        cli_cmd_method_name: The CLI command method name to run. Defaults to "cli_cmd".
        model_init_data: The model init data.

    Returns:
        The ran instance of model.

    Raises:
        SettingsError: If model_cls is not subclass of `BaseModel` or `pydantic.dataclasses.dataclass`.
        SettingsError: If model_cls does not have a `cli_cmd` entrypoint defined.
    """

    if not (is_pydantic_dataclass(model_cls) or is_model_class(model_cls)):
        raise SettingsError(
            f'Error: {model_cls.__name__} is not subclass of BaseModel or pydantic.dataclasses.dataclass'
        )

    cli_settings = None
    cli_parse_args = True if cli_args is None else cli_args
    if cli_settings_source is not None:
        if isinstance(cli_parse_args, (Namespace, SimpleNamespace, dict)):
            cli_settings = cli_settings_source(parsed_args=cli_parse_args)
        else:
            cli_settings = cli_settings_source(args=cli_parse_args)
    elif isinstance(cli_parse_args, (Namespace, SimpleNamespace, dict)):
        raise SettingsError('Error: `cli_args` must be list[str] or None when `cli_settings_source` is not used')

    model_init_data['_cli_parse_args'] = cli_parse_args
    model_init_data['_cli_exit_on_error'] = cli_exit_on_error
    model_init_data['_cli_settings_source'] = cli_settings
    if not issubclass(model_cls, BaseSettings):

        class CliAppBaseSettings(BaseSettings, model_cls):  # type: ignore
            model_config = SettingsConfigDict(
                nested_model_default_partial_update=True,
                case_sensitive=True,
                cli_hide_none_type=True,
                cli_avoid_json=True,
                cli_enforce_required=True,
                cli_implicit_flags=True,
                cli_kebab_case=True,
            )

        model = CliAppBaseSettings(**model_init_data)
        model_init_data = {}
        for field_name, field_info in model.model_fields.items():
            model_init_data[_field_name_for_signature(field_name, field_info)] = getattr(model, field_name)

    return CliApp._run_cli_cmd(model_cls(**model_init_data), cli_cmd_method_name, is_required=False)

```

### run_subcommand

```python
run_subcommand(
    model: PydanticModel,
    cli_exit_on_error: bool | None = None,
    cli_cmd_method_name: str = "cli_cmd",
) -> PydanticModel

```

Runs the model subcommand. Running a model subcommand requires the `cli_cmd` method to be defined in the nested model subcommand class.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `PydanticModel` | The model to run the subcommand from. | *required* | | `cli_exit_on_error` | `bool | None` | Determines whether this function exits with error if no subcommand is found. Defaults to model_config cli_exit_on_error value if set. Otherwise, defaults to True. | `None` | | `cli_cmd_method_name` | `str` | The CLI command method name to run. Defaults to "cli_cmd". | `'cli_cmd'` |

Returns:

| Type | Description | | --- | --- | | `PydanticModel` | The ran subcommand model. |

Raises:

| Type | Description | | --- | --- | | `SystemExit` | When no subcommand is found and cli_exit_on_error=True (the default). | | `SettingsError` | When no subcommand is found and cli_exit_on_error=False. |

Source code in `pydantic_settings/main.py`

```python
@staticmethod
def run_subcommand(
    model: PydanticModel, cli_exit_on_error: bool | None = None, cli_cmd_method_name: str = 'cli_cmd'
) -> PydanticModel:
    """
    Runs the model subcommand. Running a model subcommand requires the `cli_cmd` method to be defined in
    the nested model subcommand class.

    Args:
        model: The model to run the subcommand from.
        cli_exit_on_error: Determines whether this function exits with error if no subcommand is found.
            Defaults to model_config `cli_exit_on_error` value if set. Otherwise, defaults to `True`.
        cli_cmd_method_name: The CLI command method name to run. Defaults to "cli_cmd".

    Returns:
        The ran subcommand model.

    Raises:
        SystemExit: When no subcommand is found and cli_exit_on_error=`True` (the default).
        SettingsError: When no subcommand is found and cli_exit_on_error=`False`.
    """

    subcommand = get_subcommand(model, is_required=True, cli_exit_on_error=cli_exit_on_error)
    return CliApp._run_cli_cmd(subcommand, cli_cmd_method_name, is_required=True)

```

## SettingsConfigDict

Bases: `ConfigDict`

### pyproject_toml_depth

```python
pyproject_toml_depth: int

```

Number of levels **up** from the current working directory to attempt to find a pyproject.toml file.

This is only used when a pyproject.toml file is not found in the current working directory.

### pyproject_toml_table_header

```python
pyproject_toml_table_header: tuple[str, ...]

```

Header of the TOML table within a pyproject.toml file to use when filling variables. This is supplied as a `tuple[str, ...]` instead of a `str` to accommodate for headers containing a `.`.

For example, `toml_table_header = ("tool", "my.tool", "foo")` can be used to fill variable values from a table with header `[tool."my.tool".foo]`.

To use the root table, exclude this config setting or provide an empty tuple.

## CliSettingsSource

```python
CliSettingsSource(
    settings_cls: type[BaseSettings],
    cli_prog_name: str | None = None,
    cli_parse_args: (
        bool | list[str] | tuple[str, ...] | None
    ) = None,
    cli_parse_none_str: str | None = None,
    cli_hide_none_type: bool | None = None,
    cli_avoid_json: bool | None = None,
    cli_enforce_required: bool | None = None,
    cli_use_class_docs_for_groups: bool | None = None,
    cli_exit_on_error: bool | None = None,
    cli_prefix: str | None = None,
    cli_flag_prefix_char: str | None = None,
    cli_implicit_flags: bool | None = None,
    cli_ignore_unknown_args: bool | None = None,
    cli_kebab_case: bool | None = None,
    case_sensitive: bool | None = True,
    root_parser: Any = None,
    parse_args_method: Callable[..., Any] | None = None,
    add_argument_method: (
        Callable[..., Any] | None
    ) = add_argument,
    add_argument_group_method: (
        Callable[..., Any] | None
    ) = add_argument_group,
    add_parser_method: (
        Callable[..., Any] | None
    ) = add_parser,
    add_subparsers_method: (
        Callable[..., Any] | None
    ) = add_subparsers,
    formatter_class: Any = RawDescriptionHelpFormatter,
)

```

Bases: `EnvSettingsSource`, `Generic[T]`

Source class for loading settings values from CLI.

Note

A `CliSettingsSource` connects with a `root_parser` object by using the parser methods to add `settings_cls` fields as command line arguments. The `CliSettingsSource` internal parser representation is based upon the `argparse` parsing library, and therefore, requires the parser methods to support the same attributes as their `argparse` library counterparts.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cli_prog_name` | `str | None` | The CLI program name to display in help text. Defaults to None if cli_parse_args is None. Otherwse, defaults to sys.argv[0]. | `None` | | `cli_parse_args` | `bool | list[str] | tuple[str, ...] | None` | The list of CLI arguments to parse. Defaults to None. If set to True, defaults to sys.argv[1:]. | `None` | | `cli_parse_none_str` | `str | None` | The CLI string value that should be parsed (e.g. "null", "void", "None", etc.) into None type(None). Defaults to "null" if cli_avoid_json is False, and "None" if cli_avoid_json is True. | `None` | | `cli_hide_none_type` | `bool | None` | Hide None values in CLI help text. Defaults to False. | `None` | | `cli_avoid_json` | `bool | None` | Avoid complex JSON objects in CLI help text. Defaults to False. | `None` | | `cli_enforce_required` | `bool | None` | Enforce required fields at the CLI. Defaults to False. | `None` | | `cli_use_class_docs_for_groups` | `bool | None` | Use class docstrings in CLI group help text instead of field descriptions. Defaults to False. | `None` | | `cli_exit_on_error` | `bool | None` | Determines whether or not the internal parser exits with error info when an error occurs. Defaults to True. | `None` | | `cli_prefix` | `str | None` | Prefix for command line arguments added under the root parser. Defaults to "". | `None` | | `cli_flag_prefix_char` | `str | None` | The flag prefix character to use for CLI optional arguments. Defaults to '-'. | `None` | | `cli_implicit_flags` | `bool | None` | Whether bool fields should be implicitly converted into CLI boolean flags. (e.g. --flag, --no-flag). Defaults to False. | `None` | | `cli_ignore_unknown_args` | `bool | None` | Whether to ignore unknown CLI args and parse only known ones. Defaults to False. | `None` | | `cli_kebab_case` | `bool | None` | CLI args use kebab case. Defaults to False. | `None` | | `case_sensitive` | `bool | None` | Whether CLI "--arg" names should be read with case-sensitivity. Defaults to True. Note: Case-insensitive matching is only supported on the internal root parser and does not apply to CLI subcommands. | `True` | | `root_parser` | `Any` | The root parser object. | `None` | | `parse_args_method` | `Callable[..., Any] | None` | The root parser parse args method. Defaults to argparse.ArgumentParser.parse_args. | `None` | | `add_argument_method` | `Callable[..., Any] | None` | The root parser add argument method. Defaults to argparse.ArgumentParser.add_argument. | `add_argument` | | `add_argument_group_method` | `Callable[..., Any] | None` | The root parser add argument group method. Defaults to argparse.ArgumentParser.add_argument_group. | `add_argument_group` | | `add_parser_method` | `Callable[..., Any] | None` | The root parser add new parser (sub-command) method. Defaults to argparse.\_SubParsersAction.add_parser. | `add_parser` | | `add_subparsers_method` | `Callable[..., Any] | None` | The root parser add subparsers (sub-commands) method. Defaults to argparse.ArgumentParser.add_subparsers. | `add_subparsers` | | `formatter_class` | `Any` | A class for customizing the root parser help text. Defaults to argparse.RawDescriptionHelpFormatter. | `RawDescriptionHelpFormatter` |

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    cli_prog_name: str | None = None,
    cli_parse_args: bool | list[str] | tuple[str, ...] | None = None,
    cli_parse_none_str: str | None = None,
    cli_hide_none_type: bool | None = None,
    cli_avoid_json: bool | None = None,
    cli_enforce_required: bool | None = None,
    cli_use_class_docs_for_groups: bool | None = None,
    cli_exit_on_error: bool | None = None,
    cli_prefix: str | None = None,
    cli_flag_prefix_char: str | None = None,
    cli_implicit_flags: bool | None = None,
    cli_ignore_unknown_args: bool | None = None,
    cli_kebab_case: bool | None = None,
    case_sensitive: bool | None = True,
    root_parser: Any = None,
    parse_args_method: Callable[..., Any] | None = None,
    add_argument_method: Callable[..., Any] | None = ArgumentParser.add_argument,
    add_argument_group_method: Callable[..., Any] | None = ArgumentParser.add_argument_group,
    add_parser_method: Callable[..., Any] | None = _SubParsersAction.add_parser,
    add_subparsers_method: Callable[..., Any] | None = ArgumentParser.add_subparsers,
    formatter_class: Any = RawDescriptionHelpFormatter,
) -> None:
    self.cli_prog_name = (
        cli_prog_name if cli_prog_name is not None else settings_cls.model_config.get('cli_prog_name', sys.argv[0])
    )
    self.cli_hide_none_type = (
        cli_hide_none_type
        if cli_hide_none_type is not None
        else settings_cls.model_config.get('cli_hide_none_type', False)
    )
    self.cli_avoid_json = (
        cli_avoid_json if cli_avoid_json is not None else settings_cls.model_config.get('cli_avoid_json', False)
    )
    if not cli_parse_none_str:
        cli_parse_none_str = 'None' if self.cli_avoid_json is True else 'null'
    self.cli_parse_none_str = cli_parse_none_str
    self.cli_enforce_required = (
        cli_enforce_required
        if cli_enforce_required is not None
        else settings_cls.model_config.get('cli_enforce_required', False)
    )
    self.cli_use_class_docs_for_groups = (
        cli_use_class_docs_for_groups
        if cli_use_class_docs_for_groups is not None
        else settings_cls.model_config.get('cli_use_class_docs_for_groups', False)
    )
    self.cli_exit_on_error = (
        cli_exit_on_error
        if cli_exit_on_error is not None
        else settings_cls.model_config.get('cli_exit_on_error', True)
    )
    self.cli_prefix = cli_prefix if cli_prefix is not None else settings_cls.model_config.get('cli_prefix', '')
    self.cli_flag_prefix_char = (
        cli_flag_prefix_char
        if cli_flag_prefix_char is not None
        else settings_cls.model_config.get('cli_flag_prefix_char', '-')
    )
    self._cli_flag_prefix = self.cli_flag_prefix_char * 2
    if self.cli_prefix:
        if cli_prefix.startswith('.') or cli_prefix.endswith('.') or not cli_prefix.replace('.', '').isidentifier():  # type: ignore
            raise SettingsError(f'CLI settings source prefix is invalid: {cli_prefix}')
        self.cli_prefix += '.'
    self.cli_implicit_flags = (
        cli_implicit_flags
        if cli_implicit_flags is not None
        else settings_cls.model_config.get('cli_implicit_flags', False)
    )
    self.cli_ignore_unknown_args = (
        cli_ignore_unknown_args
        if cli_ignore_unknown_args is not None
        else settings_cls.model_config.get('cli_ignore_unknown_args', False)
    )
    self.cli_kebab_case = (
        cli_kebab_case if cli_kebab_case is not None else settings_cls.model_config.get('cli_kebab_case', False)
    )

    case_sensitive = case_sensitive if case_sensitive is not None else True
    if not case_sensitive and root_parser is not None:
        raise SettingsError('Case-insensitive matching is only supported on the internal root parser')

    super().__init__(
        settings_cls,
        env_nested_delimiter='.',
        env_parse_none_str=self.cli_parse_none_str,
        env_parse_enums=True,
        env_prefix=self.cli_prefix,
        case_sensitive=case_sensitive,
    )

    root_parser = (
        _CliInternalArgParser(
            cli_exit_on_error=self.cli_exit_on_error,
            prog=self.cli_prog_name,
            description=None if settings_cls.__doc__ is None else dedent(settings_cls.__doc__),
            formatter_class=formatter_class,
            prefix_chars=self.cli_flag_prefix_char,
            allow_abbrev=False,
        )
        if root_parser is None
        else root_parser
    )
    self._connect_root_parser(
        root_parser=root_parser,
        parse_args_method=parse_args_method,
        add_argument_method=add_argument_method,
        add_argument_group_method=add_argument_group_method,
        add_parser_method=add_parser_method,
        add_subparsers_method=add_subparsers_method,
        formatter_class=formatter_class,
    )

    if cli_parse_args not in (None, False):
        if cli_parse_args is True:
            cli_parse_args = sys.argv[1:]
        elif not isinstance(cli_parse_args, (list, tuple)):
            raise SettingsError(
                f'cli_parse_args must be List[str] or Tuple[str, ...], recieved {type(cli_parse_args)}'
            )
        self._load_env_vars(parsed_args=self._parse_args(self.root_parser, cli_parse_args))

```

### root_parser

```python
root_parser: T

```

The connected root parser instance.

## DotEnvSettingsSource

```python
DotEnvSettingsSource(
    settings_cls: type[BaseSettings],
    env_file: DotenvType | None = ENV_FILE_SENTINEL,
    env_file_encoding: str | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_nested_delimiter: str | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
)

```

Bases: `EnvSettingsSource`

Source class for loading settings values from env files.

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    env_file: DotenvType | None = ENV_FILE_SENTINEL,
    env_file_encoding: str | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_nested_delimiter: str | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
) -> None:
    self.env_file = env_file if env_file != ENV_FILE_SENTINEL else settings_cls.model_config.get('env_file')
    self.env_file_encoding = (
        env_file_encoding if env_file_encoding is not None else settings_cls.model_config.get('env_file_encoding')
    )
    super().__init__(
        settings_cls,
        case_sensitive,
        env_prefix,
        env_nested_delimiter,
        env_ignore_empty,
        env_parse_none_str,
        env_parse_enums,
    )

```

## EnvSettingsSource

```python
EnvSettingsSource(
    settings_cls: type[BaseSettings],
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_nested_delimiter: str | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
)

```

Bases: `PydanticBaseEnvSettingsSource`

Source class for loading settings values from environment variables.

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_nested_delimiter: str | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
) -> None:
    super().__init__(
        settings_cls, case_sensitive, env_prefix, env_ignore_empty, env_parse_none_str, env_parse_enums
    )
    self.env_nested_delimiter = (
        env_nested_delimiter if env_nested_delimiter is not None else self.config.get('env_nested_delimiter')
    )
    self.env_prefix_len = len(self.env_prefix)

    self.env_vars = self._load_env_vars()

```

### get_field_value

```python
get_field_value(
    field: FieldInfo, field_name: str
) -> tuple[Any, str, bool]

```

Gets the value for field from environment variables and a flag to determine whether value is complex.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `FieldInfo` | The field. | *required* | | `field_name` | `str` | The field name. | *required* |

Returns:

| Type | Description | | --- | --- | | `tuple[Any, str, bool]` | A tuple that contains the value (None if not found), key, and a flag to determine whether value is complex. |

Source code in `pydantic_settings/sources.py`

```python
def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
    """
    Gets the value for field from environment variables and a flag to determine whether value is complex.

    Args:
        field: The field.
        field_name: The field name.

    Returns:
        A tuple that contains the value (`None` if not found), key, and
            a flag to determine whether value is complex.
    """

    env_val: str | None = None
    for field_key, env_name, value_is_complex in self._extract_field_info(field, field_name):
        env_val = self.env_vars.get(env_name)
        if env_val is not None:
            break

    return env_val, field_key, value_is_complex

```

### prepare_field_value

```python
prepare_field_value(
    field_name: str,
    field: FieldInfo,
    value: Any,
    value_is_complex: bool,
) -> Any

```

Prepare value for the field.

- Extract value for nested field.
- Deserialize value to python object for complex field.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `FieldInfo` | The field. | *required* | | `field_name` | `str` | The field name. | *required* |

Returns:

| Type | Description | | --- | --- | | `Any` | A tuple contains prepared value for the field. |

Raises:

| Type | Description | | --- | --- | | `ValuesError` | When There is an error in deserializing value for complex field. |

Source code in `pydantic_settings/sources.py`

```python
def prepare_field_value(self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool) -> Any:
    """
    Prepare value for the field.

    * Extract value for nested field.
    * Deserialize value to python object for complex field.

    Args:
        field: The field.
        field_name: The field name.

    Returns:
        A tuple contains prepared value for the field.

    Raises:
        ValuesError: When There is an error in deserializing value for complex field.
    """
    is_complex, allow_parse_failure = self._field_is_complex(field)
    if self.env_parse_enums:
        enum_val = _annotation_enum_name_to_val(field.annotation, value)
        value = value if enum_val is None else enum_val

    if is_complex or value_is_complex:
        if isinstance(value, EnvNoneType):
            return value
        elif value is None:
            # field is complex but no value found so far, try explode_env_vars
            env_val_built = self.explode_env_vars(field_name, field, self.env_vars)
            if env_val_built:
                return env_val_built
        else:
            # field is complex and there's a value, decode that as JSON, then add explode_env_vars
            try:
                value = self.decode_complex_value(field_name, field, value)
            except ValueError as e:
                if not allow_parse_failure:
                    raise e

            if isinstance(value, dict):
                return deep_update(value, self.explode_env_vars(field_name, field, self.env_vars))
            else:
                return value
    elif value is not None:
        # simplest case, field is not complex, we only need to add the value if it was found
        return value

```

### next_field

```python
next_field(
    field: FieldInfo | Any | None,
    key: str,
    case_sensitive: bool | None = None,
) -> FieldInfo | None

```

Find the field in a sub model by key(env name)

By having the following models:

````text
```py
class SubSubModel(BaseSettings):
    dvals: Dict

class SubModel(BaseSettings):
    vals: list[str]
    sub_sub_model: SubSubModel

class Cfg(BaseSettings):
    sub_model: SubModel
````

````

Then

next_field(sub_model, 'vals') Returns the `vals` field of `SubModel` class
next_field(sub_model, 'sub_sub_model') Returns `sub_sub_model` field of `SubModel` class

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `field` | `FieldInfo | Any | None` | The field. | *required* |
| `key` | `str` | The key (env name). | *required* |
| `case_sensitive` | `bool | None` | Whether to search for key case sensitively. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `FieldInfo | None` | Field if it finds the next field otherwise None. |

Source code in `pydantic_settings/sources.py`

```python
def next_field(
    self, field: FieldInfo | Any | None, key: str, case_sensitive: bool | None = None
) -> FieldInfo | None:
    """
    Find the field in a sub model by key(env name)

    By having the following models:

        ```py
        class SubSubModel(BaseSettings):
            dvals: Dict

        class SubModel(BaseSettings):
            vals: list[str]
            sub_sub_model: SubSubModel

        class Cfg(BaseSettings):
            sub_model: SubModel
        ```

    Then:
        next_field(sub_model, 'vals') Returns the `vals` field of `SubModel` class
        next_field(sub_model, 'sub_sub_model') Returns `sub_sub_model` field of `SubModel` class

    Args:
        field: The field.
        key: The key (env name).
        case_sensitive: Whether to search for key case sensitively.

    Returns:
        Field if it finds the next field otherwise `None`.
    """
    if not field:
        return None

    annotation = field.annotation if isinstance(field, FieldInfo) else field
    if origin_is_union(get_origin(annotation)) or isinstance(annotation, WithArgsTypes):
        for type_ in get_args(annotation):
            type_has_key = self.next_field(type_, key, case_sensitive)
            if type_has_key:
                return type_has_key
    elif is_model_class(annotation) or is_pydantic_dataclass(annotation):
        fields = _get_model_fields(annotation)
        # `case_sensitive is None` is here to be compatible with the old behavior.
        # Has to be removed in V3.
        for field_name, f in fields.items():
            for _, env_name, _ in self._extract_field_info(f, field_name):
                if case_sensitive is None or case_sensitive:
                    if field_name == key or env_name == key:
                        return f
                elif field_name.lower() == key.lower() or env_name.lower() == key.lower():
                    return f
    return None

````

### explode_env_vars

```python
explode_env_vars(
    field_name: str,
    field: FieldInfo,
    env_vars: Mapping[str, str | None],
) -> dict[str, Any]

```

Process env_vars and extract the values of keys containing env_nested_delimiter into nested dictionaries.

This is applied to a single field, hence filtering by env_var prefix.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field_name` | `str` | The field name. | *required* | | `field` | `FieldInfo` | The field. | *required* | | `env_vars` | `Mapping[str, str | None]` | Environment variables. | *required* |

Returns:

| Type | Description | | --- | --- | | `dict[str, Any]` | A dictionary contains extracted values from nested env values. |

Source code in `pydantic_settings/sources.py`

```python
def explode_env_vars(self, field_name: str, field: FieldInfo, env_vars: Mapping[str, str | None]) -> dict[str, Any]:
    """
    Process env_vars and extract the values of keys containing env_nested_delimiter into nested dictionaries.

    This is applied to a single field, hence filtering by env_var prefix.

    Args:
        field_name: The field name.
        field: The field.
        env_vars: Environment variables.

    Returns:
        A dictionary contains extracted values from nested env values.
    """
    is_dict = lenient_issubclass(get_origin(field.annotation), dict)

    prefixes = [
        f'{env_name}{self.env_nested_delimiter}' for _, env_name, _ in self._extract_field_info(field, field_name)
    ]
    result: dict[str, Any] = {}
    for env_name, env_val in env_vars.items():
        if not any(env_name.startswith(prefix) for prefix in prefixes):
            continue
        # we remove the prefix before splitting in case the prefix has characters in common with the delimiter
        env_name_without_prefix = env_name[self.env_prefix_len :]
        _, *keys, last_key = env_name_without_prefix.split(self.env_nested_delimiter)
        env_var = result
        target_field: FieldInfo | None = field
        for key in keys:
            target_field = self.next_field(target_field, key, self.case_sensitive)
            if isinstance(env_var, dict):
                env_var = env_var.setdefault(key, {})

        # get proper field with last_key
        target_field = self.next_field(target_field, last_key, self.case_sensitive)

        # check if env_val maps to a complex field and if so, parse the env_val
        if (target_field or is_dict) and env_val:
            if target_field:
                is_complex, allow_json_failure = self._field_is_complex(target_field)
            else:
                # nested field type is dict
                is_complex, allow_json_failure = True, True
            if is_complex:
                try:
                    env_val = self.decode_complex_value(last_key, target_field, env_val)  # type: ignore
                except ValueError as e:
                    if not allow_json_failure:
                        raise e
        if isinstance(env_var, dict):
            if last_key not in env_var or not isinstance(env_val, EnvNoneType) or env_var[last_key] == {}:
                env_var[last_key] = env_val

    return result

```

## ForceDecode

Annotation to force decoding of a field value.

## InitSettingsSource

```python
InitSettingsSource(
    settings_cls: type[BaseSettings],
    init_kwargs: dict[str, Any],
    nested_model_default_partial_update: bool | None = None,
)

```

Bases: `PydanticBaseSettingsSource`

Source class for loading values provided during settings class initialization.

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    init_kwargs: dict[str, Any],
    nested_model_default_partial_update: bool | None = None,
):
    self.init_kwargs = init_kwargs
    super().__init__(settings_cls)
    self.nested_model_default_partial_update = (
        nested_model_default_partial_update
        if nested_model_default_partial_update is not None
        else self.config.get('nested_model_default_partial_update', False)
    )

```

## JsonConfigSettingsSource

```python
JsonConfigSettingsSource(
    settings_cls: type[BaseSettings],
    json_file: PathType | None = DEFAULT_PATH,
    json_file_encoding: str | None = None,
)

```

Bases: `InitSettingsSource`, `ConfigFileSourceMixin`

A source class that loads variables from a JSON file

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    json_file: PathType | None = DEFAULT_PATH,
    json_file_encoding: str | None = None,
):
    self.json_file_path = json_file if json_file != DEFAULT_PATH else settings_cls.model_config.get('json_file')
    self.json_file_encoding = (
        json_file_encoding
        if json_file_encoding is not None
        else settings_cls.model_config.get('json_file_encoding')
    )
    self.json_data = self._read_files(self.json_file_path)
    super().__init__(settings_cls, self.json_data)

```

## NoDecode

Annotation to prevent decoding of a field value.

## PydanticBaseSettingsSource

```python
PydanticBaseSettingsSource(
    settings_cls: type[BaseSettings],
)

```

Bases: `ABC`

Abstract base class for settings sources, every settings source classes should inherit from it.

Source code in `pydantic_settings/sources.py`

```python
def __init__(self, settings_cls: type[BaseSettings]):
    self.settings_cls = settings_cls
    self.config = settings_cls.model_config
    self._current_state: dict[str, Any] = {}
    self._settings_sources_data: dict[str, dict[str, Any]] = {}

```

### current_state

```python
current_state: dict[str, Any]

```

The current state of the settings, populated by the previous settings sources.

### settings_sources_data

```python
settings_sources_data: dict[str, dict[str, Any]]

```

The state of all previous settings sources.

### get_field_value

```python
get_field_value(
    field: FieldInfo, field_name: str
) -> tuple[Any, str, bool]

```

Gets the value, the key for model creation, and a flag to determine whether value is complex.

This is an abstract method that should be overridden in every settings source classes.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `FieldInfo` | The field. | *required* | | `field_name` | `str` | The field name. | *required* |

Returns:

| Type | Description | | --- | --- | | `tuple[Any, str, bool]` | A tuple that contains the value, key and a flag to determine whether value is complex. |

Source code in `pydantic_settings/sources.py`

```python
@abstractmethod
def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
    """
    Gets the value, the key for model creation, and a flag to determine whether value is complex.

    This is an abstract method that should be overridden in every settings source classes.

    Args:
        field: The field.
        field_name: The field name.

    Returns:
        A tuple that contains the value, key and a flag to determine whether value is complex.
    """
    pass

```

### field_is_complex

```python
field_is_complex(field: FieldInfo) -> bool

```

Checks whether a field is complex, in which case it will attempt to be parsed as JSON.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `FieldInfo` | The field. | *required* |

Returns:

| Type | Description | | --- | --- | | `bool` | Whether the field is complex. |

Source code in `pydantic_settings/sources.py`

```python
def field_is_complex(self, field: FieldInfo) -> bool:
    """
    Checks whether a field is complex, in which case it will attempt to be parsed as JSON.

    Args:
        field: The field.

    Returns:
        Whether the field is complex.
    """
    return _annotation_is_complex(field.annotation, field.metadata)

```

### prepare_field_value

```python
prepare_field_value(
    field_name: str,
    field: FieldInfo,
    value: Any,
    value_is_complex: bool,
) -> Any

```

Prepares the value of a field.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field_name` | `str` | The field name. | *required* | | `field` | `FieldInfo` | The field. | *required* | | `value` | `Any` | The value of the field that has to be prepared. | *required* | | `value_is_complex` | `bool` | A flag to determine whether value is complex. | *required* |

Returns:

| Type | Description | | --- | --- | | `Any` | The prepared value. |

Source code in `pydantic_settings/sources.py`

```python
def prepare_field_value(self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool) -> Any:
    """
    Prepares the value of a field.

    Args:
        field_name: The field name.
        field: The field.
        value: The value of the field that has to be prepared.
        value_is_complex: A flag to determine whether value is complex.

    Returns:
        The prepared value.
    """
    if value is not None and (self.field_is_complex(field) or value_is_complex):
        return self.decode_complex_value(field_name, field, value)
    return value

```

### decode_complex_value

```python
decode_complex_value(
    field_name: str, field: FieldInfo, value: Any
) -> Any

```

Decode the value for a complex field

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field_name` | `str` | The field name. | *required* | | `field` | `FieldInfo` | The field. | *required* | | `value` | `Any` | The value of the field that has to be prepared. | *required* |

Returns:

| Type | Description | | --- | --- | | `Any` | The decoded value for further preparation |

Source code in `pydantic_settings/sources.py`

```python
def decode_complex_value(self, field_name: str, field: FieldInfo, value: Any) -> Any:
    """
    Decode the value for a complex field

    Args:
        field_name: The field name.
        field: The field.
        value: The value of the field that has to be prepared.

    Returns:
        The decoded value for further preparation
    """
    if field and (
        NoDecode in field.metadata
        or (self.config.get('enable_decoding') is False and ForceDecode not in field.metadata)
    ):
        return value

    return json.loads(value)

```

## PyprojectTomlConfigSettingsSource

```python
PyprojectTomlConfigSettingsSource(
    settings_cls: type[BaseSettings],
    toml_file: Path | None = None,
)

```

Bases: `TomlConfigSettingsSource`

A source class that loads variables from a `pyproject.toml` file.

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    toml_file: Path | None = None,
) -> None:
    self.toml_file_path = self._pick_pyproject_toml_file(
        toml_file, settings_cls.model_config.get('pyproject_toml_depth', 0)
    )
    self.toml_table_header: tuple[str, ...] = settings_cls.model_config.get(
        'pyproject_toml_table_header', ('tool', 'pydantic-settings')
    )
    self.toml_data = self._read_files(self.toml_file_path)
    for key in self.toml_table_header:
        self.toml_data = self.toml_data.get(key, {})
    super(TomlConfigSettingsSource, self).__init__(settings_cls, self.toml_data)

```

## SecretsSettingsSource

```python
SecretsSettingsSource(
    settings_cls: type[BaseSettings],
    secrets_dir: PathType | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
)

```

Bases: `PydanticBaseEnvSettingsSource`

Source class for loading settings values from secret files.

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    secrets_dir: PathType | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
) -> None:
    super().__init__(
        settings_cls, case_sensitive, env_prefix, env_ignore_empty, env_parse_none_str, env_parse_enums
    )
    self.secrets_dir = secrets_dir if secrets_dir is not None else self.config.get('secrets_dir')

```

### find_case_path

```python
find_case_path(
    dir_path: Path, file_name: str, case_sensitive: bool
) -> Path | None

```

Find a file within path's directory matching filename, optionally ignoring case.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `dir_path` | `Path` | Directory path. | *required* | | `file_name` | `str` | File name. | *required* | | `case_sensitive` | `bool` | Whether to search for file name case sensitively. | *required* |

Returns:

| Type | Description | | --- | --- | | `Path | None` | Whether file path or None if file does not exist in directory. |

Source code in `pydantic_settings/sources.py`

```python
@classmethod
def find_case_path(cls, dir_path: Path, file_name: str, case_sensitive: bool) -> Path | None:
    """
    Find a file within path's directory matching filename, optionally ignoring case.

    Args:
        dir_path: Directory path.
        file_name: File name.
        case_sensitive: Whether to search for file name case sensitively.

    Returns:
        Whether file path or `None` if file does not exist in directory.
    """
    for f in dir_path.iterdir():
        if f.name == file_name:
            return f
        elif not case_sensitive and f.name.lower() == file_name.lower():
            return f
    return None

```

### get_field_value

```python
get_field_value(
    field: FieldInfo, field_name: str
) -> tuple[Any, str, bool]

```

Gets the value for field from secret file and a flag to determine whether value is complex.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `FieldInfo` | The field. | *required* | | `field_name` | `str` | The field name. | *required* |

Returns:

| Type | Description | | --- | --- | | `tuple[Any, str, bool]` | A tuple that contains the value (None if the file does not exist), key, and a flag to determine whether value is complex. |

Source code in `pydantic_settings/sources.py`

```python
def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
    """
    Gets the value for field from secret file and a flag to determine whether value is complex.

    Args:
        field: The field.
        field_name: The field name.

    Returns:
        A tuple that contains the value (`None` if the file does not exist), key, and
            a flag to determine whether value is complex.
    """

    for field_key, env_name, value_is_complex in self._extract_field_info(field, field_name):
        # paths reversed to match the last-wins behaviour of `env_file`
        for secrets_path in reversed(self.secrets_paths):
            path = self.find_case_path(secrets_path, env_name, self.case_sensitive)
            if not path:
                # path does not exist, we currently don't return a warning for this
                continue

            if path.is_file():
                return path.read_text().strip(), field_key, value_is_complex
            else:
                warnings.warn(
                    f'attempted to load secret file "{path}" but found a {path_type_label(path)} instead.',
                    stacklevel=4,
                )

    return None, field_key, value_is_complex

```

## TomlConfigSettingsSource

```python
TomlConfigSettingsSource(
    settings_cls: type[BaseSettings],
    toml_file: PathType | None = DEFAULT_PATH,
)

```

Bases: `InitSettingsSource`, `ConfigFileSourceMixin`

A source class that loads variables from a TOML file

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    toml_file: PathType | None = DEFAULT_PATH,
):
    self.toml_file_path = toml_file if toml_file != DEFAULT_PATH else settings_cls.model_config.get('toml_file')
    self.toml_data = self._read_files(self.toml_file_path)
    super().__init__(settings_cls, self.toml_data)

```

## YamlConfigSettingsSource

```python
YamlConfigSettingsSource(
    settings_cls: type[BaseSettings],
    yaml_file: PathType | None = DEFAULT_PATH,
    yaml_file_encoding: str | None = None,
)

```

Bases: `InitSettingsSource`, `ConfigFileSourceMixin`

A source class that loads variables from a yaml file

Source code in `pydantic_settings/sources.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    yaml_file: PathType | None = DEFAULT_PATH,
    yaml_file_encoding: str | None = None,
):
    self.yaml_file_path = yaml_file if yaml_file != DEFAULT_PATH else settings_cls.model_config.get('yaml_file')
    self.yaml_file_encoding = (
        yaml_file_encoding
        if yaml_file_encoding is not None
        else settings_cls.model_config.get('yaml_file_encoding')
    )
    self.yaml_data = self._read_files(self.yaml_file_path)
    super().__init__(settings_cls, self.yaml_data)

```

## get_subcommand

```python
get_subcommand(
    model: PydanticModel,
    is_required: bool = True,
    cli_exit_on_error: bool | None = None,
) -> Optional[PydanticModel]

```

Get the subcommand from a model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `PydanticModel` | The model to get the subcommand from. | *required* | | `is_required` | `bool` | Determines whether a model must have subcommand set and raises error if not found. Defaults to True. | `True` | | `cli_exit_on_error` | `bool | None` | Determines whether this function exits with error if no subcommand is found. Defaults to model_config cli_exit_on_error value if set. Otherwise, defaults to True. | `None` |

Returns:

| Type | Description | | --- | --- | | `Optional[PydanticModel]` | The subcommand model if found, otherwise None. |

Raises:

| Type | Description | | --- | --- | | `SystemExit` | When no subcommand is found and is_required=True and cli_exit_on_error=True (the default). | | `SettingsError` | When no subcommand is found and is_required=True and cli_exit_on_error=False. |

Source code in `pydantic_settings/sources.py`

```python
def get_subcommand(
    model: PydanticModel, is_required: bool = True, cli_exit_on_error: bool | None = None
) -> Optional[PydanticModel]:
    """
    Get the subcommand from a model.

    Args:
        model: The model to get the subcommand from.
        is_required: Determines whether a model must have subcommand set and raises error if not
            found. Defaults to `True`.
        cli_exit_on_error: Determines whether this function exits with error if no subcommand is found.
            Defaults to model_config `cli_exit_on_error` value if set. Otherwise, defaults to `True`.

    Returns:
        The subcommand model if found, otherwise `None`.

    Raises:
        SystemExit: When no subcommand is found and is_required=`True` and cli_exit_on_error=`True`
            (the default).
        SettingsError: When no subcommand is found and is_required=`True` and
            cli_exit_on_error=`False`.
    """

    model_cls = type(model)
    if cli_exit_on_error is None and is_model_class(model_cls):
        model_default = model_cls.model_config.get('cli_exit_on_error')
        if isinstance(model_default, bool):
            cli_exit_on_error = model_default
    if cli_exit_on_error is None:
        cli_exit_on_error = True

    subcommands: list[str] = []
    for field_name, field_info in _get_model_fields(model_cls).items():
        if _CliSubCommand in field_info.metadata:
            if getattr(model, field_name) is not None:
                return getattr(model, field_name)
            subcommands.append(field_name)

    if is_required:
        error_message = (
            f'Error: CLI subcommand is required {{{", ".join(subcommands)}}}'
            if subcommands
            else 'Error: CLI subcommand is required but no subcommands were found.'
        )
        raise SystemExit(error_message) if cli_exit_on_error else SettingsError(error_message)

    return None

```
