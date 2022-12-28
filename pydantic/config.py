from __future__ import annotations as _annotations

import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, ForwardRef, Optional, Tuple, Type, Union

from typing_extensions import Literal, Protocol, TypedDict

if TYPE_CHECKING:
    from typing import overload

    from .main import BaseModel

    ConfigType = Type['BaseConfig']

    class SchemaExtraCallable(Protocol):
        @overload
        def __call__(self, schema: Dict[str, Any]) -> None:
            pass

        @overload
        def __call__(self, schema: Dict[str, Any], model_class: Type[BaseModel]) -> None:
            pass

else:
    SchemaExtraCallable = Callable[..., None]

__all__ = 'BaseConfig', 'ConfigDict', 'get_config', 'Extra', 'build_config', 'inherit_config', 'prepare_config'


class Extra(str, Enum):
    allow = 'allow'
    ignore = 'ignore'
    forbid = 'forbid'


class ConfigDict(TypedDict, total=False):
    title: Optional[str]
    anystr_lower: bool
    anystr_strip_whitespace: bool
    min_anystr_length: int
    max_anystr_length: Optional[int]
    validate_all: bool
    extra: Extra
    allow_mutation: bool
    frozen: bool
    allow_population_by_field_name: bool
    use_enum_values: bool
    fields: Dict[str, Union[str, Dict[str, str]]]
    validate_assignment: bool
    error_msg_templates: Dict[str, str]
    arbitrary_types_allowed: bool
    orm_mode: bool
    alias_generator: Optional[Callable[[str], str]]
    keep_untouched: Tuple[type, ...]
    schema_extra: Union[Dict[str, object], 'SchemaExtraCallable']
    json_loads: Callable[[str], object]
    json_dumps: Callable[..., Any]
    json_encoders: Dict[Type[object], Callable[..., Any]]
    underscore_attrs_are_private: bool
    allow_inf_nan: bool
    copy_on_model_validation: Literal['none', 'deep', 'shallow']
    post_init_call: Literal['before_validation', 'after_validation']


config_keys = set(ConfigDict.__annotations__.keys())


class BaseConfig:
    title: Optional[str] = None
    anystr_lower: bool = False  # TODO rename to str_to_lower
    anystr_upper: bool = False  # TODO rename to str_to_upper
    anystr_strip_whitespace: bool = False  # TODO rename to str_strip_whitespace
    min_anystr_length: int = 0  # TODO rename to str_min_length
    max_anystr_length: Optional[int] = None  # TODO rename to str_max_length
    validate_all: bool = False  # TODO remove
    extra: Extra = Extra.ignore
    allow_mutation: bool = True  # TODO remove - replaced by frozen
    frozen: bool = False
    allow_population_by_field_name: bool = False  # TODO rename to populate_by_name
    use_enum_values: bool = False
    fields: Dict[str, Union[str, Dict[str, str]]] = {}  # TODO remove
    validate_assignment: bool = False
    error_msg_templates: Dict[str, str] = {}  # TODO remove
    arbitrary_types_allowed: bool = False  # TODO default True, or remove
    undefined_types_warning: bool = True  # TODO review docs
    orm_mode: bool = False  # TODO rename to from_attributes
    alias_generator: Optional[Callable[[str], str]] = None
    keep_untouched: Tuple[type, ...] = ()  # TODO remove??
    schema_extra: Union[Dict[str, Any], 'SchemaExtraCallable'] = {}  # TODO remove, new model method
    json_loads: Callable[[str], Any] = json.loads  # TODO decide
    json_dumps: Callable[..., str] = json.dumps  # TODO decide
    json_encoders: Dict[Union[Type[Any], str, ForwardRef], Callable[..., Any]] = {}  # TODO decide
    underscore_attrs_are_private: bool = False  # TODO remove
    allow_inf_nan: bool = True

    strict: bool = False

    # whether inherited models as fields should be reconstructed as base model,
    # and whether such a copy should be shallow or deep
    copy_on_model_validation: Literal['none', 'deep', 'shallow'] = 'shallow'  # TODO remove???

    # whether `Union` should check all allowed types before even trying to coerce
    smart_union: bool = False  # TODO remove
    # whether dataclass `__post_init__` should be run before or after validation
    post_init_call: Literal['before_validation', 'after_validation'] = 'before_validation'  # TODO remove

    @classmethod
    def get_field_info(cls, name: str) -> Dict[str, Any]:
        """
        Get properties of FieldInfo from the `fields` property of the config class.
        """

        fields_value = cls.fields.get(name)

        if isinstance(fields_value, str):
            field_info: Dict[str, Any] = {'alias': fields_value}
        elif isinstance(fields_value, dict):
            field_info = fields_value
        else:
            field_info = {}

        if 'alias' in field_info:
            field_info.setdefault('alias_priority', 2)

        if field_info.get('alias_priority', 0) <= 1 and cls.alias_generator:
            alias = cls.alias_generator(name)
            if not isinstance(alias, str):
                raise TypeError(f'Config.alias_generator must return str, not {alias.__class__}')
            field_info.update(alias=alias, alias_priority=1)
        return field_info

    @classmethod
    def prepare_field(cls, field: Any) -> None:
        """
        Optional hook to check or modify fields during model creation.
        """
        pass


def get_config(config: Union[ConfigDict, Type[object], None]) -> Type[BaseConfig]:
    if config is None:
        return BaseConfig

    else:
        config_dict = (
            config
            if isinstance(config, dict)
            else {k: getattr(config, k) for k in dir(config) if not k.startswith('__')}
        )

        class Config(BaseConfig):
            ...

        for k, v in config_dict.items():
            setattr(Config, k, v)
        return Config


def inherit_config(self_config: 'ConfigType', parent_config: 'ConfigType', **namespace: Any) -> 'ConfigType':
    # TODO remove
    if not self_config:
        base_classes: Tuple['ConfigType', ...] = (parent_config,)
    elif self_config == parent_config:
        base_classes = (self_config,)
    else:
        base_classes = self_config, parent_config

    namespace['json_encoders'] = {
        **getattr(parent_config, 'json_encoders', {}),
        **getattr(self_config, 'json_encoders', {}),
        **namespace.get('json_encoders', {}),
    }

    return type('Config', base_classes, namespace)


def build_config(
    cls_name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any], kwargs: dict[str, Any]
) -> tuple[type[BaseConfig], type[BaseConfig] | None]:
    """
    TODO update once we're sure what this does.

    Note: merging json_encoders is not currently implemented
    """
    config_kwargs = {k: kwargs.pop(k) for k in list(kwargs.keys()) if k in config_keys}
    config_from_namespace = namespace.get('Config')

    config_bases = []
    for base in bases:
        config = getattr(base, 'Config', None)
        if config:
            config_bases.append(config)

    if len(config_bases) == 1 and not any([config_kwargs, config_from_namespace]):
        return BaseConfig, None

    if config_from_namespace:
        config_bases = [config_from_namespace] + config_bases

    combined_config: type[BaseConfig] = type('CombinedConfig', tuple(config_bases), config_kwargs)
    prepare_config(combined_config, cls_name)

    if config_from_namespace and config_kwargs:
        # we want to override `Config` so future inheritance includes config_kwargs
        new_model_config: type[BaseConfig] = type('ConfigWithKwargs', (config_from_namespace,), config_kwargs)
        return combined_config, new_model_config
    else:
        # we want to use CombinedConfig for `__config__`, but we
        return combined_config, combined_config


def prepare_config(config: Type[BaseConfig], cls_name: str) -> None:
    if not isinstance(config.extra, Extra):
        try:
            config.extra = Extra(config.extra)
        except ValueError:
            raise ValueError(f'"{cls_name}": {config.extra} is not a valid value for "extra"')
