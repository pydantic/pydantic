import typing
from typing import no_type_check, Tuple, Type, Dict, Any

from typing_extensions import dataclass_transform

from ._internal.typing_extra import is_classvar


# TODO add `field_specifiers`
from .fields import is_finalvar_with_default_val


@dataclass_transform(kw_only_default=True)
class ModelMetaclass(type):
    @no_type_check
    def __new__(mcs, name: str, bases: Tuple[Type[Any], ...], namespace: Dict[str, Any], **kwargs: Any):
        class_vars: typing.Set[str] = set()
        annotations = namespace.get('__annotations__', {})
        for ann_name, ann_type in annotations.items():
            if is_classvar(ann_type):
                class_vars.add(ann_name)
            elif is_finalvar_with_default_val(ann_type, namespace.get(ann_name, Undefined)):
                class_vars.add(ann_name)
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class BaseModel(metaclass=ModelMetaclass):
    __slots__ = '__dict__', '__fields_set__'


class Model(BaseModel):
    foo: int
    bar: str
    spam: bool = True
    ham: list[int]
