## SettingsError

Bases: `ValueError`

Base exception for settings-related errors.

## BaseSettings

```python
BaseSettings(
    __pydantic_self__,
    _case_sensitive: bool | None = None,
    _nested_model_default_partial_update: (
        bool | None
    ) = None,
    _env_prefix: str | None = None,
    _env_prefix_target: EnvPrefixTarget | None = None,
    _env_file: DotenvType | None = ENV_FILE_SENTINEL,
    _env_file_encoding: str | None = None,
    _env_ignore_empty: bool | None = None,
    _env_nested_delimiter: str | None = None,
    _env_nested_max_split: int | None = None,
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
    _cli_implicit_flags: (
        bool | Literal["dual", "toggle"] | None
    ) = None,
    _cli_ignore_unknown_args: bool | None = None,
    _cli_kebab_case: (
        bool | Literal["all", "no_enums"] | None
    ) = None,
    _cli_shortcuts: (
        Mapping[str, str | list[str]] | None
    ) = None,
    _secrets_dir: PathType | None = None,
    _build_sources: (
        tuple[
            tuple[PydanticBaseSettingsSource, ...],
            dict[str, Any],
        ]
        | None
    ) = None,
    **values: Any
)

```

Bases: `BaseModel`

Base class for settings, allowing values to be overridden by environment variables.

This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose), Heroku and any 12 factor app design.

All the below attributes can be set via `model_config`.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `_case_sensitive` | `bool | None` | Whether environment and CLI variable names should be read with case-sensitivity. Defaults to None. | `None` | | `_nested_model_default_partial_update` | `bool | None` | Whether to allow partial updates on nested model default object fields. Defaults to False. | `None` | | `_env_prefix` | `str | None` | Prefix for all environment variables. Defaults to None. | `None` | | `_env_prefix_target` | `EnvPrefixTarget | None` | Targets to which \_env_prefix is applied. Default: variable. | `None` | | `_env_file` | `DotenvType | None` | The env file(s) to load settings values from. Defaults to Path(''), which means that the value from model_config['env_file'] should be used. You can also pass None to indicate that environment variables should not be loaded from an env file. | `ENV_FILE_SENTINEL` | | `_env_file_encoding` | `str | None` | The env file encoding, e.g. 'latin-1'. Defaults to None. | `None` | | `_env_ignore_empty` | `bool | None` | Ignore environment variables where the value is an empty string. Default to False. | `None` | | `_env_nested_delimiter` | `str | None` | The nested env values delimiter. Defaults to None. | `None` | | `_env_nested_max_split` | `int | None` | The nested env values maximum nesting. Defaults to None, which means no limit. | `None` | | `_env_parse_none_str` | `str | None` | The env string value that should be parsed (e.g. "null", "void", "None", etc.) into None type(None). Defaults to None type(None), which means no parsing should occur. | `None` | | `_env_parse_enums` | `bool | None` | Parse enum field names to values. Defaults to None., which means no parsing should occur. | `None` | | `_cli_prog_name` | `str | None` | The CLI program name to display in help text. Defaults to None if \_cli_parse_args is None. Otherwise, defaults to sys.argv[0]. | `None` | | `_cli_parse_args` | `bool | list[str] | tuple[str, ...] | None` | The list of CLI arguments to parse. Defaults to None. If set to True, defaults to sys.argv[1:]. | `None` | | `_cli_settings_source` | `CliSettingsSource[Any] | None` | Override the default CLI settings source with a user defined instance. Defaults to None. | `None` | | `_cli_parse_none_str` | `str | None` | The CLI string value that should be parsed (e.g. "null", "void", "None", etc.) into None type(None). Defaults to \_env_parse_none_str value if set. Otherwise, defaults to "null" if \_cli_avoid_json is False, and "None" if \_cli_avoid_json is True. | `None` | | `_cli_hide_none_type` | `bool | None` | Hide None values in CLI help text. Defaults to False. | `None` | | `_cli_avoid_json` | `bool | None` | Avoid complex JSON objects in CLI help text. Defaults to False. | `None` | | `_cli_enforce_required` | `bool | None` | Enforce required fields at the CLI. Defaults to False. | `None` | | `_cli_use_class_docs_for_groups` | `bool | None` | Use class docstrings in CLI group help text instead of field descriptions. Defaults to False. | `None` | | `_cli_exit_on_error` | `bool | None` | Determines whether or not the internal parser exits with error info when an error occurs. Defaults to True. | `None` | | `_cli_prefix` | `str | None` | The root parser command line arguments prefix. Defaults to "". | `None` | | `_cli_flag_prefix_char` | `str | None` | The flag prefix character to use for CLI optional arguments. Defaults to '-'. | `None` | | `_cli_implicit_flags` | `bool | Literal['dual', 'toggle'] | None` | Controls how bool fields are exposed as CLI flags. False (default): no implicit flags are generated; booleans must be set explicitly (e.g. --flag=true). True / 'dual': optional boolean fields generate both positive and negative forms (--flag and --no-flag). 'toggle': required boolean fields remain in 'dual' mode, while optional boolean fields generate a single flag aligned with the default value (if default=False, expose --flag; if default=True, expose --no-flag). | `None` | | `_cli_ignore_unknown_args` | `bool | None` | Whether to ignore unknown CLI args and parse only known ones. Defaults to False. | `None` | | `_cli_kebab_case` | `bool | Literal['all', 'no_enums'] | None` | CLI args use kebab case. Defaults to False. | `None` | | `_cli_shortcuts` | `Mapping[str, str | list[str]] | None` | Mapping of target field name to alias names. Defaults to None. | `None` | | `_secrets_dir` | `PathType | None` | The secret files directory or a sequence of directories. Defaults to None. | `None` | | `_build_sources` | `tuple[tuple[PydanticBaseSettingsSource, ...], dict[str, Any]] | None` | Pre-initialized sources and init kwargs to use for building instantiation values. Defaults to None. | `None` |

Source code in `pydantic_settings/main.py`

```python
def __init__(
    __pydantic_self__,
    _case_sensitive: bool | None = None,
    _nested_model_default_partial_update: bool | None = None,
    _env_prefix: str | None = None,
    _env_prefix_target: EnvPrefixTarget | None = None,
    _env_file: DotenvType | None = ENV_FILE_SENTINEL,
    _env_file_encoding: str | None = None,
    _env_ignore_empty: bool | None = None,
    _env_nested_delimiter: str | None = None,
    _env_nested_max_split: int | None = None,
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
    _cli_implicit_flags: bool | Literal['dual', 'toggle'] | None = None,
    _cli_ignore_unknown_args: bool | None = None,
    _cli_kebab_case: bool | Literal['all', 'no_enums'] | None = None,
    _cli_shortcuts: Mapping[str, str | list[str]] | None = None,
    _secrets_dir: PathType | None = None,
    _build_sources: tuple[tuple[PydanticBaseSettingsSource, ...], dict[str, Any]] | None = None,
    **values: Any,
) -> None:
    sources, init_kwargs = (
        _build_sources
        if _build_sources is not None
        else __pydantic_self__.__class__._settings_init_sources(
            _case_sensitive=_case_sensitive,
            _nested_model_default_partial_update=_nested_model_default_partial_update,
            _env_prefix=_env_prefix,
            _env_prefix_target=_env_prefix_target,
            _env_file=_env_file,
            _env_file_encoding=_env_file_encoding,
            _env_ignore_empty=_env_ignore_empty,
            _env_nested_delimiter=_env_nested_delimiter,
            _env_nested_max_split=_env_nested_max_split,
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
            _cli_shortcuts=_cli_shortcuts,
            _secrets_dir=_secrets_dir,
            _init_kwargs=values,
        )
    )

    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))

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

    if not issubclass(model_cls, BaseSettings):
        base_settings_cls = CliApp._get_base_settings_cls(model_cls)
        sources, init_kwargs = base_settings_cls._settings_init_sources(
            _cli_parse_args=cli_parse_args,  # type: ignore[arg-type]
            _cli_exit_on_error=cli_exit_on_error,
            _cli_settings_source=cli_settings,
            _init_kwargs=model_init_data,
        )
        model = base_settings_cls(**base_settings_cls._settings_build_values(sources, init_kwargs))
        model_init_data = {}
        for field_name, field_info in base_settings_cls.model_fields.items():
            model_init_data[_field_name_for_signature(field_name, field_info)] = getattr(model, field_name)
        command = model_cls(**model_init_data)
    else:
        sources, init_kwargs = model_cls._settings_init_sources(
            _cli_parse_args=cli_parse_args,  # type: ignore[arg-type]
            _cli_exit_on_error=cli_exit_on_error,
            _cli_settings_source=cli_settings,
            _init_kwargs=model_init_data,
        )
        command = model_cls(_build_sources=(sources, init_kwargs))

    subcommand_dest = ':subcommand'
    cli_settings_source = [source for source in sources if isinstance(source, CliSettingsSource)][0]
    CliApp._subcommand_stack[id(command)] = (cli_settings_source, cli_settings_source.root_parser, subcommand_dest)
    try:
        data_model = CliApp._run_cli_cmd(command, cli_cmd_method_name, is_required=False)
    finally:
        del CliApp._subcommand_stack[id(command)]
    return data_model

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

    if id(model) in CliApp._subcommand_stack:
        cli_settings_source, parser, subcommand_dest = CliApp._subcommand_stack[id(model)]
    else:
        cli_settings_source = CliSettingsSource[Any](CliApp._get_base_settings_cls(type(model)))
        parser = cli_settings_source.root_parser
        subcommand_dest = ':subcommand'

    cli_exit_on_error = cli_settings_source.cli_exit_on_error if cli_exit_on_error is None else cli_exit_on_error

    errors: list[SettingsError | SystemExit] = []
    subcommand = get_subcommand(
        model, is_required=True, cli_exit_on_error=cli_exit_on_error, _suppress_errors=errors
    )
    if errors:
        err = errors[0]
        if err.__context__ is None and err.__cause__ is None and cli_settings_source._format_help is not None:
            error_message = f'{err}\n{cli_settings_source._format_help(parser)}'
            raise type(err)(error_message) from None
        else:
            raise err

    subcommand_cls = cast(type[BaseModel], type(subcommand))
    subcommand_arg = cli_settings_source._parser_map[subcommand_dest][subcommand_cls]
    subcommand_dest = f'{subcommand_arg.dest}.:subcommand'
    subcommand_parser = subcommand_arg.parser
    CliApp._subcommand_stack[id(subcommand)] = (cli_settings_source, subcommand_parser, subcommand_dest)
    try:
        data_model = CliApp._run_cli_cmd(subcommand, cli_cmd_method_name, is_required=True)
    finally:
        del CliApp._subcommand_stack[id(subcommand)]
    return data_model

```

### serialize

```python
serialize(
    model: PydanticModel,
    list_style: Literal[
        "json", "argparse", "lazy"
    ] = "json",
    dict_style: Literal["json", "env"] = "json",
    positionals_first: bool = False,
) -> list[str]

```

Serializes the CLI arguments for a Pydantic data model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `PydanticModel` | The data model to serialize. | *required* | | `list_style` | `Literal['json', 'argparse', 'lazy']` | Controls how list-valued fields are serialized on the command line. - 'json' (default): Lists are encoded as a single JSON array. Example: --tags '["a","b","c"]' - 'argparse': Each list element becomes its own repeated flag, following typical argparse conventions. Example: --tags a --tags b --tags c - 'lazy': Lists are emitted as a single comma-separated string without JSON quoting or escaping. Example: --tags a,b,c | `'json'` | | `dict_style` | `Literal['json', 'env']` | Controls how dictionary-valued fields are serialized. - 'json' (default): The entire dictionary is emitted as a single JSON object. Example: --config '{"host": "localhost", "port": 5432}' - 'env': The dictionary is flattened into multiple CLI flags using environment-variable-style assignement. Example: --config host=localhost --config port=5432 | `'json'` | | `positionals_first` | `bool` | Controls whether positional arguments should be serialized first compared to optional arguments. Defaults to False. | `False` |

Returns:

| Type | Description | | --- | --- | | `list[str]` | The serialized CLI arguments for the data model. |

Source code in `pydantic_settings/main.py`

```python
@staticmethod
def serialize(
    model: PydanticModel,
    list_style: Literal['json', 'argparse', 'lazy'] = 'json',
    dict_style: Literal['json', 'env'] = 'json',
    positionals_first: bool = False,
) -> list[str]:
    """
    Serializes the CLI arguments for a Pydantic data model.

    Args:
        model: The data model to serialize.
        list_style:
            Controls how list-valued fields are serialized on the command line.
            - 'json' (default):
              Lists are encoded as a single JSON array.
              Example: `--tags '["a","b","c"]'`
            - 'argparse':
              Each list element becomes its own repeated flag, following
              typical `argparse` conventions.
              Example: `--tags a --tags b --tags c`
            - 'lazy':
              Lists are emitted as a single comma-separated string without JSON
              quoting or escaping.
              Example: `--tags a,b,c`
        dict_style:
            Controls how dictionary-valued fields are serialized.
            - 'json' (default):
              The entire dictionary is emitted as a single JSON object.
              Example: `--config '{"host": "localhost", "port": 5432}'`
            - 'env':
              The dictionary is flattened into multiple CLI flags using
              environment-variable-style assignement.
              Example: `--config host=localhost --config port=5432`
        positionals_first: Controls whether positional arguments should be serialized
            first compared to optional arguments. Defaults to `False`.

    Returns:
        The serialized CLI arguments for the data model.
    """

    base_settings_cls = CliApp._get_base_settings_cls(type(model))
    serialized_args = CliSettingsSource[Any](base_settings_cls)._serialized_args(
        model,
        list_style=list_style,
        dict_style=dict_style,
        positionals_first=positionals_first,
    )
    return CliSettingsSource._flatten_serialized_args(serialized_args, positionals_first)

```

### format_help

```python
format_help(
    model: PydanticModel | type[T],
    cli_settings_source: (
        CliSettingsSource[Any] | None
    ) = None,
    strip_ansi_color: bool = False,
) -> str

```

Return a string containing a help message for a Pydantic model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `PydanticModel | type[T]` | The model or model class. | *required* | | `cli_settings_source` | `CliSettingsSource[Any] | None` | Override the default CLI settings source with a user defined instance. Defaults to None. | `None` | | `strip_ansi_color` | `bool` | Strips ANSI color codes from the help message when set to True. | `False` |

Returns:

| Type | Description | | --- | --- | | `str` | The help message string for the model. |

Source code in `pydantic_settings/main.py`

```python
@staticmethod
def format_help(
    model: PydanticModel | type[T],
    cli_settings_source: CliSettingsSource[Any] | None = None,
    strip_ansi_color: bool = False,
) -> str:
    """
    Return a string containing a help message for a Pydantic model.

    Args:
        model: The model or model class.
        cli_settings_source: Override the default CLI settings source with a user defined instance.
            Defaults to `None`.
        strip_ansi_color: Strips ANSI color codes from the help message when set to `True`.

    Returns:
        The help message string for the model.
    """
    model_cls = model if isinstance(model, type) else type(model)
    if cli_settings_source is None:
        if not isinstance(model, type) and id(model) in CliApp._subcommand_stack:
            cli_settings_source, *_ = CliApp._subcommand_stack[id(model)]
        else:
            cli_settings_source = CliSettingsSource(CliApp._get_base_settings_cls(model_cls))
    help_message = cli_settings_source._format_help(cli_settings_source.root_parser)
    return help_message if not strip_ansi_color else CliApp._ansi_color.sub('', help_message)

```

### print_help

```python
print_help(
    model: PydanticModel | type[T],
    cli_settings_source: (
        CliSettingsSource[Any] | None
    ) = None,
    file: TextIO | None = None,
    strip_ansi_color: bool = False,
) -> None

```

Print a help message for a Pydantic model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `PydanticModel | type[T]` | The model or model class. | *required* | | `cli_settings_source` | `CliSettingsSource[Any] | None` | Override the default CLI settings source with a user defined instance. Defaults to None. | `None` | | `file` | `TextIO | None` | A text stream to which the help message is written. If None, the output is sent to sys.stdout. | `None` | | `strip_ansi_color` | `bool` | Strips ANSI color codes from the help message when set to True. | `False` |

Source code in `pydantic_settings/main.py`

```python
@staticmethod
def print_help(
    model: PydanticModel | type[T],
    cli_settings_source: CliSettingsSource[Any] | None = None,
    file: TextIO | None = None,
    strip_ansi_color: bool = False,
) -> None:
    """
    Print a help message for a Pydantic model.

    Args:
        model: The model or model class.
        cli_settings_source: Override the default CLI settings source with a user defined instance.
            Defaults to `None`.
        file: A text stream to which the help message is written. If `None`, the output is sent to sys.stdout.
        strip_ansi_color: Strips ANSI color codes from the help message when set to `True`.
    """
    print(
        CliApp.format_help(
            model,
            cli_settings_source=cli_settings_source,
            strip_ansi_color=strip_ansi_color,
        ),
        file=file,
    )

```

## SettingsConfigDict

Bases: `ConfigDict`

### yaml_config_section

```python
yaml_config_section: str | None

```

Specifies the section in a YAML file from which to load the settings. Supports dot-notation for nested paths (e.g., 'config.app.settings'). If provided, the settings will be loaded from the specified section. This is useful when the YAML file contains multiple configuration sections and you only want to load a specific subset into your settings model.

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
    cli_implicit_flags: (
        bool | Literal["dual", "toggle"] | None
    ) = None,
    cli_ignore_unknown_args: bool | None = None,
    cli_kebab_case: (
        bool | Literal["all", "no_enums"] | None
    ) = None,
    cli_shortcuts: (
        Mapping[str, str | list[str]] | None
    ) = None,
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
    format_help_method: (
        Callable[..., Any] | None
    ) = format_help,
    formatter_class: Any = RawDescriptionHelpFormatter,
)

```

Bases: `EnvSettingsSource`, `Generic[T]`

Source class for loading settings values from CLI.

Note

A `CliSettingsSource` connects with a `root_parser` object by using the parser methods to add `settings_cls` fields as command line arguments. The `CliSettingsSource` internal parser representation is based upon the `argparse` parsing library, and therefore, requires the parser methods to support the same attributes as their `argparse` library counterparts.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `cli_prog_name` | `str | None` | The CLI program name to display in help text. Defaults to None if cli_parse_args is None. Otherwise, defaults to sys.argv[0]. | `None` | | `cli_parse_args` | `bool | list[str] | tuple[str, ...] | None` | The list of CLI arguments to parse. Defaults to None. If set to True, defaults to sys.argv[1:]. | `None` | | `cli_parse_none_str` | `str | None` | The CLI string value that should be parsed (e.g. "null", "void", "None", etc.) into None type(None). Defaults to "null" if cli_avoid_json is False, and "None" if cli_avoid_json is True. | `None` | | `cli_hide_none_type` | `bool | None` | Hide None values in CLI help text. Defaults to False. | `None` | | `cli_avoid_json` | `bool | None` | Avoid complex JSON objects in CLI help text. Defaults to False. | `None` | | `cli_enforce_required` | `bool | None` | Enforce required fields at the CLI. Defaults to False. | `None` | | `cli_use_class_docs_for_groups` | `bool | None` | Use class docstrings in CLI group help text instead of field descriptions. Defaults to False. | `None` | | `cli_exit_on_error` | `bool | None` | Determines whether or not the internal parser exits with error info when an error occurs. Defaults to True. | `None` | | `cli_prefix` | `str | None` | Prefix for command line arguments added under the root parser. Defaults to "". | `None` | | `cli_flag_prefix_char` | `str | None` | The flag prefix character to use for CLI optional arguments. Defaults to '-'. | `None` | | `cli_implicit_flags` | `bool | Literal['dual', 'toggle'] | None` | Controls how bool fields are exposed as CLI flags. False (default): no implicit flags are generated; booleans must be set explicitly (e.g. --flag=true). True / 'dual': optional boolean fields generate both positive and negative forms (--flag and --no-flag). 'toggle': required boolean fields remain in 'dual' mode, while optional boolean fields generate a single flag aligned with the default value (if default=False, expose --flag; if default=True, expose --no-flag). | `None` | | `cli_ignore_unknown_args` | `bool | None` | Whether to ignore unknown CLI args and parse only known ones. Defaults to False. | `None` | | `cli_kebab_case` | `bool | Literal['all', 'no_enums'] | None` | CLI args use kebab case. Defaults to False. | `None` | | `cli_shortcuts` | `Mapping[str, str | list[str]] | None` | Mapping of target field name to alias names. Defaults to None. | `None` | | `case_sensitive` | `bool | None` | Whether CLI "--arg" names should be read with case-sensitivity. Defaults to True. Note: Case-insensitive matching is only supported on the internal root parser and does not apply to CLI subcommands. | `True` | | `root_parser` | `Any` | The root parser object. | `None` | | `parse_args_method` | `Callable[..., Any] | None` | The root parser parse args method. Defaults to argparse.ArgumentParser.parse_args. | `None` | | `add_argument_method` | `Callable[..., Any] | None` | The root parser add argument method. Defaults to argparse.ArgumentParser.add_argument. | `add_argument` | | `add_argument_group_method` | `Callable[..., Any] | None` | The root parser add argument group method. Defaults to argparse.ArgumentParser.add_argument_group. | `add_argument_group` | | `add_parser_method` | `Callable[..., Any] | None` | The root parser add new parser (sub-command) method. Defaults to argparse.\_SubParsersAction.add_parser. | `add_parser` | | `add_subparsers_method` | `Callable[..., Any] | None` | The root parser add subparsers (sub-commands) method. Defaults to argparse.ArgumentParser.add_subparsers. | `add_subparsers` | | `format_help_method` | `Callable[..., Any] | None` | The root parser format help method. Defaults to argparse.ArgumentParser.format_help. | `format_help` | | `formatter_class` | `Any` | A class for customizing the root parser help text. Defaults to argparse.RawDescriptionHelpFormatter. | `RawDescriptionHelpFormatter` |

Source code in `pydantic_settings/sources/providers/cli.py`

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
    cli_implicit_flags: bool | Literal['dual', 'toggle'] | None = None,
    cli_ignore_unknown_args: bool | None = None,
    cli_kebab_case: bool | Literal['all', 'no_enums'] | None = None,
    cli_shortcuts: Mapping[str, str | list[str]] | None = None,
    case_sensitive: bool | None = True,
    root_parser: Any = None,
    parse_args_method: Callable[..., Any] | None = None,
    add_argument_method: Callable[..., Any] | None = ArgumentParser.add_argument,
    add_argument_group_method: Callable[..., Any] | None = ArgumentParser.add_argument_group,
    add_parser_method: Callable[..., Any] | None = _SubParsersAction.add_parser,
    add_subparsers_method: Callable[..., Any] | None = ArgumentParser.add_subparsers,
    format_help_method: Callable[..., Any] | None = ArgumentParser.format_help,
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
    self.cli_shortcuts = (
        cli_shortcuts if cli_shortcuts is not None else settings_cls.model_config.get('cli_shortcuts', None)
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
        env_nested_max_split=0,
    )

    root_parser = (
        _CliInternalArgParser(
            cli_exit_on_error=self.cli_exit_on_error,
            prog=self.cli_prog_name,
            description=_get_model_description(settings_cls),
            formatter_class=formatter_class,
            prefix_chars=self.cli_flag_prefix_char,
            allow_abbrev=False,
            add_help=False,
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
        format_help_method=format_help_method,
        formatter_class=formatter_class,
    )

    if cli_parse_args not in (None, False):
        if cli_parse_args is True:
            cli_parse_args = sys.argv[1:]
        elif not isinstance(cli_parse_args, (list, tuple)):
            raise SettingsError(
                f'cli_parse_args must be a list or tuple of strings, received {type(cli_parse_args)}'
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
    dotenv_filtering: DotenvFiltering | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_prefix_target: EnvPrefixTarget | None = None,
    env_nested_delimiter: str | None = None,
    env_nested_max_split: int | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
)

```

Bases: `EnvSettingsSource`

Source class for loading settings values from env files.

Source code in `pydantic_settings/sources/providers/dotenv.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    env_file: DotenvType | None = ENV_FILE_SENTINEL,
    env_file_encoding: str | None = None,
    dotenv_filtering: DotenvFiltering | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_prefix_target: EnvPrefixTarget | None = None,
    env_nested_delimiter: str | None = None,
    env_nested_max_split: int | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
) -> None:
    self.env_file = env_file if env_file != ENV_FILE_SENTINEL else settings_cls.model_config.get('env_file')
    self.env_file_encoding = (
        env_file_encoding if env_file_encoding is not None else settings_cls.model_config.get('env_file_encoding')
    )
    self.dotenv_filtering = (
        dotenv_filtering if dotenv_filtering is not None else settings_cls.model_config.get('dotenv_filtering')
    )
    super().__init__(
        settings_cls,
        case_sensitive,
        env_prefix,
        env_prefix_target,
        env_nested_delimiter,
        env_nested_max_split,
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
    env_prefix_target: EnvPrefixTarget | None = None,
    env_nested_delimiter: str | None = None,
    env_nested_max_split: int | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
)

```

Bases: `PydanticBaseEnvSettingsSource`

Source class for loading settings values from environment variables.

Source code in `pydantic_settings/sources/providers/env.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_prefix_target: EnvPrefixTarget | None = None,
    env_nested_delimiter: str | None = None,
    env_nested_max_split: int | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
) -> None:
    super().__init__(
        settings_cls,
        case_sensitive,
        env_prefix,
        env_prefix_target,
        env_ignore_empty,
        env_parse_none_str,
        env_parse_enums,
    )
    self.env_nested_delimiter = (
        env_nested_delimiter if env_nested_delimiter is not None else self.config.get('env_nested_delimiter')
    )
    self.env_nested_max_split = (
        env_nested_max_split if env_nested_max_split is not None else self.config.get('env_nested_max_split')
    )
    self.maxsplit = (self.env_nested_max_split or 0) - 1
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

Source code in `pydantic_settings/sources/providers/env.py`

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

Source code in `pydantic_settings/sources/providers/env.py`

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
        return self._coerce_env_val_strict(field, value)

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

Source code in `pydantic_settings/sources/providers/env.py`

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
    for type_ in get_args(annotation):
        type_has_key = self.next_field(type_, key, case_sensitive)
        if type_has_key:
            return type_has_key
    if _lenient_issubclass(get_origin(annotation), dict):
        # get value type if it's a dict
        return get_args(annotation)[-1]
    elif is_model_class(annotation) or is_pydantic_dataclass(annotation):  # type: ignore[arg-type]
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

Source code in `pydantic_settings/sources/providers/env.py`

```python
def explode_env_vars(self, field_name: str, field: FieldInfo, env_vars: Mapping[str, str | None]) -> dict[str, Any]:  # noqa: C901
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
    if not self.env_nested_delimiter:
        return {}

    ann = field.annotation
    is_dict = ann is dict or _lenient_issubclass(get_origin(ann), dict)

    prefixes = [
        f'{env_name}{self.env_nested_delimiter}' for _, env_name, _ in self._extract_field_info(field, field_name)
    ]
    result: dict[str, Any] = {}
    for env_name, env_val in env_vars.items():
        try:
            prefix = next(prefix for prefix in prefixes if env_name.startswith(prefix))
        except StopIteration:
            continue
        # we remove the prefix before splitting in case the prefix has characters in common with the delimiter
        env_name_without_prefix = env_name[len(prefix) :]
        *keys, last_key = env_name_without_prefix.split(self.env_nested_delimiter, self.maxsplit)
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
            if isinstance(target_field, FieldInfo):
                is_complex, allow_json_failure = self._field_is_complex(target_field)
                if self.env_parse_enums:
                    enum_val = _annotation_enum_name_to_val(target_field.annotation, env_val)
                    env_val = env_val if enum_val is None else enum_val
            elif target_field:
                # target_field is a raw type (e.g. from dict value type annotation)
                is_complex = _annotation_is_complex(target_field, [])
                allow_json_failure = True
            else:
                # nested field type is dict
                is_complex, allow_json_failure = True, True
            if is_complex:
                try:
                    field_info = target_field if isinstance(target_field, FieldInfo) else None
                    env_val = self.decode_complex_value(last_key, field_info, env_val)  # type: ignore
                except ValueError as e:
                    if not allow_json_failure:
                        raise e
        if isinstance(env_var, dict):
            if last_key not in env_var or not isinstance(env_val, EnvNoneType) or env_var[last_key] == {}:
                env_var[last_key] = self._coerce_env_val_strict(target_field, env_val)
    return result

```

## ForceDecode

Annotation to force decoding of a field value.

## GoogleSecretManagerSettingsSource

```python
GoogleSecretManagerSettingsSource(
    settings_cls: type[BaseSettings],
    credentials: Credentials | None = None,
    project_id: str | None = None,
    env_prefix: str | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
    secret_client: SecretManagerServiceClient | None = None,
    case_sensitive: bool | None = True,
)

```

Bases: `EnvSettingsSource`

Source code in `pydantic_settings/sources/providers/gcp.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    credentials: Credentials | None = None,
    project_id: str | None = None,
    env_prefix: str | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
    secret_client: SecretManagerServiceClient | None = None,
    case_sensitive: bool | None = True,
) -> None:
    # Import Google Packages if they haven't already been imported
    if SecretManagerServiceClient is None or Credentials is None or google_auth_default is None:
        import_gcp_secret_manager()

    # If credentials or project_id are not passed, then
    # try to get them from the default function
    if not credentials or not project_id:
        _creds, _project_id = google_auth_default()

    # Set the credentials and/or project id if they weren't specified
    if credentials is None:
        credentials = _creds

    if project_id is None:
        if isinstance(_project_id, str):
            project_id = _project_id
        else:
            raise AttributeError(
                'project_id is required to be specified either as an argument or from the google.auth.default. See https://google-auth.readthedocs.io/en/master/reference/google.auth.html#google.auth.default'
            )

    self._credentials: Credentials = credentials
    self._project_id: str = project_id

    if secret_client:
        self._secret_client = secret_client
    else:
        self._secret_client = SecretManagerServiceClient(credentials=self._credentials)

    super().__init__(
        settings_cls,
        case_sensitive=case_sensitive,
        env_prefix=env_prefix,
        env_ignore_empty=False,
        env_parse_none_str=env_parse_none_str,
        env_parse_enums=env_parse_enums,
    )

```

### get_field_value

```python
get_field_value(
    field: FieldInfo, field_name: str
) -> tuple[Any, str, bool]

```

Override get_field_value to get the secret value from GCP Secret Manager. Look for a SecretVersion metadata field to specify a particular SecretVersion.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `field` | `FieldInfo` | The field to get the value for | *required* | | `field_name` | `str` | The declared name of the field | *required* |

Returns:

| Type | Description | | --- | --- | | `Any` | A tuple of (value, key, value_is_complex), where key is the identifier used | | `str` | to populate the model (either the field name or an alias, depending on | | `bool` | configuration). |

Source code in `pydantic_settings/sources/providers/gcp.py`

```python
def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
    """Override get_field_value to get the secret value from GCP Secret Manager.
    Look for a SecretVersion metadata field to specify a particular SecretVersion.

    Args:
        field: The field to get the value for
        field_name: The declared name of the field

    Returns:
        A tuple of (value, key, value_is_complex), where `key` is the identifier used
        to populate the model (either the field name or an alias, depending on
        configuration).
    """

    secret_version = next((m.version for m in field.metadata if isinstance(m, SecretVersion)), None)

    # If a secret version is specified, try to get that specific version of the secret from
    # GCP Secret Manager via the GoogleSecretManagerMapping. This allows different versions
    # of the same secret name to be retrieved independently and cached in the GoogleSecretManagerMapping
    if secret_version and isinstance(self.env_vars, GoogleSecretManagerMapping):
        for field_key, env_name, value_is_complex in self._extract_field_info(field, field_name):
            gcp_secret_name = self.env_vars._secret_name_map.get(env_name)
            if gcp_secret_name is None and not self.case_sensitive:
                gcp_secret_name = self.env_vars._secret_name_map.get(env_name.lower())

            if gcp_secret_name:
                env_val = self.env_vars._get_secret_value(gcp_secret_name, secret_version)
                if env_val is not None:
                    # If populate_by_name is enabled, return field_name to allow multiple fields
                    # with the same alias but different versions to be distinguished
                    if self.settings_cls.model_config.get('populate_by_name'):
                        return env_val, field_name, value_is_complex
                    return env_val, field_key, value_is_complex

        # If a secret version is specified but not found, we should not fall back to "latest" (default behavior)
        # as that would be incorrect. We return None to indicate the value was not found.
        return None, field_name, False

    val, key, is_complex = super().get_field_value(field, field_name)

    # If populate_by_name is enabled, we need to return the field_name as the key
    # without this being enabled, you cannot load two secrets with the same name but different versions
    if self.settings_cls.model_config.get('populate_by_name') and val is not None:
        return val, field_name, is_complex
    return val, key, is_complex

```

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

Source code in `pydantic_settings/sources/base.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    init_kwargs: dict[str, Any],
    nested_model_default_partial_update: bool | None = None,
):
    self.init_kwargs = {}
    init_kwarg_names = set(init_kwargs.keys())
    for field_name, field_info in settings_cls.model_fields.items():
        alias_names, *_ = _get_alias_names(field_name, field_info)
        # When populate_by_name is True, allow using the field name as an input key,
        # but normalize to the preferred alias to keep keys consistent across sources.
        matchable_names = set(alias_names)
        include_name = settings_cls.model_config.get('populate_by_name', False) or settings_cls.model_config.get(
            'validate_by_name', False
        )
        if include_name:
            matchable_names.add(field_name)
        init_kwarg_name = init_kwarg_names & matchable_names
        if init_kwarg_name:
            preferred_alias = alias_names[0] if alias_names else field_name
            # Choose provided key deterministically: prefer the first alias in alias_names order;
            # fall back to field_name if allowed and provided.
            provided_key = next((alias for alias in alias_names if alias in init_kwarg_names), None)
            if provided_key is None and include_name and field_name in init_kwarg_names:
                provided_key = field_name
            # provided_key should not be None here because init_kwarg_name is non-empty
            assert provided_key is not None
            init_kwarg_names -= init_kwarg_name
            self.init_kwargs[preferred_alias] = init_kwargs[provided_key]
    # Include any remaining init kwargs (e.g., extras) unchanged
    # Note: If populate_by_name is True and the provided key is the field name, but
    # no alias exists, we keep it as-is so it can be processed as extra if allowed.
    self.init_kwargs.update({key: val for key, val in init_kwargs.items() if key in init_kwarg_names})

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
    deep_merge: bool = False,
)

```

Bases: `InitSettingsSource`, `ConfigFileSourceMixin`

A source class that loads variables from a JSON file

Source code in `pydantic_settings/sources/providers/json.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    json_file: PathType | None = DEFAULT_PATH,
    json_file_encoding: str | None = None,
    deep_merge: bool = False,
):
    self.json_file_path = json_file if json_file != DEFAULT_PATH else settings_cls.model_config.get('json_file')
    self.json_file_encoding = (
        json_file_encoding
        if json_file_encoding is not None
        else settings_cls.model_config.get('json_file_encoding')
    )
    self.json_data = self._read_files(self.json_file_path, deep_merge=deep_merge)
    super().__init__(settings_cls, self.json_data)

```

## NestedSecretsSettingsSource

```python
NestedSecretsSettingsSource(
    file_secret_settings: (
        PydanticBaseSettingsSource | SecretsSettingsSource
    ),
    secrets_dir: Optional[PathType] = None,
    secrets_dir_missing: (
        Literal["ok", "warn", "error"] | None
    ) = None,
    secrets_dir_max_size: int | None = None,
    secrets_case_sensitive: bool | None = None,
    secrets_prefix: str | None = None,
    secrets_nested_delimiter: str | None = None,
    secrets_nested_subdir: bool | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
)

```

Bases: `EnvSettingsSource`

Source code in `pydantic_settings/sources/providers/nested_secrets.py`

```python
def __init__(
    self,
    file_secret_settings: PydanticBaseSettingsSource | SecretsSettingsSource,
    secrets_dir: Optional['PathType'] = None,
    secrets_dir_missing: Literal['ok', 'warn', 'error'] | None = None,
    secrets_dir_max_size: int | None = None,
    secrets_case_sensitive: bool | None = None,
    secrets_prefix: str | None = None,
    secrets_nested_delimiter: str | None = None,
    secrets_nested_subdir: bool | None = None,
    # args for compatibility with SecretsSettingsSource, don't use directly
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
) -> None:
    # We allow the first argument to be settings_cls like original
    # SecretsSettingsSource. However, it is recommended to pass
    # SecretsSettingsSource instance instead (as it is shown in usage examples),
    # otherwise `_secrets_dir` arg passed to Settings() constructor will be ignored.
    settings_cls: type[BaseSettings] = getattr(
        file_secret_settings,
        'settings_cls',
        file_secret_settings,  # type: ignore[arg-type]
    )
    # config options
    conf = settings_cls.model_config
    self.secrets_dir: PathType | None = first_not_none(
        getattr(file_secret_settings, 'secrets_dir', None),
        secrets_dir,
        conf.get('secrets_dir'),
    )
    self.secrets_dir_missing: Literal['ok', 'warn', 'error'] = first_not_none(
        secrets_dir_missing,
        conf.get('secrets_dir_missing'),
        'warn',
    )
    if self.secrets_dir_missing not in ('ok', 'warn', 'error'):
        raise SettingsError(f'invalid secrets_dir_missing value: {self.secrets_dir_missing}')
    self.secrets_dir_max_size: int = first_not_none(
        secrets_dir_max_size,
        conf.get('secrets_dir_max_size'),
        SECRETS_DIR_MAX_SIZE,
    )
    self.case_sensitive: bool = first_not_none(
        secrets_case_sensitive,
        conf.get('secrets_case_sensitive'),
        case_sensitive,
        conf.get('case_sensitive'),
        False,
    )
    self.secrets_prefix: str = first_not_none(
        secrets_prefix,
        conf.get('secrets_prefix'),
        env_prefix,
        conf.get('env_prefix'),
        '',
    )

    # nested options
    self.secrets_nested_delimiter: str | None = first_not_none(
        secrets_nested_delimiter,
        conf.get('secrets_nested_delimiter'),
        conf.get('env_nested_delimiter'),
    )
    self.secrets_nested_subdir: bool = first_not_none(
        secrets_nested_subdir,
        conf.get('secrets_nested_subdir'),
        False,
    )
    if self.secrets_nested_subdir:
        if secrets_nested_delimiter or conf.get('secrets_nested_delimiter'):
            raise SettingsError('Options secrets_nested_delimiter and secrets_nested_subdir are mutually exclusive')
        else:
            self.secrets_nested_delimiter = os.sep

    # ensure valid secrets_path
    if self.secrets_dir is None:
        paths = []
    elif isinstance(self.secrets_dir, (Path, str)):
        paths = [self.secrets_dir]
    else:
        paths = list(self.secrets_dir)
    self.secrets_paths: list[Path] = [Path(p).expanduser().resolve() for p in paths]
    for path in self.secrets_paths:
        self.validate_secrets_path(path)

    # construct parent
    super().__init__(
        settings_cls,
        case_sensitive=self.case_sensitive,
        env_prefix=self.secrets_prefix,
        env_nested_delimiter=self.secrets_nested_delimiter,
        env_ignore_empty=False,  # match SecretsSettingsSource behaviour
        env_parse_enums=True,  # we can pass everything here, it will still behave as "True"
        env_parse_none_str=None,  # match SecretsSettingsSource behaviour
    )
    self.env_parse_none_str = None  # update manually because of None

    # update parent members
    if not len(self.secrets_paths):
        self.env_vars = {}
    else:
        secrets = reduce(
            lambda d1, d2: dict((*d1.items(), *d2.items())),
            (self.load_secrets(p) for p in self.secrets_paths),
        )
        self.env_vars = parse_env_vars(
            secrets,
            self.case_sensitive,
            self.env_ignore_empty,
            self.env_parse_none_str,
        )

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

Source code in `pydantic_settings/sources/base.py`

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

Source code in `pydantic_settings/sources/base.py`

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

Source code in `pydantic_settings/sources/base.py`

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

Source code in `pydantic_settings/sources/base.py`

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

Source code in `pydantic_settings/sources/base.py`

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
        NoDecode in _get_field_metadata(field)
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

Source code in `pydantic_settings/sources/providers/pyproject.py`

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
    env_prefix_target: EnvPrefixTarget | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
)

```

Bases: `PydanticBaseEnvSettingsSource`

Source class for loading settings values from secret files.

Source code in `pydantic_settings/sources/providers/secrets.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    secrets_dir: PathType | None = None,
    case_sensitive: bool | None = None,
    env_prefix: str | None = None,
    env_prefix_target: EnvPrefixTarget | None = None,
    env_ignore_empty: bool | None = None,
    env_parse_none_str: str | None = None,
    env_parse_enums: bool | None = None,
) -> None:
    super().__init__(
        settings_cls,
        case_sensitive,
        env_prefix,
        env_prefix_target,
        env_ignore_empty,
        env_parse_none_str,
        env_parse_enums,
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

Source code in `pydantic_settings/sources/providers/secrets.py`

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

Source code in `pydantic_settings/sources/providers/secrets.py`

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
    deep_merge: bool = False,
)

```

Bases: `InitSettingsSource`, `ConfigFileSourceMixin`

A source class that loads variables from a TOML file

Source code in `pydantic_settings/sources/providers/toml.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    toml_file: PathType | None = DEFAULT_PATH,
    deep_merge: bool = False,
):
    self.toml_file_path = toml_file if toml_file != DEFAULT_PATH else settings_cls.model_config.get('toml_file')
    self.toml_data = self._read_files(self.toml_file_path, deep_merge=deep_merge)
    super().__init__(settings_cls, self.toml_data)

```

## YamlConfigSettingsSource

```python
YamlConfigSettingsSource(
    settings_cls: type[BaseSettings],
    yaml_file: PathType | None = DEFAULT_PATH,
    yaml_file_encoding: str | None = None,
    yaml_config_section: str | None = None,
    deep_merge: bool = False,
)

```

Bases: `InitSettingsSource`, `ConfigFileSourceMixin`

A source class that loads variables from a yaml file

Source code in `pydantic_settings/sources/providers/yaml.py`

```python
def __init__(
    self,
    settings_cls: type[BaseSettings],
    yaml_file: PathType | None = DEFAULT_PATH,
    yaml_file_encoding: str | None = None,
    yaml_config_section: str | None = None,
    deep_merge: bool = False,
):
    self.yaml_file_path = yaml_file if yaml_file != DEFAULT_PATH else settings_cls.model_config.get('yaml_file')
    self.yaml_file_encoding = (
        yaml_file_encoding
        if yaml_file_encoding is not None
        else settings_cls.model_config.get('yaml_file_encoding')
    )
    self.yaml_config_section = (
        yaml_config_section
        if yaml_config_section is not None
        else settings_cls.model_config.get('yaml_config_section')
    )
    self.yaml_data = self._read_files(self.yaml_file_path, deep_merge=deep_merge)

    if self.yaml_config_section is not None:
        self.yaml_data = self._traverse_nested_section(
            self.yaml_data, self.yaml_config_section, self.yaml_config_section
        )
    super().__init__(settings_cls, self.yaml_data)

```

## get_subcommand

```python
get_subcommand(
    model: PydanticModel,
    is_required: bool = True,
    cli_exit_on_error: bool | None = None,
    _suppress_errors: (
        list[SettingsError | SystemExit] | None
    ) = None,
) -> PydanticModel | None

```

Get the subcommand from a model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `model` | `PydanticModel` | The model to get the subcommand from. | *required* | | `is_required` | `bool` | Determines whether a model must have subcommand set and raises error if not found. Defaults to True. | `True` | | `cli_exit_on_error` | `bool | None` | Determines whether this function exits with error if no subcommand is found. Defaults to model_config cli_exit_on_error value if set. Otherwise, defaults to True. | `None` |

Returns:

| Type | Description | | --- | --- | | `PydanticModel | None` | The subcommand model if found, otherwise None. |

Raises:

| Type | Description | | --- | --- | | `SystemExit` | When no subcommand is found and is_required=True and cli_exit_on_error=True (the default). | | `SettingsError` | When no subcommand is found and is_required=True and cli_exit_on_error=False. |

Source code in `pydantic_settings/sources/base.py`

```python
def get_subcommand(
    model: PydanticModel,
    is_required: bool = True,
    cli_exit_on_error: bool | None = None,
    _suppress_errors: list[SettingsError | SystemExit] | None = None,
) -> PydanticModel | None:
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
        err = SystemExit(error_message) if cli_exit_on_error else SettingsError(error_message)
        if _suppress_errors is None:
            raise err
        _suppress_errors.append(err)

    return None

```
