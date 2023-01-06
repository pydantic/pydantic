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
    extra: Extra
    frozen: bool
    allow_population_by_field_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool
    orm_mode: bool
    alias_generator: Optional[Callable[[str], str]]
    keep_untouched: Tuple[type, ...]
    json_loads: Callable[[str], object]
    json_dumps: Callable[..., Any]
    json_encoders: Dict[Type[object], Callable[..., Any]]
    allow_inf_nan: bool
    copy_on_model_validation: Literal['none', 'deep', 'shallow']
    post_init_call: Literal['before_validation', 'after_validation']


config_keys = set([*ConfigDict.__annotations__.keys(), 'undefined_types_warning'])


class BaseConfig(TypedDict, total=False):
    title: Optional[str]
    anystr_lower: bool  # TODO rename to str_to_lower
    anystr_upper: bool  # TODO rename to str_to_upper
    anystr_strip_whitespace: bool  # TODO rename to str_strip_whitespace
    min_anystr_length: int  # TODO rename to str_min_length
    max_anystr_length: Optional[int]  # TODO rename to str_max_length
    extra: Extra
    frozen: bool
    allow_population_by_field_name: bool  # TODO rename to populate_by_name
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool  # TODO default True, or remove
    undefined_types_warning: bool  # TODO review docs
    orm_mode: bool  # TODO rename to from_attributes
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
        anystr_lower=False,
        anystr_upper=False,
        anystr_strip_whitespace=False,
        min_anystr_length=0,
        max_anystr_length=None,
        extra=Extra.ignore,
        frozen=False,
        allow_population_by_field_name=False,
        use_enum_values=False,
        validate_assignment=False,
        arbitrary_types_allowed=False,
        undefined_types_warning=True,
        orm_mode=False,
        alias_generator=None,
        keep_untouched=(),
        json_loads=json.loads,
        json_dumps=json.dumps,
        json_encoders={},
        allow_inf_nan=True,
        strict=False,
        copy_on_model_validation='shallow',
    )


def get_config(config: Union[ConfigDict, Type[object], None]) -> BaseConfig:
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


def inherit_config(self_config: BaseConfig, parent_config: BaseConfig, **namespace: Any) -> BaseConfig:
    # # TODO remove
    # if not self_config:
    #     base_classes: Tuple['ConfigType', ...] = (parent_config,)
    # elif self_config == parent_config:
    #     base_classes = (self_config,)
    # else:
    #     base_classes = self_config, parent_config

    namespace['json_encoders'] = {
        **getattr(parent_config, 'json_encoders', {}),
        **getattr(self_config, 'json_encoders', {}),
        **namespace.get('json_encoders', {}),
    }

    # return type('Config', base_classes, namespace)
    return self_config


def build_config(
    cls_name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any], kwargs: dict[str, Any]
) -> BaseConfig:
    """
    TODO update once we're sure what this does.

    Note: merging json_encoders is not currently implemented
    """
    config_kwargs = {k: kwargs.pop(k) for k in list(kwargs.keys()) if k in config_keys}

    config_default = dict(_default_base_config())
    config_bases = {}
    for base in bases:
        config: Optional[Dict[str, object]] = getattr(base, 'model_config', None)
        if config:
            config_bases.update({key: value for key, value in config.items() if config_default[key] != value})
    config_new = dict(list(config_default.items()) + list(config_bases.items()))

    config_from_namespace = namespace.get('model_config', None)
    if config_from_namespace:
        if not isinstance(config_from_namespace, dict):
            raise ValueError(f'"{cls_name}": {config_from_namespace} must be of type {dict}')
        config_new.update(config_from_namespace)

    config_new.update(config_kwargs)
    new_model_config = BaseConfig(config_new)  # type: ignore
    prepare_config(new_model_config, cls_name)
    return new_model_config


def prepare_config(config: BaseConfig, cls_name: str) -> None:
    if not isinstance(config['extra'], Extra):
        try:
            config['extra'] = Extra(config['extra'])
        except ValueError:
            raise ValueError(f'"{cls_name}": {config["extra"]} is not a valid value for "extra"')
