from __future__ import annotations as _annotations

import json
import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, ForwardRef

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
    # TODO: We should raise a warning when building a model class if a now-invalid config key is present
    title: str | None
    str_to_lower: bool
    str_to_upper: bool
    str_strip_whitespace: bool
    str_min_length: int
    str_max_length: int | None
    extra: Extra
    frozen: bool
    populate_by_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool  # TODO default True, or remove
    undefined_types_warning: bool  # TODO review docs
    from_attributes: bool
    alias_generator: Callable[[str], str] | None
    keep_untouched: tuple[type, ...]  # TODO remove??
    json_loads: Callable[[str], Any]  # TODO decide
    json_dumps: Callable[..., str]  # TODO decide
    json_encoders: dict[type[Any] | str | ForwardRef, Callable[..., Any]]  # TODO decide
    allow_inf_nan: bool

    strict: bool

    # whether inherited models as fields should be reconstructed as base model,
    # and whether such a copy should be shallow or deep
    copy_on_model_validation: Literal['none', 'deep', 'shallow']  # TODO remove???

    # whether dataclass `__post_init__` should be run before or after validation
    post_init_call: Literal['before_validation', 'after_validation']  # TODO remove

    # new in V2
    ser_json_timedelta: Literal['iso8601', 'float']
    ser_json_bytes: Literal['utf8', 'base64']
    validate_default: bool


config_keys = set(_ConfigDict.__annotations__.keys())

if TYPE_CHECKING:

    class ConfigDict(_ConfigDict):
        ...

else:

    class ConfigDict(dict):
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
    extra=Extra.ignore,
    frozen=False,
    populate_by_name=False,
    use_enum_values=False,
    validate_assignment=False,
    arbitrary_types_allowed=False,
    undefined_types_warning=True,
    from_attributes=False,
    alias_generator=None,
    keep_untouched=(),
    json_loads=json.loads,
    json_dumps=json.dumps,
    json_encoders={},
    allow_inf_nan=True,
    strict=False,
    copy_on_model_validation='shallow',
    post_init_call='before_validation',
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
            raise AttributeError(f"type object '{self.__name__}' has no attribute {exc}")


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
                raise AttributeError(str(exc))

    def __init_subclass__(cls, **kwargs: Any) -> None:
        warnings.warn(
            '`BaseConfig` is deprecated and will be removed in a future version',
            DeprecationWarning,
        )
        return super().__init_subclass__(**kwargs)


def get_config(config: ConfigDict | dict[str, Any] | type[Any] | None) -> ConfigDict:
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
    # merge `json_encoders`-dict in correct order
    json_encoders = {}
    for c in configs_ordered:
        json_encoders.update(c.get('json_encoders', {}))

    if json_encoders:
        new_model_config['json_encoders'] = json_encoders

    prepare_config(new_model_config, cls_name)
    return new_model_config


def prepare_config(config: ConfigDict, cls_name: str) -> None:
    if not isinstance(config['extra'], Extra):
        try:
            config['extra'] = Extra(config['extra'])
        except ValueError:
            raise ValueError(f'"{cls_name}": {config["extra"]} is not a valid value for "extra"')
