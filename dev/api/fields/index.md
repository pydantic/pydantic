Defining fields on models.

## Field

```python
Field(
    default: ellipsis,
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: (
        str | AliasPath | AliasChoices | None
    ) = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: (
        Callable[[str, FieldInfo], str] | None
    ) = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: SupportsGt | None = _Unset,
    ge: SupportsGe | None = _Unset,
    lt: SupportsLt | None = _Unset,
    le: SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal["smart", "left_to_right"] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs]
) -> Any

```

```python
Field(
    default: Any,
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: (
        str | AliasPath | AliasChoices | None
    ) = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: (
        Callable[[str, FieldInfo], str] | None
    ) = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[True],
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: SupportsGt | None = _Unset,
    ge: SupportsGe | None = _Unset,
    lt: SupportsLt | None = _Unset,
    le: SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal["smart", "left_to_right"] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs]
) -> Any

```

```python
Field(
    default: _T,
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: (
        str | AliasPath | AliasChoices | None
    ) = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: (
        Callable[[str, FieldInfo], str] | None
    ) = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[False] = ...,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: SupportsGt | None = _Unset,
    ge: SupportsGe | None = _Unset,
    lt: SupportsLt | None = _Unset,
    le: SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal["smart", "left_to_right"] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs]
) -> _T

```

```python
Field(
    *,
    default_factory: (
        Callable[[], Any] | Callable[[dict[str, Any]], Any]
    ),
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: (
        str | AliasPath | AliasChoices | None
    ) = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: (
        Callable[[str, FieldInfo], str] | None
    ) = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[True],
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: SupportsGt | None = _Unset,
    ge: SupportsGe | None = _Unset,
    lt: SupportsLt | None = _Unset,
    le: SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal["smart", "left_to_right"] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs]
) -> Any

```

```python
Field(
    *,
    default_factory: (
        Callable[[], _T] | Callable[[dict[str, Any]], _T]
    ),
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: (
        str | AliasPath | AliasChoices | None
    ) = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: (
        Callable[[str, FieldInfo], str] | None
    ) = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = _Unset,
    frozen: bool | None = _Unset,
    validate_default: Literal[False] | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: SupportsGt | None = _Unset,
    ge: SupportsGe | None = _Unset,
    lt: SupportsLt | None = _Unset,
    le: SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal["smart", "left_to_right"] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs]
) -> _T

```

```python
Field(
    *,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: (
        str | AliasPath | AliasChoices | None
    ) = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: (
        Callable[[str, FieldInfo], str] | None
    ) = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: SupportsGt | None = _Unset,
    ge: SupportsGe | None = _Unset,
    lt: SupportsLt | None = _Unset,
    le: SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal["smart", "left_to_right"] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs]
) -> Any

```

```python
Field(
    default: Any = PydanticUndefined,
    *,
    default_factory: (
        Callable[[], Any]
        | Callable[[dict[str, Any]], Any]
        | None
    ) = _Unset,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: (
        str | AliasPath | AliasChoices | None
    ) = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: (
        Callable[[str, FieldInfo], str] | None
    ) = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: SupportsGt | None = _Unset,
    ge: SupportsGe | None = _Unset,
    lt: SupportsLt | None = _Unset,
    le: SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal["smart", "left_to_right"] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs]
) -> Any

```

Usage Documentation

[Fields](../../concepts/fields/)

Create a field for objects that can be configured.

Used to provide extra information about a field, either for the model schema or complex validation. Some arguments apply only to number fields (`int`, `float`, `Decimal`) and some apply only to `str`.

Note

- Any `_Unset` objects will be replaced by the corresponding value defined in the `_DefaultValues` dictionary. If a key for the `_Unset` object is not found in the `_DefaultValues` dictionary, it will default to `None`

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `default` | `Any` | Default value if the field is not set. | `PydanticUndefined` | | `default_factory` | `Callable[[], Any] | Callable[[dict[str, Any]], Any] | None` | A callable to generate the default value. The callable can either take 0 arguments (in which case it is called as is) or a single argument containing the already validated data. | `_Unset` | | `alias` | `str | None` | The name to use for the attribute when validating or serializing by alias. This is often used for things like converting between snake and camel case. | `_Unset` | | `alias_priority` | `int | None` | Priority of the alias. This affects whether an alias generator is used. | `_Unset` | | `validation_alias` | `str | AliasPath | AliasChoices | None` | Like alias, but only affects validation, not serialization. | `_Unset` | | `serialization_alias` | `str | None` | Like alias, but only affects serialization, not validation. | `_Unset` | | `title` | `str | None` | Human-readable title. | `_Unset` | | `field_title_generator` | `Callable[[str, FieldInfo], str] | None` | A callable that takes a field name and returns title for it. | `_Unset` | | `description` | `str | None` | Human-readable description. | `_Unset` | | `examples` | `list[Any] | None` | Example values for this field. | `_Unset` | | `exclude` | `bool | None` | Whether to exclude the field from the model serialization. | `_Unset` | | `exclude_if` | `Callable[[Any], bool] | None` | A callable that determines whether to exclude a field during serialization based on its value. | `_Unset` | | `discriminator` | `str | Discriminator | None` | Field name or Discriminator for discriminating the type in a tagged union. | `_Unset` | | `deprecated` | `Deprecated | str | bool | None` | A deprecation message, an instance of warnings.deprecated or the typing_extensions.deprecated backport, or a boolean. If True, a default deprecation message will be emitted when accessing the field. | `_Unset` | | `json_schema_extra` | `JsonDict | Callable[[JsonDict], None] | None` | A dict or callable to provide extra JSON schema properties. | `_Unset` | | `frozen` | `bool | None` | Whether the field is frozen. If true, attempts to change the value on an instance will raise an error. | `_Unset` | | `validate_default` | `bool | None` | If True, apply validation to the default value every time you create an instance. Otherwise, for performance reasons, the default value of the field is trusted and not validated. | `_Unset` | | `repr` | `bool` | A boolean indicating whether to include the field in the __repr__ output. | `_Unset` | | `init` | `bool | None` | Whether the field should be included in the constructor of the dataclass. (Only applies to dataclasses.) | `_Unset` | | `init_var` | `bool | None` | Whether the field should only be included in the constructor of the dataclass. (Only applies to dataclasses.) | `_Unset` | | `kw_only` | `bool | None` | Whether the field should be a keyword-only argument in the constructor of the dataclass. (Only applies to dataclasses.) | `_Unset` | | `coerce_numbers_to_str` | `bool | None` | Whether to enable coercion of any Number type to str (not applicable in strict mode). | `_Unset` | | `strict` | `bool | None` | If True, strict validation is applied to the field. See Strict Mode for details. | `_Unset` | | `gt` | `SupportsGt | None` | Greater than. If set, value must be greater than this. Only applicable to numbers. | `_Unset` | | `ge` | `SupportsGe | None` | Greater than or equal. If set, value must be greater than or equal to this. Only applicable to numbers. | `_Unset` | | `lt` | `SupportsLt | None` | Less than. If set, value must be less than this. Only applicable to numbers. | `_Unset` | | `le` | `SupportsLe | None` | Less than or equal. If set, value must be less than or equal to this. Only applicable to numbers. | `_Unset` | | `multiple_of` | `float | None` | Value must be a multiple of this. Only applicable to numbers. | `_Unset` | | `min_length` | `int | None` | Minimum length for iterables. | `_Unset` | | `max_length` | `int | None` | Maximum length for iterables. | `_Unset` | | `pattern` | `str | Pattern[str] | None` | Pattern for strings (a regular expression). | `_Unset` | | `allow_inf_nan` | `bool | None` | Allow inf, -inf, nan. Only applicable to float and Decimal numbers. | `_Unset` | | `max_digits` | `int | None` | Maximum number of allow digits for strings. | `_Unset` | | `decimal_places` | `int | None` | Maximum number of decimal places allowed for numbers. | `_Unset` | | `union_mode` | `Literal['smart', 'left_to_right']` | The strategy to apply when validating a union. Can be smart (the default), or left_to_right. See Union Mode for details. | `_Unset` | | `fail_fast` | `bool | None` | If True, validation will stop on the first error. If False, all validation errors will be collected. This option can be applied only to iterable types (list, tuple, set, and frozenset). | `_Unset` | | `extra` | `Unpack[_EmptyKwargs]` | (Deprecated) Extra fields that will be included in the JSON schema. Warning The extra kwargs is deprecated. Use json_schema_extra instead. | `{}` |

Returns:

| Type | Description | | --- | --- | | `Any` | A new FieldInfo. The return annotation is Any so Field can be used on type-annotated fields without causing a type error. |

Source code in `pydantic/fields.py`

```python
def Field(  # noqa: C901
    default: Any = PydanticUndefined,
    *,
    default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any] | None = _Unset,
    alias: str | None = _Unset,
    alias_priority: int | None = _Unset,
    validation_alias: str | AliasPath | AliasChoices | None = _Unset,
    serialization_alias: str | None = _Unset,
    title: str | None = _Unset,
    field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
    description: str | None = _Unset,
    examples: list[Any] | None = _Unset,
    exclude: bool | None = _Unset,
    exclude_if: Callable[[Any], bool] | None = _Unset,
    discriminator: str | types.Discriminator | None = _Unset,
    deprecated: Deprecated | str | bool | None = _Unset,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
    frozen: bool | None = _Unset,
    validate_default: bool | None = _Unset,
    repr: bool = _Unset,
    init: bool | None = _Unset,
    init_var: bool | None = _Unset,
    kw_only: bool | None = _Unset,
    pattern: str | re.Pattern[str] | None = _Unset,
    strict: bool | None = _Unset,
    coerce_numbers_to_str: bool | None = _Unset,
    gt: annotated_types.SupportsGt | None = _Unset,
    ge: annotated_types.SupportsGe | None = _Unset,
    lt: annotated_types.SupportsLt | None = _Unset,
    le: annotated_types.SupportsLe | None = _Unset,
    multiple_of: float | None = _Unset,
    allow_inf_nan: bool | None = _Unset,
    max_digits: int | None = _Unset,
    decimal_places: int | None = _Unset,
    min_length: int | None = _Unset,
    max_length: int | None = _Unset,
    union_mode: Literal['smart', 'left_to_right'] = _Unset,
    fail_fast: bool | None = _Unset,
    **extra: Unpack[_EmptyKwargs],
) -> Any:
    """!!! abstract "Usage Documentation"
        [Fields](../concepts/fields.md)

    Create a field for objects that can be configured.

    Used to provide extra information about a field, either for the model schema or complex validation. Some arguments
    apply only to number fields (`int`, `float`, `Decimal`) and some apply only to `str`.

    Note:
        - Any `_Unset` objects will be replaced by the corresponding value defined in the `_DefaultValues` dictionary. If a key for the `_Unset` object is not found in the `_DefaultValues` dictionary, it will default to `None`

    Args:
        default: Default value if the field is not set.
        default_factory: A callable to generate the default value. The callable can either take 0 arguments
            (in which case it is called as is) or a single argument containing the already validated data.
        alias: The name to use for the attribute when validating or serializing by alias.
            This is often used for things like converting between snake and camel case.
        alias_priority: Priority of the alias. This affects whether an alias generator is used.
        validation_alias: Like `alias`, but only affects validation, not serialization.
        serialization_alias: Like `alias`, but only affects serialization, not validation.
        title: Human-readable title.
        field_title_generator: A callable that takes a field name and returns title for it.
        description: Human-readable description.
        examples: Example values for this field.
        exclude: Whether to exclude the field from the model serialization.
        exclude_if: A callable that determines whether to exclude a field during serialization based on its value.
        discriminator: Field name or Discriminator for discriminating the type in a tagged union.
        deprecated: A deprecation message, an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport,
            or a boolean. If `True`, a default deprecation message will be emitted when accessing the field.
        json_schema_extra: A dict or callable to provide extra JSON schema properties.
        frozen: Whether the field is frozen. If true, attempts to change the value on an instance will raise an error.
        validate_default: If `True`, apply validation to the default value every time you create an instance.
            Otherwise, for performance reasons, the default value of the field is trusted and not validated.
        repr: A boolean indicating whether to include the field in the `__repr__` output.
        init: Whether the field should be included in the constructor of the dataclass.
            (Only applies to dataclasses.)
        init_var: Whether the field should _only_ be included in the constructor of the dataclass.
            (Only applies to dataclasses.)
        kw_only: Whether the field should be a keyword-only argument in the constructor of the dataclass.
            (Only applies to dataclasses.)
        coerce_numbers_to_str: Whether to enable coercion of any `Number` type to `str` (not applicable in `strict` mode).
        strict: If `True`, strict validation is applied to the field.
            See [Strict Mode](../concepts/strict_mode.md) for details.
        gt: Greater than. If set, value must be greater than this. Only applicable to numbers.
        ge: Greater than or equal. If set, value must be greater than or equal to this. Only applicable to numbers.
        lt: Less than. If set, value must be less than this. Only applicable to numbers.
        le: Less than or equal. If set, value must be less than or equal to this. Only applicable to numbers.
        multiple_of: Value must be a multiple of this. Only applicable to numbers.
        min_length: Minimum length for iterables.
        max_length: Maximum length for iterables.
        pattern: Pattern for strings (a regular expression).
        allow_inf_nan: Allow `inf`, `-inf`, `nan`. Only applicable to float and [`Decimal`][decimal.Decimal] numbers.
        max_digits: Maximum number of allow digits for strings.
        decimal_places: Maximum number of decimal places allowed for numbers.
        union_mode: The strategy to apply when validating a union. Can be `smart` (the default), or `left_to_right`.
            See [Union Mode](../concepts/unions.md#union-modes) for details.
        fail_fast: If `True`, validation will stop on the first error. If `False`, all validation errors will be collected.
            This option can be applied only to iterable types (list, tuple, set, and frozenset).
        extra: (Deprecated) Extra fields that will be included in the JSON schema.

            !!! warning Deprecated
                The `extra` kwargs is deprecated. Use `json_schema_extra` instead.

    Returns:
        A new [`FieldInfo`][pydantic.fields.FieldInfo]. The return annotation is `Any` so `Field` can be used on
            type-annotated fields without causing a type error.
    """
    # Check deprecated and removed params from V1. This logic should eventually be removed.
    const = extra.pop('const', None)  # type: ignore
    if const is not None:
        raise PydanticUserError('`const` is removed, use `Literal` instead', code='removed-kwargs')

    min_items = extra.pop('min_items', None)  # type: ignore
    if min_items is not None:
        warn(
            '`min_items` is deprecated and will be removed, use `min_length` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if min_length in (None, _Unset):
            min_length = min_items  # type: ignore

    max_items = extra.pop('max_items', None)  # type: ignore
    if max_items is not None:
        warn(
            '`max_items` is deprecated and will be removed, use `max_length` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if max_length in (None, _Unset):
            max_length = max_items  # type: ignore

    unique_items = extra.pop('unique_items', None)  # type: ignore
    if unique_items is not None:
        raise PydanticUserError(
            (
                '`unique_items` is removed, use `Set` instead'
                '(this feature is discussed in https://github.com/pydantic/pydantic-core/issues/296)'
            ),
            code='removed-kwargs',
        )

    allow_mutation = extra.pop('allow_mutation', None)  # type: ignore
    if allow_mutation is not None:
        warn(
            '`allow_mutation` is deprecated and will be removed. use `frozen` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if allow_mutation is False:
            frozen = True

    regex = extra.pop('regex', None)  # type: ignore
    if regex is not None:
        raise PydanticUserError('`regex` is removed. use `pattern` instead', code='removed-kwargs')

    if extra:
        warn(
            'Using extra keyword arguments on `Field` is deprecated and will be removed.'
            ' Use `json_schema_extra` instead.'
            f' (Extra keys: {", ".join(k.__repr__() for k in extra.keys())})',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )
        if not json_schema_extra or json_schema_extra is _Unset:
            json_schema_extra = extra  # type: ignore

    if (
        validation_alias
        and validation_alias is not _Unset
        and not isinstance(validation_alias, (str, AliasChoices, AliasPath))
    ):
        raise TypeError('Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`')

    if serialization_alias in (_Unset, None) and isinstance(alias, str):
        serialization_alias = alias

    if validation_alias in (_Unset, None):
        validation_alias = alias

    include = extra.pop('include', None)  # type: ignore
    if include is not None:
        warn(
            '`include` is deprecated and does nothing. It will be removed, use `exclude` instead',
            PydanticDeprecatedSince20,
            stacklevel=2,
        )

    return FieldInfo.from_field(
        default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        field_title_generator=field_title_generator,
        description=description,
        examples=examples,
        exclude=exclude,
        exclude_if=exclude_if,
        discriminator=discriminator,
        deprecated=deprecated,
        json_schema_extra=json_schema_extra,
        frozen=frozen,
        pattern=pattern,
        validate_default=validate_default,
        repr=repr,
        init=init,
        init_var=init_var,
        kw_only=kw_only,
        coerce_numbers_to_str=coerce_numbers_to_str,
        strict=strict,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        min_length=min_length,
        max_length=max_length,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        union_mode=union_mode,
        fail_fast=fail_fast,
    )

```

## FieldInfo

```python
FieldInfo(**kwargs: Unpack[_FieldInfoInputs])

```

Bases: `Representation`

This class holds information about a field.

`FieldInfo` is used for any field definition regardless of whether the Field() function is explicitly used.

Warning

The `FieldInfo` class is meant to expose information about a field in a Pydantic model or dataclass. `FieldInfo` instances shouldn't be instantiated directly, nor mutated.

If you need to derive a new model from another one and are willing to alter `FieldInfo` instances, refer to this [dynamic model example](../../examples/dynamic_models/).

Attributes:

| Name | Type | Description | | --- | --- | --- | | `annotation` | `type[Any] | None` | The type annotation of the field. | | `default` | `Any` | The default value of the field. | | `default_factory` | `Callable[[], Any] | Callable[[dict[str, Any]], Any] | None` | A callable to generate the default value. The callable can either take 0 arguments (in which case it is called as is) or a single argument containing the already validated data. | | `alias` | `str | None` | The alias name of the field. | | `alias_priority` | `int | None` | The priority of the field's alias. | | `validation_alias` | `str | AliasPath | AliasChoices | None` | The validation alias of the field. | | `serialization_alias` | `str | None` | The serialization alias of the field. | | `title` | `str | None` | The title of the field. | | `field_title_generator` | `Callable[[str, FieldInfo], str] | None` | A callable that takes a field name and returns title for it. | | `description` | `str | None` | The description of the field. | | `examples` | `list[Any] | None` | List of examples of the field. | | `exclude` | `bool | None` | Whether to exclude the field from the model serialization. | | `exclude_if` | `Callable[[Any], bool] | None` | A callable that determines whether to exclude a field during serialization based on its value. | | `discriminator` | `str | Discriminator | None` | Field name or Discriminator for discriminating the type in a tagged union. | | `deprecated` | `Deprecated | str | bool | None` | A deprecation message, an instance of warnings.deprecated or the typing_extensions.deprecated backport, or a boolean. If True, a default deprecation message will be emitted when accessing the field. | | `json_schema_extra` | `JsonDict | Callable[[JsonDict], None] | None` | A dict or callable to provide extra JSON schema properties. | | `frozen` | `bool | None` | Whether the field is frozen. | | `validate_default` | `bool | None` | Whether to validate the default value of the field. | | `repr` | `bool` | Whether to include the field in representation of the model. | | `init` | `bool | None` | Whether the field should be included in the constructor of the dataclass. | | `init_var` | `bool | None` | Whether the field should only be included in the constructor of the dataclass, and not stored. | | `kw_only` | `bool | None` | Whether the field should be a keyword-only argument in the constructor of the dataclass. | | `metadata` | `list[Any]` | The metadata list. Contains all the data that isn't expressed as direct FieldInfo attributes, including: Type-specific constraints, such as gt or min_length (these are converted to metadata classes such as annotated_types.Gt). Any other arbitrary object used within Annotated metadata (e.g. custom types handlers or any object not recognized by Pydantic). |

See the signature of `pydantic.fields.Field` for more details about the expected arguments.

Source code in `pydantic/fields.py`

```python
def __init__(self, **kwargs: Unpack[_FieldInfoInputs]) -> None:
    """This class should generally not be initialized directly; instead, use the `pydantic.fields.Field` function
    or one of the constructor classmethods.

    See the signature of `pydantic.fields.Field` for more details about the expected arguments.
    """
    # Tracking the explicitly set attributes is necessary to correctly merge `Field()` functions
    # (e.g. with `Annotated[int, Field(alias='a'), Field(alias=None)]`, even though `None` is the default value,
    # we need to track that `alias=None` was explicitly set):
    self._attributes_set = {k: v for k, v in kwargs.items() if v is not _Unset and k not in self.metadata_lookup}
    kwargs = {k: _DefaultValues.get(k) if v is _Unset else v for k, v in kwargs.items()}  # type: ignore
    self.annotation = kwargs.get('annotation')

    # Note: in theory, the second `pop()` arguments are not required below, as defaults are already set from `_DefaultsValues`.
    default = kwargs.pop('default', PydanticUndefined)
    if default is Ellipsis:
        self.default = PydanticUndefined
        self._attributes_set.pop('default', None)
    else:
        self.default = default

    self.default_factory = kwargs.pop('default_factory', None)

    if self.default is not PydanticUndefined and self.default_factory is not None:
        raise TypeError('cannot specify both default and default_factory')

    self.alias = kwargs.pop('alias', None)
    self.validation_alias = kwargs.pop('validation_alias', None)
    self.serialization_alias = kwargs.pop('serialization_alias', None)
    alias_is_set = any(alias is not None for alias in (self.alias, self.validation_alias, self.serialization_alias))
    self.alias_priority = kwargs.pop('alias_priority', None) or 2 if alias_is_set else None
    self.title = kwargs.pop('title', None)
    self.field_title_generator = kwargs.pop('field_title_generator', None)
    self.description = kwargs.pop('description', None)
    self.examples = kwargs.pop('examples', None)
    self.exclude = kwargs.pop('exclude', None)
    self.exclude_if = kwargs.pop('exclude_if', None)
    self.discriminator = kwargs.pop('discriminator', None)
    # For compatibility with FastAPI<=0.110.0, we preserve the existing value if it is not overridden
    self.deprecated = kwargs.pop('deprecated', getattr(self, 'deprecated', None))
    self.repr = kwargs.pop('repr', True)
    self.json_schema_extra = kwargs.pop('json_schema_extra', None)
    self.validate_default = kwargs.pop('validate_default', None)
    self.frozen = kwargs.pop('frozen', None)
    # currently only used on dataclasses
    self.init = kwargs.pop('init', None)
    self.init_var = kwargs.pop('init_var', None)
    self.kw_only = kwargs.pop('kw_only', None)

    self.metadata = self._collect_metadata(kwargs)  # type: ignore

    # Private attributes:
    self._qualifiers: set[Qualifier] = set()
    # Used to rebuild FieldInfo instances:
    self._complete = True
    self._original_annotation: Any = PydanticUndefined
    self._original_assignment: Any = PydanticUndefined
    # Used to track whether the `FieldInfo` instance represents the data about a field (and is exposed in `model_fields`/`__pydantic_fields__`),
    # or if it is the result of the `Field()` function being used as metadata in an `Annotated` type/as an assignment
    # (not an ideal pattern, see https://github.com/pydantic/pydantic/issues/11122):
    self._final = False

```

### deprecation_message

```python
deprecation_message: str | None

```

The deprecation message to be emitted, or `None` if not set.

### default_factory_takes_validated_data

```python
default_factory_takes_validated_data: bool | None

```

Whether the provided default factory callable has a validated data parameter.

Returns `None` if no default factory is set.

### get_default

```python
get_default(
    *,
    call_default_factory: Literal[True],
    validated_data: dict[str, Any] | None = None
) -> Any

```

```python
get_default(
    *, call_default_factory: Literal[False] = ...
) -> Any

```

```python
get_default(
    *,
    call_default_factory: bool = False,
    validated_data: dict[str, Any] | None = None
) -> Any

```

Get the default value.

We expose an option for whether to call the default_factory (if present), as calling it may result in side effects that we want to avoid. However, there are times when it really should be called (namely, when instantiating a model via `model_construct`).

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `call_default_factory` | `bool` | Whether to call the default factory or not. | `False` | | `validated_data` | `dict[str, Any] | None` | The already validated data to be passed to the default factory. | `None` |

Returns:

| Type | Description | | --- | --- | | `Any` | The default value, calling the default factory if requested or None if not set. |

Source code in `pydantic/fields.py`

```python
def get_default(self, *, call_default_factory: bool = False, validated_data: dict[str, Any] | None = None) -> Any:
    """Get the default value.

    We expose an option for whether to call the default_factory (if present), as calling it may
    result in side effects that we want to avoid. However, there are times when it really should
    be called (namely, when instantiating a model via `model_construct`).

    Args:
        call_default_factory: Whether to call the default factory or not.
        validated_data: The already validated data to be passed to the default factory.

    Returns:
        The default value, calling the default factory if requested or `None` if not set.
    """
    if self.default_factory is None:
        return _utils.smart_deepcopy(self.default)
    elif call_default_factory:
        if self.default_factory_takes_validated_data:
            fac = cast('Callable[[dict[str, Any]], Any]', self.default_factory)
            if validated_data is None:
                raise ValueError(
                    "The default factory requires the 'validated_data' argument, which was not provided when calling 'get_default'."
                )
            return fac(validated_data)
        else:
            fac = cast('Callable[[], Any]', self.default_factory)
            return fac()
    else:
        return None

```

### is_required

```python
is_required() -> bool

```

Check if the field is required (i.e., does not have a default value or factory).

Returns:

| Type | Description | | --- | --- | | `bool` | True if the field is required, False otherwise. |

Source code in `pydantic/fields.py`

```python
def is_required(self) -> bool:
    """Check if the field is required (i.e., does not have a default value or factory).

    Returns:
        `True` if the field is required, `False` otherwise.
    """
    return self.default is PydanticUndefined and self.default_factory is None

```

### asdict

```python
asdict() -> _FieldInfoAsDict

```

Return a dictionary representation of the `FieldInfo` instance.

The returned value is a dictionary with three items:

- `annotation`: The type annotation of the field.
- `metadata`: The metadata list.
- `attributes`: A mapping of the remaining `FieldInfo` attributes to their values (e.g. `alias`, `title`).

Source code in `pydantic/fields.py`

```python
def asdict(self) -> _FieldInfoAsDict:
    """Return a dictionary representation of the `FieldInfo` instance.

    The returned value is a dictionary with three items:

    * `annotation`: The type annotation of the field.
    * `metadata`: The metadata list.
    * `attributes`: A mapping of the remaining `FieldInfo` attributes to their values (e.g. `alias`, `title`).
    """
    return {
        'annotation': self.annotation,
        'metadata': self.metadata,
        'attributes': {attr: getattr(self, attr) for attr in _Attrs},
    }

```

## PrivateAttr

```python
PrivateAttr(
    default: _T" optional hover>_T, *, init: Literal[False] = False
) -> _T

```

```python
PrivateAttr(
    *,
    default_factory: Callable[[], _T],
    init: Literal[False] = False
) -> _T

```

```python
PrivateAttr(*, init: Literal[False] = False) -> Any

```

```python
PrivateAttr(
    default: Any = PydanticUndefined,
    *,
    default_factory: Callable[[], Any] | None = None,
    init: Literal[False] = False
) -> Any

```

Usage Documentation

[Private Model Attributes](../../concepts/models/#private-model-attributes)

Indicates that an attribute is intended for private use and not handled during normal validation/serialization.

Private attributes are not validated by Pydantic, so it's up to you to ensure they are used in a type-safe manner.

Private attributes are stored in `__private_attributes__` on the model.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `default` | `Any` | The attribute's default value. Defaults to Undefined. | `PydanticUndefined` | | `default_factory` | `Callable[[], Any] | None` | Callable that will be called when a default value is needed for this attribute. If both default and default_factory are set, an error will be raised. | `None` | | `init` | `Literal[False]` | Whether the attribute should be included in the constructor of the dataclass. Always False. | `False` |

Returns:

| Type | Description | | --- | --- | | `Any` | An instance of ModelPrivateAttr class. |

Raises:

| Type | Description | | --- | --- | | `ValueError` | If both default and default_factory are set. |

Source code in `pydantic/fields.py`

```python
def PrivateAttr(
    default: Any = PydanticUndefined,
    *,
    default_factory: Callable[[], Any] | None = None,
    init: Literal[False] = False,
) -> Any:
    """!!! abstract "Usage Documentation"
        [Private Model Attributes](../concepts/models.md#private-model-attributes)

    Indicates that an attribute is intended for private use and not handled during normal validation/serialization.

    Private attributes are not validated by Pydantic, so it's up to you to ensure they are used in a type-safe manner.

    Private attributes are stored in `__private_attributes__` on the model.

    Args:
        default: The attribute's default value. Defaults to Undefined.
        default_factory: Callable that will be
            called when a default value is needed for this attribute.
            If both `default` and `default_factory` are set, an error will be raised.
        init: Whether the attribute should be included in the constructor of the dataclass. Always `False`.

    Returns:
        An instance of [`ModelPrivateAttr`][pydantic.fields.ModelPrivateAttr] class.

    Raises:
        ValueError: If both `default` and `default_factory` are set.
    """
    if default is not PydanticUndefined and default_factory is not None:
        raise TypeError('cannot specify both default and default_factory')

    return ModelPrivateAttr(
        default,
        default_factory=default_factory,
    )

```

## ModelPrivateAttr

```python
ModelPrivateAttr(
    default: Any = PydanticUndefined,
    *,
    default_factory: Callable[[], Any] | None = None
)

```

Bases: `Representation`

A descriptor for private attributes in class models.

Warning

You generally shouldn't be creating `ModelPrivateAttr` instances directly, instead use `pydantic.fields.PrivateAttr`. (This is similar to `FieldInfo` vs. `Field`.)

Attributes:

| Name | Type | Description | | --- | --- | --- | | `default` | | The default value of the attribute if not provided. | | `default_factory` | | A callable function that generates the default value of the attribute if not provided. |

Source code in `pydantic/fields.py`

```python
def __init__(self, default: Any = PydanticUndefined, *, default_factory: Callable[[], Any] | None = None) -> None:
    if default is Ellipsis:
        self.default = PydanticUndefined
    else:
        self.default = default
    self.default_factory = default_factory

```

### __getattr__

```python
__getattr__(item: str) -> Any

```

This function improves compatibility with custom descriptors by ensuring delegation happens as expected when the default value of a private attribute is a descriptor.

Source code in `pydantic/fields.py`

```python
def __getattr__(self, item: str) -> Any:
    """This function improves compatibility with custom descriptors by ensuring delegation happens
    as expected when the default value of a private attribute is a descriptor.
    """
    if item in {'__get__', '__set__', '__delete__'}:
        if hasattr(self.default, item):
            return getattr(self.default, item)
    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')

```

### __set_name__

```python
__set_name__(cls: type[Any], name: str) -> None

```

Preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487.

Source code in `pydantic/fields.py`

```python
def __set_name__(self, cls: type[Any], name: str) -> None:
    """Preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487."""
    default = self.default
    if default is PydanticUndefined:
        return
    set_name = getattr(default, '__set_name__', None)
    if callable(set_name):
        set_name(cls, name)

```

### get_default

```python
get_default() -> Any

```

Retrieve the default value of the object.

If `self.default_factory` is `None`, the method will return a deep copy of the `self.default` object.

If `self.default_factory` is not `None`, it will call `self.default_factory` and return the value returned.

Returns:

| Type | Description | | --- | --- | | `Any` | The default value of the object. |

Source code in `pydantic/fields.py`

```python
def get_default(self) -> Any:
    """Retrieve the default value of the object.

    If `self.default_factory` is `None`, the method will return a deep copy of the `self.default` object.

    If `self.default_factory` is not `None`, it will call `self.default_factory` and return the value returned.

    Returns:
        The default value of the object.
    """
    return _utils.smart_deepcopy(self.default) if self.default_factory is None else self.default_factory()

```

## computed_field

```python
computed_field(func: PropertyT) -> PropertyT

```

```python
computed_field(
    *,
    alias: str | None = None,
    alias_priority: int | None = None,
    title: str | None = None,
    field_title_generator: (
        Callable[[str, ComputedFieldInfo], str] | None
    ) = None,
    description: str | None = None,
    deprecated: Deprecated | str | bool | None = None,
    examples: list[Any] | None = None,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = None,
    repr: bool = True,
    return_type: Any = PydanticUndefined
) -> Callable[[PropertyT], PropertyT]

```

```python
computed_field(
    func: PropertyT | None = None,
    /,
    *,
    alias: str | None = None,
    alias_priority: int | None = None,
    title: str | None = None,
    field_title_generator: (
        Callable[[str, ComputedFieldInfo], str] | None
    ) = None,
    description: str | None = None,
    deprecated: Deprecated | str | bool | None = None,
    examples: list[Any] | None = None,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ) = None,
    repr: bool | None = None,
    return_type: Any = PydanticUndefined,
) -> PropertyT | Callable[[PropertyT], PropertyT]

```

Usage Documentation

[The `computed_field` decorator](../../concepts/fields/#the-computed_field-decorator)

Decorator to include `property` and `cached_property` when serializing models or dataclasses.

This is useful for fields that are computed from other fields, or for fields that are expensive to compute and should be cached.

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: int
    length: int

    @computed_field
    @property
    def area(self) -> int:
        return self.width * self.length

print(Rectangle(width=3, length=2).model_dump())
#> {'width': 3, 'length': 2, 'area': 6}

```

If applied to functions not yet decorated with `@property` or `@cached_property`, the function is automatically wrapped with `property`. Although this is more concise, you will lose IntelliSense in your IDE, and confuse static type checkers, thus explicit use of `@property` is recommended.

Mypy Warning

Even with the `@property` or `@cached_property` applied to your function before `@computed_field`, mypy may throw a `Decorated property not supported` error. See [mypy issue #1362](https://github.com/python/mypy/issues/1362), for more information. To avoid this error message, add `# type: ignore[prop-decorator]` to the `@computed_field` line.

[pyright](https://github.com/microsoft/pyright) supports `@computed_field` without error.

```python
import random

from pydantic import BaseModel, computed_field

class Square(BaseModel):
    width: float

    @computed_field
    def area(self) -> float:  # converted to a `property` by `computed_field`
        return round(self.width**2, 2)

    @area.setter
    def area(self, new_area: float) -> None:
        self.width = new_area**0.5

    @computed_field(alias='the magic number', repr=False)
    def random_number(self) -> int:
        return random.randint(0, 1_000)

square = Square(width=1.3)

# `random_number` does not appear in representation
print(repr(square))
#> Square(width=1.3, area=1.69)

print(square.random_number)
#> 3

square.area = 4

print(square.model_dump_json(by_alias=True))
#> {"width":2.0,"area":4.0,"the magic number":3}

```

Overriding with `computed_field`

You can't override a field from a parent class with a `computed_field` in the child class. `mypy` complains about this behavior if allowed, and `dataclasses` doesn't allow this pattern either. See the example below:

```python
from pydantic import BaseModel, computed_field

class Parent(BaseModel):
    a: str

try:

    class Child(Parent):
        @computed_field
        @property
        def a(self) -> str:
            return 'new a'

except TypeError as e:
    print(e)
    '''
    Field 'a' of class 'Child' overrides symbol of same name in a parent class. This override with a computed_field is incompatible.
    '''

```

Private properties decorated with `@computed_field` have `repr=False` by default.

```python
from functools import cached_property

from pydantic import BaseModel, computed_field

class Model(BaseModel):
    foo: int

    @computed_field
    @cached_property
    def _private_cached_property(self) -> int:
        return -self.foo

    @computed_field
    @property
    def _private_property(self) -> int:
        return -self.foo

m = Model(foo=1)
print(repr(m))
#> Model(foo=1)

```

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `func` | `PropertyT | None` | the function to wrap. | `None` | | `alias` | `str | None` | alias to use when serializing this computed field, only used when by_alias=True | `None` | | `alias_priority` | `int | None` | priority of the alias. This affects whether an alias generator is used | `None` | | `title` | `str | None` | Title to use when including this computed field in JSON Schema | `None` | | `field_title_generator` | `Callable[[str, ComputedFieldInfo], str] | None` | A callable that takes a field name and returns title for it. | `None` | | `description` | `str | None` | Description to use when including this computed field in JSON Schema, defaults to the function's docstring | `None` | | `deprecated` | `Deprecated | str | bool | None` | A deprecation message (or an instance of warnings.deprecated or the typing_extensions.deprecated backport). to be emitted when accessing the field. Or a boolean. This will automatically be set if the property is decorated with the deprecated decorator. | `None` | | `examples` | `list[Any] | None` | Example values to use when including this computed field in JSON Schema | `None` | | `json_schema_extra` | `JsonDict | Callable[[JsonDict], None] | None` | A dict or callable to provide extra JSON schema properties. | `None` | | `repr` | `bool | None` | whether to include this computed field in model repr. Default is False for private properties and True for public properties. | `None` | | `return_type` | `Any` | optional return for serialization logic to expect when serializing to JSON, if included this must be correct, otherwise a TypeError is raised. If you don't include a return type Any is used, which does runtime introspection to handle arbitrary objects. | `PydanticUndefined` |

Returns:

| Type | Description | | --- | --- | | `PropertyT | Callable[[PropertyT], PropertyT]` | A proxy wrapper for the property. |

Source code in `pydantic/fields.py`

````python
def computed_field(
    func: PropertyT | None = None,
    /,
    *,
    alias: str | None = None,
    alias_priority: int | None = None,
    title: str | None = None,
    field_title_generator: Callable[[str, ComputedFieldInfo], str] | None = None,
    description: str | None = None,
    deprecated: Deprecated | str | bool | None = None,
    examples: list[Any] | None = None,
    json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = None,
    repr: bool | None = None,
    return_type: Any = PydanticUndefined,
) -> PropertyT | Callable[[PropertyT], PropertyT]:
    """!!! abstract "Usage Documentation"
        [The `computed_field` decorator](../concepts/fields.md#the-computed_field-decorator)

    Decorator to include `property` and `cached_property` when serializing models or dataclasses.

    This is useful for fields that are computed from other fields, or for fields that are expensive to compute and should be cached.

    ```python
    from pydantic import BaseModel, computed_field

    class Rectangle(BaseModel):
        width: int
        length: int

        @computed_field
        @property
        def area(self) -> int:
            return self.width * self.length

    print(Rectangle(width=3, length=2).model_dump())
    #> {'width': 3, 'length': 2, 'area': 6}
    ```

    If applied to functions not yet decorated with `@property` or `@cached_property`, the function is
    automatically wrapped with `property`. Although this is more concise, you will lose IntelliSense in your IDE,
    and confuse static type checkers, thus explicit use of `@property` is recommended.

    !!! warning "Mypy Warning"
        Even with the `@property` or `@cached_property` applied to your function before `@computed_field`,
        mypy may throw a `Decorated property not supported` error.
        See [mypy issue #1362](https://github.com/python/mypy/issues/1362), for more information.
        To avoid this error message, add `# type: ignore[prop-decorator]` to the `@computed_field` line.

        [pyright](https://github.com/microsoft/pyright) supports `@computed_field` without error.

    ```python
    import random

    from pydantic import BaseModel, computed_field

    class Square(BaseModel):
        width: float

        @computed_field
        def area(self) -> float:  # converted to a `property` by `computed_field`
            return round(self.width**2, 2)

        @area.setter
        def area(self, new_area: float) -> None:
            self.width = new_area**0.5

        @computed_field(alias='the magic number', repr=False)
        def random_number(self) -> int:
            return random.randint(0, 1_000)

    square = Square(width=1.3)

    # `random_number` does not appear in representation
    print(repr(square))
    #> Square(width=1.3, area=1.69)

    print(square.random_number)
    #> 3

    square.area = 4

    print(square.model_dump_json(by_alias=True))
    #> {"width":2.0,"area":4.0,"the magic number":3}
    ```

    !!! warning "Overriding with `computed_field`"
        You can't override a field from a parent class with a `computed_field` in the child class.
        `mypy` complains about this behavior if allowed, and `dataclasses` doesn't allow this pattern either.
        See the example below:

    ```python
    from pydantic import BaseModel, computed_field

    class Parent(BaseModel):
        a: str

    try:

        class Child(Parent):
            @computed_field
            @property
            def a(self) -> str:
                return 'new a'

    except TypeError as e:
        print(e)
        '''
        Field 'a' of class 'Child' overrides symbol of same name in a parent class. This override with a computed_field is incompatible.
        '''
    ```

    Private properties decorated with `@computed_field` have `repr=False` by default.

    ```python
    from functools import cached_property

    from pydantic import BaseModel, computed_field

    class Model(BaseModel):
        foo: int

        @computed_field
        @cached_property
        def _private_cached_property(self) -> int:
            return -self.foo

        @computed_field
        @property
        def _private_property(self) -> int:
            return -self.foo

    m = Model(foo=1)
    print(repr(m))
    #> Model(foo=1)
    ```

    Args:
        func: the function to wrap.
        alias: alias to use when serializing this computed field, only used when `by_alias=True`
        alias_priority: priority of the alias. This affects whether an alias generator is used
        title: Title to use when including this computed field in JSON Schema
        field_title_generator: A callable that takes a field name and returns title for it.
        description: Description to use when including this computed field in JSON Schema, defaults to the function's
            docstring
        deprecated: A deprecation message (or an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport).
            to be emitted when accessing the field. Or a boolean. This will automatically be set if the property is decorated with the
            `deprecated` decorator.
        examples: Example values to use when including this computed field in JSON Schema
        json_schema_extra: A dict or callable to provide extra JSON schema properties.
        repr: whether to include this computed field in model repr.
            Default is `False` for private properties and `True` for public properties.
        return_type: optional return for serialization logic to expect when serializing to JSON, if included
            this must be correct, otherwise a `TypeError` is raised.
            If you don't include a return type Any is used, which does runtime introspection to handle arbitrary
            objects.

    Returns:
        A proxy wrapper for the property.
    """

    def dec(f: Any) -> Any:
        nonlocal description, deprecated, return_type, alias_priority
        unwrapped = _decorators.unwrap_wrapped_function(f)

        if description is None and unwrapped.__doc__:
            description = inspect.cleandoc(unwrapped.__doc__)

        if deprecated is None and hasattr(unwrapped, '__deprecated__'):
            deprecated = unwrapped.__deprecated__

        # if the function isn't already decorated with `@property` (or another descriptor), then we wrap it now
        f = _decorators.ensure_property(f)
        alias_priority = (alias_priority or 2) if alias is not None else None

        if repr is None:
            repr_: bool = not _wrapped_property_is_private(property_=f)
        else:
            repr_ = repr

        dec_info = ComputedFieldInfo(
            f,
            return_type,
            alias,
            alias_priority,
            title,
            field_title_generator,
            description,
            deprecated,
            examples,
            json_schema_extra,
            repr_,
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if func is None:
        return dec
    else:
        return dec(func)

````

## ComputedFieldInfo

```python
ComputedFieldInfo(
    wrapped_property: property,
    return_type: Any,
    alias: str | None,
    alias_priority: int | None,
    title: str | None,
    field_title_generator: (
        Callable[[str, ComputedFieldInfo], str] | None
    ),
    description: str | None,
    deprecated: Deprecated | str | bool | None,
    examples: list[Any] | None,
    json_schema_extra: (
        JsonDict | Callable[[JsonDict], None] | None
    ),
    repr: bool,
)

```

A container for data from `@computed_field` so that we can access it while building the pydantic-core schema.

Attributes:

| Name | Type | Description | | --- | --- | --- | | `decorator_repr` | `str` | A class variable representing the decorator string, '@computed_field'. | | `wrapped_property` | `property` | The wrapped computed field property. | | `return_type` | `Any` | The type of the computed field property's return value. | | `alias` | `str | None` | The alias of the property to be used during serialization. | | `alias_priority` | `int | None` | The priority of the alias. This affects whether an alias generator is used. | | `title` | `str | None` | Title of the computed field to include in the serialization JSON schema. | | `field_title_generator` | `Callable[[str, ComputedFieldInfo], str] | None` | A callable that takes a field name and returns title for it. | | `description` | `str | None` | Description of the computed field to include in the serialization JSON schema. | | `deprecated` | `Deprecated | str | bool | None` | A deprecation message, an instance of warnings.deprecated or the typing_extensions.deprecated backport, or a boolean. If True, a default deprecation message will be emitted when accessing the field. | | `examples` | `list[Any] | None` | Example values of the computed field to include in the serialization JSON schema. | | `json_schema_extra` | `JsonDict | Callable[[JsonDict], None] | None` | A dict or callable to provide extra JSON schema properties. | | `repr` | `bool` | A boolean indicating whether to include the field in the repr output. |

### deprecation_message

```python
deprecation_message: str | None

```

The deprecation message to be emitted, or `None` if not set.
