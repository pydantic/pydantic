"""
Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`.
"""
from __future__ import annotations as _annotations

import dataclasses
import re
import sys
from copy import copy
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ForwardRef

from pydantic_core import core_schema

from ..errors import PydanticUndefinedAnnotation
from ._forward_ref import PydanticForwardRef
from ._repr import Representation
from ._typing_extra import get_type_hints, is_classvar
from ._generics import replace_types

if TYPE_CHECKING:
    from ..fields import FieldInfo


class _UndefinedType:
    """
    Singleton class to represent an undefined value.
    """

    def __repr__(self) -> str:
        return 'PydanticUndefined'

    def __copy__(self) -> '_UndefinedType':
        return self

    def __reduce__(self) -> str:
        return 'Undefined'

    def __deepcopy__(self, _: Any) -> '_UndefinedType':
        return self


Undefined = _UndefinedType()


class PydanticMetadata(Representation):
    """
    Base class for annotation markers like `Strict`.
    """

    __slots__ = ()


class PydanticGeneralMetadata(PydanticMetadata):
    def __init__(self, **metadata: Any):
        self.__dict__ = metadata


class SchemaRef(Representation):
    """
    Holds a reference to another schema.
    """

    __slots__ = ('__pydantic_core_schema__',)

    def __init__(self, schema: core_schema.CoreSchema):
        self.__pydantic_core_schema__ = schema


class CustomValidator(ABC):
    """
    Used to define functional validators which can be updated with constraints.
    """

    @abstractmethod
    def __pydantic_update_schema__(self, schema: core_schema.CoreSchema, **constraints: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def __call__(self, __input_value: Any, **_kwargs: Any) -> Any:
        raise NotImplementedError()

    def _update_attrs(self, constraints: dict[str, Any], attrs: set[str] | None = None) -> None:
        """
        Utility for updating attributes/slots and raising an error if they don't exist, to be used by
        implementations of `CustomValidator`.
        """
        attrs = attrs or set(self.__slots__)  # type: ignore[attr-defined]
        for k, v in constraints.items():
            if k not in attrs:
                raise TypeError(f'{self.__class__.__name__} has no attribute {k!r}')
            setattr(self, k, v)


def collect_fields(  # noqa: C901
    cls: type[Any],
    name: str,
    bases: tuple[type[Any], ...],
    types_namespace: dict[str, Any] | None = None,
    typevars_map: dict[str, Any] | None = None,
) -> tuple[dict[str, FieldInfo], str]:
    """
    Collect the fields of a pydantic model or dataclass, also returns the model/class ref to use in the
    core-schema.

    :param cls: BaseModel or dataclass
    :param name: name of the class, generally `cls.__name__`
    :param bases: parents of the class, generally `cls.__bases__`
    :param types_namespace: optional extra namespace to look for types in
    :param typevars_map: TODO
    """
    from ..fields import FieldInfo
    from ._generate_schema import get_model_self_schema

    module_name = getattr(cls, '__module__', None)
    global_ns: dict[str, Any] | None = None
    if module_name:
        try:
            module = sys.modules[module_name]
        except KeyError:
            # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
            pass
        else:
            if types_namespace:
                global_ns = {**module.__dict__, **types_namespace}
            else:
                global_ns = module.__dict__

    self_schema = get_model_self_schema(cls)
    local_ns = {**(types_namespace or {}), name: PydanticForwardRef(self_schema, cls)}
    # schema_ref = f'{module_name}.{name}'
    # self_schema = core_schema.model_schema(cls, core_schema.recursive_reference_schema(schema_ref))
    # local_ns = {name: Annotated[SelfType, SchemaRef(self_schema)]}

    # get type hints and raise a PydanticUndefinedAnnotation if any types are undefined
    try:
        type_hints = get_type_hints(cls, global_ns, local_ns, include_extras=True)
    except NameError as e:
        try:
            name = e.name
        except AttributeError:
            m = re.search(r".*'(.+?)'", str(e))
            if m:
                name = m.group(1)
            else:
                # should never happen
                raise
        raise PydanticUndefinedAnnotation(name) from e

    # https://docs.python.org/3/howto/annotations.html#accessing-the-annotations-dict-of-an-object-in-python-3-9-and-older
    # annotations is only used for finding fields in parent classes
    annotations = cls.__dict__.get('__annotations__', {})
    fields: dict[str, FieldInfo] = {}

    # cls_fields: dict[str, FieldInfo] = getattr(cls, 'model_fields', None) or getattr(cls, '__pydantic_fields__', {})
    # currently just used for `init=False` dataclass fields, but could be used more
    omitted_fields: set[str] | None = getattr(cls, '__pydantic_omitted_fields__', None)

    for ann_name, ann_type in type_hints.items():
        if ann_name.startswith('_') or is_classvar(ann_type) or (omitted_fields and ann_name in omitted_fields):
            continue

        # raise a PydanticUndefinedAnnotation if type is undefined
        if isinstance(ann_type, ForwardRef):
            raise PydanticUndefinedAnnotation(ann_type.__forward_arg__)

        if cls.__pydantic_generic_typevars_map__:
            ann_type = replace_types(ann_type, cls.__pydantic_generic_typevars_map__)

        generic_origin = cls.__pydantic_generic_origin__
        for base in bases:
            if hasattr(base, ann_name):
                if base is not generic_origin:  # Don't warn about "shadowing" of attributes in parametrized generics
                    raise NameError(
                        f'Field name "{ann_name}" shadows an attribute in parent "{base.__qualname__}"; '
                        f'you might want to use a different field name with "alias=\'{ann_name}\'".'
                    )

        try:
            default = getattr(cls, ann_name, Undefined)
            if default is Undefined and generic_origin:
                default = (generic_origin.__pydantic_generic_defaults__ or {}).get(ann_name, Undefined)
            if default is Undefined:
                raise AttributeError
        except AttributeError:
            if ann_name in annotations or isinstance(ann_type, PydanticForwardRef):
                fields[ann_name] = FieldInfo.from_annotation(ann_type)
            else:
                # # if field has no default value and is not in __annotations__ this means that it is
                # # defined in a base class and we can take it from there
                # fields[ann_name] = cls_fields[ann_name]
                model_fields_lookup: dict[str, FieldInfo] = {}
                for x in cls.__bases__[::-1]:
                    model_fields_lookup.update(getattr(x, 'model_fields', {}))
                if ann_name in model_fields_lookup:
                    # The field was present on one of the (possibly multiple) base classes
                    # copy the field to make sure typevar substitutions don't cause issues with the base classes
                    field = copy(model_fields_lookup[ann_name])
                else:
                    # The field was not found on any base classes; this seems to be caused by fields not getting
                    # generated thanks to models not being fully defined while initializing recursive models.
                    # Nothing stops us from just creating a new FieldInfo for this type hint, so we do this.
                    field = FieldInfo.from_annotation(ann_type)
                fields[ann_name] = field
        else:
            if isinstance(default, dataclasses.Field) and not default.init:
                # dataclasses.Field with init=False are not fields
                continue

            fields[ann_name] = FieldInfo.from_annotated_attribute(ann_type, default)
            # attributes which are fields are removed from the class namespace:
            # 1. To match the behaviour of annotation-only fields
            # 2. To avoid false positives in the NameError check above
            try:
                delattr(cls, ann_name)
                if cls.__pydantic_generic_parameters__:  # model can be parametrized
                    assert cls.__pydantic_generic_defaults__ is not None
                    cls.__pydantic_generic_defaults__[ann_name] = default
            except AttributeError:
                pass  # indicates the attribute was on a parent class

    typevars_map = cls.__pydantic_generic_typevars_map__ or typevars_map
    if typevars_map:
        for field in fields.values():
            field.annotation = replace_types(field.annotation, typevars_map)
    schema_ref = self_schema['schema']['schema_ref']

    return fields, schema_ref
