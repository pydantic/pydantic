from typing import Any, Dict, Tuple, Type, Union, get_type_hints, no_type_check

from pydantic import BaseModel, create_model
from pydantic.class_validators import gather_validators


class BaseGenericModel:
    """
    This might benefit from being modeled more closely on something like typing_extensions.Protocol
    so that subclasses can inherit directly from BaseGenericModel[T, ...]
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(f"Type {type(self).__name__} cannot be instantiated without providing generic parameters")

    @no_type_check
    def __class_getitem__(cls, params: Union[Any, Tuple[Any, ...]]) -> Type[BaseModel]:
        if not isinstance(params, tuple):
            params = (params,)
        generic_alias = super().__class_getitem__(params)
        __parameters__ = generic_alias.__origin__.__parameters__
        typevars_map = dict(zip(__parameters__, params))
        model_name = f"{cls.__name__}[{generic_name(params)}]"
        __module__ = cls.__module__
        __config__ = None

        if hasattr(cls, "Config"):
            __config__ = cls.Config
        validators = gather_validators(cls)
        type_hints = get_type_hints(cls)
        new_type_hints = resolve_generic_type_hints(type_hints, typevars_map)
        fields = {}
        for k, v in new_type_hints.items():
            fields[k] = (v, getattr(cls, k, ...))
        created_model = create_model(
            model_name=model_name, __module__=__module__, __config__=__config__, __validators__=validators, **fields
        )
        return created_model


def generic_name(params: Tuple[Type[Any], ...]) -> str:
    param_names = []
    for param in params:
        if hasattr(param, "__name__"):
            param_names.append(param.__name__)
        elif hasattr(param, "__origin__"):
            param_names.append(str(param))
        else:
            raise ValueError(f"Couldn't get name for {param}")
    return ", ".join(param_names)


def resolve_generic_type_hints(generic_type_hints: Dict[str, Any], typevars_map: Dict[Any, Any]) -> Dict[str, Any]:
    new_type_hints = {}
    for k, v in generic_type_hints.items():
        new_type_hints[k] = resolve_type_hint(v, typevars_map)
    return new_type_hints


def resolve_type_hint(type_: Any, typevars_map: Dict[Any, Any]) -> Type[Any]:
    if hasattr(type_, "__origin__"):
        new_args = tuple(resolve_type_hint(x, typevars_map) for x in type_.__args__)
        if type_.__origin__ is Union:
            return type_.__origin__[new_args]
        else:
            return type_[new_args]
    return typevars_map.get(type_, type_)
