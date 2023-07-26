"""Configuration for Pydantic models."""
from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Type, Union

from typing_extensions import Literal, TypeAlias, TypedDict

from ._migration import getattr_migration
from .deprecated.config import BaseConfig
from .deprecated.config import Extra as _Extra

if TYPE_CHECKING:
    from ._internal._generate_schema import GenerateSchema as _GenerateSchema

__all__ = 'BaseConfig', 'ConfigDict', 'Extra'


JsonEncoder = Callable[[Any], Any]

JsonSchemaExtraCallable: TypeAlias = Union[
    Callable[[Dict[str, Any]], None],
    Callable[[Dict[str, Any], Type[Any]], None],
]

Extra = _Extra()

ExtraValues = Literal['allow', 'ignore', 'forbid']


class ConfigDict(TypedDict, total=False):
    """Usage docs: https://docs.pydantic.dev/2.0/usage/model_config/

    A TypedDict for configuring Pydantic behaviour.
    """

    title: str | None
    """The title for the generated JSON schema, defaults to the model's name"""

    str_to_lower: bool
    """Whether to convert all characters to lowercase for str types. Defaults to `False`."""

    str_to_upper: bool
    """Whether to convert all characters to uppercase for str types. Defaults to `False`."""
    str_strip_whitespace: bool
    """Whether to strip leading and trailing whitespace for str types."""

    str_min_length: int
    """The minimum length for str types. Defaults to `None`."""

    str_max_length: int | None
    """The maximum length for str types. Defaults to `None`."""

    extra: ExtraValues | None
    """
    Whether to ignore, allow, or forbid extra attributes during model initialization.

    The value must be a [`ExtraValues`][pydantic.config.ExtraValues] string. Defaults to `'ignore'`.

    See [Extra Attributes](../usage/model_config.md#extra-attributes) for details.
    """

    frozen: bool
    """
    Whether or not models are faux-immutable, i.e. whether `__setattr__` is allowed, and also generates
    a `__hash__()` method for the model. This makes instances of the model potentially hashable if all the
    attributes are hashable. Defaults to `False`.

    !!! note
        On V1, this setting was called `allow_mutation`, and was `True` by default.
    """

    populate_by_name: bool
    """
    Whether an aliased field may be populated by its name as given by the model
    attribute, as well as the alias. Defaults to `False`.

    !!! note
        The name of this configuration setting was changed in **v2.0** from
        `allow_population_by_alias` to `populate_by_name`.
    """

    use_enum_values: bool
    """
    Whether to populate models with the `value` property of enums, rather than the raw enum.
    This may be useful if you want to serialize `model.model_dump()` later. Defaults to `False`.
    """

    validate_assignment: bool
    arbitrary_types_allowed: bool
    from_attributes: bool
    """
    Whether to build models and look up discriminators of tagged unions using python object attributes.
    """

    loc_by_alias: bool
    """Whether to use the alias for error `loc`s rather than the field's name. Defaults to `True`."""

    alias_generator: Callable[[str], str] | None
    """
    A callable that takes a field name and returns an alias for it.

    See [Alias Generator](../usage/model_config.md#alias-generator) for details.
    """

    ignored_types: tuple[type, ...]
    """A tuple of types that may occur as values of class attributes without annotations. This is
    typically used for custom descriptors (classes that behave like `property`). If an attribute is set on a
    class without an annotation and has a type that is not in this tuple (or otherwise recognized by
    _pydantic_), an error will be raised. Defaults to `()`.
    """

    allow_inf_nan: bool
    """Whether to allow infinity (`+inf` an `-inf`) and NaN values to float fields. Defaults to `True`."""

    json_schema_extra: dict[str, object] | JsonSchemaExtraCallable | None
    """A dict or callable to provide extra JSON schema properties. Defaults to `None`."""

    json_encoders: dict[type[object], JsonEncoder] | None
    """
    A `dict` of custom JSON encoders for specific types. Defaults to `None`.

    !!! warning "Deprecated"
        This config option is a carryover from v1.
        We originally planned to remove it in v2 but didn't have a 1:1 replacement so we are keeping it for now.
        It is still deprecated and will likely be removed in the future.
    """

    # new in V2
    strict: bool
    """
    _(new in V2)_ If `True`, strict validation is applied to all fields on the model.
    See [Strict Mode](../usage/strict_mode.md) for details.
    """
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    """

    When and how to revalidate models and dataclasses during validation. Accepts the string
    values of `'never'`, `'always'` and `'subclass-instances'`. Defaults to `'never'`.

    - `'never'` will not revalidate models and dataclasses during validation
    - `'always'` will revalidate models and dataclasses during validation
    - `'subclass-instances'` will revalidate models and dataclasses during validation if the instance is a
        subclass of the model or dataclass

    See [Revalidate Instances](../usage/model_config.md#revalidate-instances) for details.
    """

    ser_json_timedelta: Literal['iso8601', 'float']
    """
    The format of JSON serialized timedeltas. Accepts the string values of `'iso8601'` and
    `'float'`. Defaults to `'iso8601'`.

    - `'iso8601'` will serialize timedeltas to ISO 8601 durations.
    - `'float'` will serialize timedeltas to the total number of seconds.
    """

    ser_json_bytes: Literal['utf8', 'base64']
    """
    The encoding of JSON serialized bytes. Accepts the string values of `'utf8'` and `'base64'`.
    Defaults to `'utf8'`.

    - `'utf8'` will serialize bytes to UTF-8 strings.
    - `'base64'` will serialize bytes to base64 strings.
    """

    # whether to validate default values during validation, default False
    validate_default: bool
    """Whether to validate default values during validation. Defaults to `False`."""

    validate_return: bool
    """whether to validate the return value from call validators."""

    protected_namespaces: tuple[str, ...]
    """
    A `tuple` of strings that prevent model to have field which conflict with them.
    Defaults to `('model_', )`).

    See [Protected Namespaces](../usage/model_config.md#protected-namespaces) for details.
    """

    hide_input_in_errors: bool
    """
    Whether to hide inputs when printing errors. Defaults to `False`.

    See [Hide Input in Errors](../usage/model_config.md#hide-input-in-errors).
    """

    defer_build: bool
    """
    Whether to defer model validator and serializer construction until the first model validation.

    This can be useful to avoid the overhead of building models which are only
    used nested within other models, or when you want to manually define type namespace via
    [`Model.model_rebuild(_types_namespace=...)`][pydantic.BaseModel.model_rebuild]. Defaults to False.
    """

    schema_generator: type[_GenerateSchema] | None
    """
    A custom core schema generator class to use when generating JSON schemas.
    Useful if you want to change the way types are validated across an entire model/schema.

    The `GenerateSchema` interface is subject to change, currently only the `string_schema` method is public.

    See [#6737](https://github.com/pydantic/pydantic/pull/6737) for details.

    Defaults to `None`.
    """


__getattr__ = getattr_migration(__name__)
