from typing import Any, Dict, Tuple, Type

from pydantic_core import SchemaValidator
from typing_extensions import dataclass_transform

from ._internal.babelfish import generate_field_schema
from ._internal.typing_extra import resolve_annotations
from .fields import Undefined

_base_class_defined = False


@dataclass_transform(kw_only_default=True)
class ModelMetaclass(type):
    def __new__(mcs, name: str, bases: Tuple[Type[Any], ...], namespace: Dict[str, Any], **kwargs: Any):
        if not _base_class_defined:
            namespace['__schema__'] = {'fields': {}}
            return super().__new__(mcs, name, bases, namespace, **kwargs)

        fields = {}
        annotations = resolve_annotations(namespace.get('__annotations__', {}), namespace.get('__module__'))
        for ann_name, ann_type in annotations.items():
            if not ann_name.startswith('_'):
                field_value = namespace.pop(ann_name, Undefined)
                fields[ann_name] = generate_field_schema(ann_type, field_value)

        for var_name, value in namespace.items():
            if not var_name.startswith('_') and var_name not in annotations:
                raise TypeError(f'All fields must include a type annotation, {var_name!r} does not.')

        fields_schema = {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': fields,
        }
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls.__validator__ = SchemaValidator(fields_schema)
        cls.__pydantic_validation_schema__ = {
            'type': 'new-class',
            'class_type': cls,
            'schema': fields_schema,
        }
        return cls


object_setattr = object.__setattr__


class BaseModel(metaclass=ModelMetaclass):
    __slots__ = '__dict__', '__fields_set__'

    def __init__(__pydantic_self__, **data: Any) -> None:
        values, fields_set = __pydantic_self__.__validator__.validate_python(data)
        object_setattr(__pydantic_self__, '__dict__', values)
        object_setattr(__pydantic_self__, '__fields_set__', fields_set)


_base_class_defined = True


class Model(BaseModel):
    foo: int
    bar: str
    spam: bool = True
    ham: list[int]


m = Model(foo='123', bar='abc', ham=[1, 2, 3])
debug(m.__dict__)
