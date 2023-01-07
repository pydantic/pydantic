from __future__ import annotations as _annotations

import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, ForwardRef, Optional, Tuple, Type, Union

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

__all__ = 'BaseConfig', 'ConfigDict', 'get_config', 'Extra', 'build_config', 'prepare_config'


class Extra(str, Enum):
    allow = 'allow'
    ignore = 'ignore'
    forbid = 'forbid'


class ConfigDict(TypedDict, total=False):
    title: Optional[str]
    str_to_lower: bool
    str_to_upper: bool
    str_min_length: int
    str_max_length: Optional[int]
    extra: Extra
    frozen: bool
    populate_by_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool
    from_attributes: bool
    alias_generator: Optional[Callable[[str], str]]
    keep_untouched: Tuple[type, ...]
    json_loads: Callable[[str], object]
    json_dumps: Callable[..., Any]
    json_encoders: Dict[Type[object], Callable[..., Any]]
    allow_inf_nan: bool
    copy_on_model_validation: Literal['none', 'deep', 'shallow']
    post_init_call: Literal['before_validation', 'after_validation']


config_keys = {*ConfigDict.__annotations__.keys(), 'undefined_types_warning'}


class BaseConfig(TypedDict, total=False):
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

    # TODO where to impelement these two classmethods?
    # @classmethod
    # def get_field_info(cls, name: str) -> Dict[str, Any]:
    #     """
    #     Get properties of FieldInfo from the `fields` property of the config class.
    #     """

    #     fields_value = cls.fields.get(name)

    #     if isinstance(fields_value, str):
    #         field_info: Dict[str, Any] = {'alias': fields_value}
    #     elif isinstance(fields_value, dict):
    #         field_info = fields_value
    #     else:
    #         field_info = {}

    #     if 'alias' in field_info:
    #         field_info.setdefault('alias_priority', 2)

    #     if field_info.get('alias_priority', 0) <= 1 and cls.alias_generator:
    #         alias = cls.alias_generator(name)
    #         if not isinstance(alias, str):
    #             raise TypeError(f'Config.alias_generator must return str, not {alias.__class__}')
    #         field_info.update(alias=alias, alias_priority=1)
    #     return field_info

    # @classmethod
    # def prepare_field(cls, field: Any) -> None:
    #     """
    #     Optional hook to check or modify fields during model creation.
    #     """
    #     pass


def _default_base_config() -> BaseConfig:
    return BaseConfig(
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
    )


def get_config(config: Union[ConfigDict, Type[object], None] = None) -> BaseConfig:
    if config is None:
        return _default_base_config()

    else:
        config_dict = (
            config
            if isinstance(config, dict)
            else {k: getattr(config, k) for k in dir(config) if not k.startswith('__')}
        )
        config_new = _default_base_config()
        config_new.update(config_dict)  # type:ignore
        return config_new


def build_config(
    cls_name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any], kwargs: dict[str, Any]
) -> BaseConfig:
    """
    Build a new BaseConfig instance based on (from lowest to highest)
    - default options
    - options defined in base
    - options defined in namespace
    - options defined via kwargs
    """
    config_kwargs = {k: kwargs.pop(k) for k in list(kwargs.keys()) if k in config_keys}

    config_default = dict(_default_base_config())
    config_bases = {}
    configs_ordered = [config_default]
    # collect all config options from bases
    # to avoid that options will be overriden by default-values we just take value != default-value
    for base in bases:
        config = getattr(base, 'model_config', {})
        if config:
            configs_ordered.append(config)
            config_bases.update({key: value for key, value in config.items() if config_default[key] != value})
    config_new = dict(tuple(config_default.items()) + tuple(config_bases.items()))

    config_from_namespace = namespace.get('model_config')
    if config_from_namespace:
        configs_ordered.append(config_from_namespace)
        config_new.update(config_from_namespace)
    configs_ordered.append(config_kwargs)

    config_new.update(config_kwargs)
    new_model_config = BaseConfig(config_new)  # type: ignore
    # merge `json_encoders`-dict in correct order
    new_model_config['json_encoders'] = {}
    for c in configs_ordered:
        new_model_config['json_encoders'].update(c.get('json_encoders', {}))

    prepare_config(new_model_config, cls_name)
    return new_model_config


def prepare_config(config: BaseConfig, cls_name: str) -> None:
    if not isinstance(config['extra'], Extra):
        try:
            config['extra'] = Extra(config['extra'])
        except ValueError:
            raise ValueError(f'"{cls_name}": {config["extra"]} is not a valid value for "extra"')
