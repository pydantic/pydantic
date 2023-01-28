from __future__ import annotations as _annotations

import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, ForwardRef, Optional, Tuple, Type, Union
import warnings

from typing_extensions import Literal, Protocol, TypedDict

if TYPE_CHECKING:
    from typing import overload

    from .main import BaseModel

    class SchemaExtraCallable(Protocol):
        @overload
        def __call__(self, schema: Dict[str, Any]) -> None:
            pass

        @overload
        def __call__(self, schema: Dict[str, Any], model_class: Type[BaseModel]) -> None:
            pass

else:
    SchemaExtraCallable = Callable[..., None]

__all__ = 'BaseConfig', 'ConfigDict', 'Extra', 'build_config', 'prepare_config'


class Extra(str, Enum):
    allow = 'allow'
    ignore = 'ignore'
    forbid = 'forbid'


class _ConfigDict(TypedDict, total=False):
    title: Optional[str]
    str_to_lower: bool
    str_to_upper: bool
    str_strip_whitespace: bool
    str_min_length: int
    str_max_length: Optional[int]
    extra: Extra
    frozen: bool
    populate_by_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool  # TODO default True, or remove
    undefined_types_warning: bool  # TODO review docs
    from_attributes: bool
    alias_generator: Optional[Callable[[str], str]]
    keep_untouched: Tuple[type, ...]  # TODO remove??
    schema_extra: Union[Dict[str, Any], 'SchemaExtraCallable']  # TODO remove, new model method
    json_loads: Callable[[str], Any]  # TODO decide
    json_dumps: Callable[..., str]  # TODO decide
    json_encoders: Dict[Union[Type[Any], str, ForwardRef], Callable[..., Any]]  # TODO decide
    allow_inf_nan: bool

    strict: bool

    # whether inherited models as fields should be reconstructed as base model,
    # and whether such a copy should be shallow or deep
    copy_on_model_validation: Literal['none', 'deep', 'shallow']  # TODO remove???

    # whether dataclass `__post_init__` should be run before or after validation
    post_init_call: Literal['before_validation', 'after_validation']  # TODO remove


config_keys = set(_ConfigDict.__annotations__.keys())


if TYPE_CHECKING:

    class ConfigDict(_ConfigDict):
        ...

else:

    class ConfigDict(dict):
        def __missing__(self, key):
            return _default_config[key]


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
)


class BaseConfig:
    title: Optional[str] = None
    str_to_lower: bool = False
    str_to_upper: bool = False
    str_strip_whitespace: bool = False
    str_min_length: int = 0
    str_max_length: Optional[int] = None
    extra: Extra = Extra.ignore
    frozen: bool = False
    populate_by_name: bool = False
    use_enum_values: bool = False
    validate_assignment: bool = False
    arbitrary_types_allowed: bool = False
    undefined_types_warning: bool = True
    from_attributes: bool = False
    alias_generator: Optional[Callable[[str], str]] = None
    keep_untouched: Tuple[type, ...] = ()
    json_loads: Callable[[str], Any] = json.loads
    json_dumps: Callable[..., str] = json.dumps
    json_encoders: Dict[Union[Type[Any], str, ForwardRef], Callable[..., Any]] = {}
    allow_inf_nan: bool = True
    strict: bool = False
    copy_on_model_validation: Literal['none', 'deep', 'shallow'] = 'shallow'
    post_init_call: Literal['before_validation', 'after_validation'] = 'before_validation'


def get_config(config: Union[ConfigDict, Type[object], None]) -> ConfigDict:
    if config is None:
        return ConfigDict()

    if not isinstance(config, dict):
        warnings.warn(
            f'Support for "config" as "{type(config)}" is deprecated' ' and will be removed in a future version"',
            DeprecationWarning,
        )

    config_dict = (
        config if isinstance(config, dict) else {k: getattr(config, k) for k in dir(config) if not k.startswith('__')}
    )

    return config_dict  # type: ignore


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

    config_from_namespace = (
        get_config(config_class_from_namespace) if config_class_from_namespace else namespace.get('model_config')
    )
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
