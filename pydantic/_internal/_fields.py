"""
Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`.
"""
from __future__ import annotations as _annotations

import re
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ForwardRef

from pydantic_core import core_schema
from typing_extensions import Annotated

from ..errors import PydanticUndefinedAnnotation
from ._repr import Representation
from ._typing_extra import get_type_hints, is_classvar

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


class SelfType:
    """
    No-op marker class for `self` type reference.
    """


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
) -> tuple[dict[str, FieldInfo], str]:
    """
    Collect the fields of a pydantic model or dataclass, also returns teh model/class ref to use in the
    core-schema.

    :param cls: BaseModel or dataclass
    :param name: name of the class, generally `cls.__name__`
    :param bases: parents of the class, generally `cls.__bases__`
    :param types_namespace: optional extra namespace to look for types in
    """
    from ..fields import FieldInfo

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

    schema_ref = f'{module_name}.{name}'
    self_schema = core_schema.model_schema(cls, core_schema.recursive_reference_schema(schema_ref))
    local_ns = {name: Annotated[SelfType, SchemaRef(self_schema)]}

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

    cls_fields: dict[str, FieldInfo] = getattr(cls, 'model_fields', None) or getattr(cls, '__pydantic_fields__', {})

    for ann_name, ann_type in type_hints.items():
        if ann_name.startswith('_') or is_classvar(ann_type):
            continue

        # raise a PydanticUndefinedAnnotation if type is undefined
        if isinstance(ann_type, ForwardRef):
            raise PydanticUndefinedAnnotation(ann_type.__forward_arg__)

        for base in bases:
            if hasattr(base, ann_name):
                raise NameError(
                    f'Field name "{ann_name}" shadows an attribute in parent "{base.__qualname__}"; '
                    f'you might want to use a different field name with "alias=\'{ann_name}\'".'
                )

        try:
            default = getattr(cls, ann_name)
        except AttributeError:
            # if field has no default value and is not in __annotations__ this means that it is
            # defined in a base class and we can take it from there
            if ann_name in annotations:
                fields[ann_name] = FieldInfo.from_annotation(ann_type)
            else:
                fields[ann_name] = cls_fields[ann_name]
        else:
            fields[ann_name] = FieldInfo.from_annotated_attribute(ann_type, default)
            # attributes which are fields are removed from the class namespace:
            # 1. To match the behaviour of annotation-only fields
            # 2. To avoid false positives in the NameError check above
            delattr(cls, ann_name)

    return fields, schema_ref
