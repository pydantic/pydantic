"""Configuration for Pydantic models."""
from __future__ import annotations as _annotations

from typing import Any, Callable, overload
from warnings import warn

from typing_extensions import Literal, Protocol, TypedDict

from ._migration import getattr_migration
from .deprecated.config import BaseConfig

__all__ = 'BaseConfig', 'ConfigDict', 'Extra'


class JsonSchemaExtraCallable(Protocol):
    @overload
    def __call__(self, schema: dict[str, Any]) -> None:
        pass

    @overload
    def __call__(self, schema: dict[str, Any], model_class: type[Any]) -> None:
        pass


class _Extra:
    allow: Literal['allow'] = 'allow'
    ignore: Literal['ignore'] = 'ignore'
    forbid: Literal['forbid'] = 'forbid'

    def __getattribute__(self, __name: str) -> Any:
        warn(
            '`pydantic.config.Extra` is deprecated, use literal values instead' " (e.g. `extra='allow'`)",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__getattribute__(__name)


Extra = _Extra()

ExtraValues = Literal['allow', 'ignore', 'forbid']


class ConfigDict(TypedDict, total=False):
    """A dictionary-like class for configuring Pydantic models.

    Attributes:
        title: Optional title for the configuration. Defaults to `None`.
        str_to_lower: Whether to convert strings to lowercase. Defaults to `False`.
        str_to_upper: Whether to convert strings to uppercase. Defaults to `False`.
        str_strip_whitespace: Whether to strip whitespace from strings. Defaults to `False`.
        str_min_length: The minimum length for strings. Defaults to `None`.
        str_max_length: The maximum length for strings. Defaults to `None`.
        extra: Extra values to include in this configuration. Defaults to `None`.
        frozen: Whether to freeze the configuration. Defaults to `False`.
        populate_by_name: Whether to populate fields by name. Defaults to `False`.
        use_enum_values: Whether to use enum values. Defaults to `False`.
        validate_assignment: Whether to validate assignments. Defaults to `False`.
        arbitrary_types_allowed: Whether to allow arbitrary types. Defaults to `False`.
        from_attributes: Whether to set attributes from the configuration. Defaults to `False`.
        loc_by_alias: Whether to use the alias for error `loc`s. Defaults to `True`.
        alias_generator: A function to generate aliases. Defaults to `None`.
        ignored_types: A tuple of types to ignore. Defaults to `()`.
        allow_inf_nan: Whether to allow infinity and NaN. Defaults to `False`.
        strict: Whether to make the configuration strict. Defaults to `False`.
        revalidate_instances: When and how to revalidate models and dataclasses during validation. Defaults to 'never'.
        ser_json_timedelta: The format of JSON serialized timedeltas. Defaults to 'iso8601'.
        ser_json_bytes: The encoding of JSON serialized bytes. Defaults to 'utf8'.
        validate_default: Whether to validate default values during validation. Defaults to `False`.
        protected_namespaces: A list of protected namespaces. Defaults to `('model_', )`.
        hide_input_in_errors: Whether to hide inputs when printing errors. Defaults to `False`.
    """

    title: str | None
    str_to_lower: bool
    str_to_upper: bool
    str_strip_whitespace: bool
    str_min_length: int
    str_max_length: int | None
    extra: ExtraValues | None
    frozen: bool
    populate_by_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool
    from_attributes: bool
    # whether to use the used alias (or first alias for "field required" errors) instead of field_names
    # to construct error `loc`s, default True
    loc_by_alias: bool
    alias_generator: Callable[[str], str] | None
    ignored_types: tuple[type, ...]
    allow_inf_nan: bool
    json_schema_extra: dict[str, object] | JsonSchemaExtraCallable | None

    # new in V2
    strict: bool
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    ser_json_timedelta: Literal['iso8601', 'float']
    ser_json_bytes: Literal['utf8', 'base64']
    # whether to validate default values during validation, default False
    validate_default: bool
    # whether to validate the return value from call validator
    validate_return: bool
    protected_namespaces: tuple[str, ...]
    hide_input_in_errors: bool


__getattr__ = getattr_migration(__name__)
