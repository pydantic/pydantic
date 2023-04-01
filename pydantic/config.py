from __future__ import annotations as _annotations

import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from typing_extensions import Literal, Protocol, TypedDict

from pydantic.errors import PydanticUserError

if TYPE_CHECKING:
    from typing import overload

    from .main import BaseModel

    class SchemaExtraCallable(Protocol):
        # TODO: This has been replaced with __pydantic_modify_json_schema__ in v2; need to make sure we
        #   document the migration, in particular changing `model_class` to `cls` from the classmethod
        # TODO: Note that the argument to Field(...) that served a similar purpose received the FieldInfo as well.
        #   Should we accept that argument here too? Will that add a ton of boilerplate?
        # Tentative suggestion to previous TODO: I think we let the json_schema_extra argument
        #   to FieldInfo be a callable that accepts schema, model_class, and field_info. And use
        #   similar machinery to `_apply_modify_schema` to call the function properly for different signatures.
        #   (And use this Protocol-based approach to get good type-checking.)
        @overload
        def __call__(self, schema: dict[str, Any]) -> None:
            pass

        @overload
        def __call__(self, schema: dict[str, Any], model_class: type[BaseModel]) -> None:
            pass

else:
    SchemaExtraCallable = Callable[..., None]

__all__ = 'BaseConfig', 'ConfigDict', 'Extra', 'build_config', 'prepare_config'


class Extra(str, Enum):
    allow = 'allow'
    ignore = 'ignore'
    forbid = 'forbid'


class _ConfigDict(TypedDict, total=False):
    title: str | None
    str_to_lower: bool
    str_to_upper: bool
    str_strip_whitespace: bool
    str_min_length: int
    str_max_length: int | None
    extra: Extra | None
    frozen: bool
    populate_by_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool  # TODO default True, or remove
    undefined_types_warning: bool  # TODO review docs
    from_attributes: bool
    # whether to use the used alias (or first alias for "field required" errors) instead of field_names
    # to construct error `loc`s, default True
    loc_by_alias: bool
    alias_generator: Callable[[str], str] | None
    ignored_types: tuple[type, ...]
    allow_inf_nan: bool

    # new in V2
    strict: bool
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    ser_json_timedelta: Literal['iso8601', 'float']
    ser_json_bytes: Literal['utf8', 'base64']
    # whether to validate default values during validation, default False
    validate_default: bool


config_keys = set(_ConfigDict.__annotations__.keys())

if TYPE_CHECKING:

    class ConfigDict(_ConfigDict):
        ...

else:

    class ConfigDict(dict):
        _V2_REMOVED_KEYS = {
            'allow_mutation',
            'error_msg_templates',
            'fields',
            'getter_dict',
            'schema_extra',
            'smart_union',
            'underscore_attrs_are_private',
            'json_loads',
            'json_dumps',
            'json_encoders',
            'copy_on_model_validation',
            'post_init_call',
        }
        _V2_RENAMED_KEYS = {
            'allow_population_by_field_name': 'populate_by_name',
            'anystr_lower': 'str_to_lower',
            'anystr_strip_whitespace': 'str_strip_whitespace',
            'anystr_upper': 'str_to_upper',
            'keep_untouched': 'ignored_types',
            'max_anystr_length': 'str_max_length',
            'min_anystr_length': 'str_min_length',
            'orm_mode': 'from_attributes',
            'validate_all': 'validate_default',
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            deprecated_removed_keys = ConfigDict._V2_REMOVED_KEYS & self.keys()
            deprecated_renamed_keys = ConfigDict._V2_RENAMED_KEYS.keys() & self.keys()
            if deprecated_removed_keys or deprecated_renamed_keys:
                renamings = {k: self._V2_RENAMED_KEYS[k] for k in sorted(deprecated_renamed_keys)}
                renamed_bullets = [f'* {k!r} has been renamed to {v!r}' for k, v in renamings.items()]
                removed_bullets = [f'* {k!r} has been removed' for k in sorted(deprecated_removed_keys)]
                message = '\n'.join(['Valid config keys have changed in V2:'] + renamed_bullets + removed_bullets)
                warnings.warn(message, UserWarning)

        def __missing__(self, key: str) -> Any:
            if key in _default_config:  # need this check to prevent a recursion error
                return _default_config[key]
            raise KeyError(key)


_default_config = ConfigDict(
    title=None,
    str_to_lower=False,
    str_to_upper=False,
    str_strip_whitespace=False,
    str_min_length=0,
    str_max_length=None,
    # let the model / dataclass decide how to handle it
    extra=None,
    frozen=False,
    revalidate_instances='never',
    populate_by_name=False,
    use_enum_values=False,
    validate_assignment=False,
    arbitrary_types_allowed=False,
    undefined_types_warning=True,
    from_attributes=False,
    loc_by_alias=True,
    alias_generator=None,
    ignored_types=(),
    allow_inf_nan=True,
    strict=False,
    ser_json_timedelta='iso8601',
    ser_json_bytes='utf8',
    validate_default=False,
)


class ConfigMetaclass(type):
    def __getattr__(self, item: str) -> Any:
        warnings.warn(
            f'Support for "config" as "{self.__name__}" is deprecated and will be removed in a future version"',
            DeprecationWarning,
        )

        try:
            return _default_config[item]  # type: ignore[literal-required]
        except KeyError as exc:
            raise AttributeError(f"type object '{self.__name__}' has no attribute {exc}") from exc


class BaseConfig(metaclass=ConfigMetaclass):
    """
    This class is only retained for backwards compatibility.

    The preferred approach going forward is to assign a ConfigDict to the `model_config` attribute of the Model class.
    """

    def __getattr__(self, item: str) -> Any:
        warnings.warn(
            f'Support for "config" as "{type(self).__name__}" is deprecated and will be removed in a future version',
            DeprecationWarning,
        )
        try:
            return super().__getattribute__(item)
        except AttributeError as exc:
            try:
                return getattr(type(self), item)
            except AttributeError:
                # reraising changes the displayed text to reflect that `self` is not a type
                raise AttributeError(str(exc)) from exc

    def __init_subclass__(cls, **kwargs: Any) -> None:
        warnings.warn(
            '`BaseConfig` is deprecated and will be removed in a future version',
            DeprecationWarning,
        )
        return super().__init_subclass__(**kwargs)


def get_config(config: ConfigDict | dict[str, Any] | type[Any] | None, error_label: str | None = None) -> ConfigDict:
    if config is None:
        return ConfigDict()

    if isinstance(config, dict):
        config_dict = config
    else:
        warnings.warn(
            f'Support for "config" as "{type(config).__name__}" is deprecated and will be removed in a future version',
            DeprecationWarning,
        )
        config_dict = {k: getattr(config, k) for k in dir(config) if not k.startswith('__')}

    prepare_config(config_dict, error_label or 'ConfigDict')
    return ConfigDict(config_dict)  # type: ignore


def build_config(
    cls_name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any], kwargs: dict[str, Any]
) -> ConfigDict:
    """
    Build a new ConfigDict instance based on (from lowest to highest)
    - options defined in base
    - options defined in namespace
    - options defined via kwargs
    """
    config_kwargs = {k: kwargs.pop(k) for k in list(kwargs.keys()) if k in config_keys}

    config_bases = {}
    configs_ordered = []
    # collect all config options from bases
    for base in bases:
        config = getattr(base, 'model_config', None)
        if config:
            configs_ordered.append(config)
            config_bases.update({key: value for key, value in config.items()})
    config_new = dict(config_bases.items())

    config_class_from_namespace = namespace.get('Config')
    config_dict_from_namespace = namespace.get('model_config')

    if config_class_from_namespace and config_dict_from_namespace:
        raise PydanticUserError('"Config" and "model_config" cannot be used together')

    config_from_namespace = config_dict_from_namespace or get_config(config_class_from_namespace)

    if config_from_namespace:
        configs_ordered.append(config_from_namespace)
        config_new.update(config_from_namespace)
    configs_ordered.append(config_kwargs)

    config_new.update(config_kwargs)
    new_model_config = ConfigDict(config_new)  # type: ignore

    prepare_config(new_model_config, cls_name)
    return new_model_config


def prepare_config(config: ConfigDict | dict[str, Any], error_label: str) -> None:
    extra = config.get('extra')
    if extra is not None and not isinstance(extra, Extra):
        try:
            config['extra'] = Extra(extra)
        except ValueError as e:
            raise ValueError(f'{error_label!r}: {extra!r} is not a valid value for config[{"extra"!r}]') from e
