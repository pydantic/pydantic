"""
Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`.
"""
from __future__ import annotations as _annotations

import dataclasses
import sys
from copy import copy
from typing import TYPE_CHECKING, Any

from . import _typing_extra
from ._config import ConfigWrapper
from ._forward_ref import PydanticForwardRef
from ._repr import Representation
from ._typing_extra import get_cls_type_hints_lenient, get_type_hints, is_classvar, is_finalvar

if TYPE_CHECKING:
    from ..fields import FieldInfo
    from ..main import BaseModel
    from ._dataclasses import StandardDataclass


def get_type_hints_infer_globalns(
    obj: Any,
    localns: dict[str, Any] | None = None,
    include_extras: bool = False,
) -> dict[str, Any]:
    module_name = getattr(obj, '__module__', None)
    globalns: dict[str, Any] | None = None
    if module_name:
        try:
            globalns = sys.modules[module_name].__dict__
        except KeyError:
            # happens occasionally, see https://github.com/pydantic/pydantic/issues/2363
            pass
    return get_type_hints(obj, globalns=globalns, localns=localns, include_extras=include_extras)


class _UndefinedType:
    """
    Singleton class to represent an undefined value.
    """

    def __repr__(self) -> str:
        return 'PydanticUndefined'

    def __copy__(self) -> _UndefinedType:
        return self

    def __reduce__(self) -> str:
        return 'Undefined'

    def __deepcopy__(self, _: Any) -> _UndefinedType:
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


def collect_model_fields(  # noqa: C901
    cls: type[BaseModel],
    bases: tuple[type[Any], ...],
    config_wrapper: ConfigWrapper,
    types_namespace: dict[str, Any] | None,
    *,
    typevars_map: dict[Any, Any] | None = None,
) -> tuple[dict[str, FieldInfo], set[str]]:
    """
    Collect the fields of a nascent pydantic model

    Also collect the names of any ClassVars present in the type hints.

    The returned value is a tuple of two items: the fields dict, and the set of ClassVar names.

    :param cls: BaseModel or dataclass
    :param bases: parents of the class, generally `cls.__bases__`
    :param types_namespace: optional extra namespace to look for types in
    """
    from ..fields import FieldInfo

    type_hints = get_cls_type_hints_lenient(cls, types_namespace)

    # https://docs.python.org/3/howto/annotations.html#accessing-the-annotations-dict-of-an-object-in-python-3-9-and-older
    # annotations is only used for finding fields in parent classes
    annotations = cls.__dict__.get('__annotations__', {})
    fields: dict[str, FieldInfo] = {}

    class_vars: set[str] = set()
    for ann_name, ann_type in type_hints.items():
        for protected_namespace in config_wrapper.protected_namespaces:
            if ann_name.startswith(protected_namespace):
                raise NameError(f'Field "{ann_name}" has conflict with protected namespace "{protected_namespace}"')
        if is_classvar(ann_type):
            class_vars.add(ann_name)
            continue
        if _is_finalvar_with_default_val(ann_type, getattr(cls, ann_name, Undefined)):
            class_vars.add(ann_name)
            continue
        if ann_name.startswith('_'):
            continue
        if cls.__pydantic_root_model__ and ann_name != 'root':
            raise NameError(
                f"Unexpected field with name {ann_name!r}; only 'root' is allowed as a field of a `RootModel`"
            )

        # when building a generic model with `MyModel[int]`, the generic_origin check makes sure we don't get
        # "... shadows an attribute" errors
        generic_origin = getattr(cls, '__pydantic_generic_metadata__', {}).get('origin')
        for base in bases:
            if hasattr(base, ann_name):
                if base is generic_origin:
                    # Don't error when "shadowing" of attributes in parametrized generics
                    continue
                raise NameError(
                    f'Field name "{ann_name}" shadows an attribute in parent "{base.__qualname__}"; '
                    f'you might want to use a different field name with "alias=\'{ann_name}\'".'
                )

        try:
            default = getattr(cls, ann_name, Undefined)
            if default is Undefined:
                raise AttributeError
        except AttributeError:
            if ann_name in annotations:
                field_info = FieldInfo.from_annotation(ann_type)
            elif isinstance(ann_type, PydanticForwardRef):
                field_info = FieldInfo.from_annotation(annotation=ann_type)  # type: ignore
            else:
                # if field has no default value and is not in __annotations__ this means that it is
                # defined in a base class and we can take it from there
                model_fields_lookup: dict[str, FieldInfo] = {}
                for x in cls.__bases__[::-1]:
                    model_fields_lookup.update(getattr(x, 'model_fields', {}))
                if ann_name in model_fields_lookup:
                    # The field was present on one of the (possibly multiple) base classes
                    # copy the field to make sure typevar substitutions don't cause issues with the base classes
                    field_info = copy(model_fields_lookup[ann_name])
                else:
                    # The field was not found on any base classes; this seems to be caused by fields not getting
                    # generated thanks to models not being fully defined while initializing recursive models.
                    # Nothing stops us from just creating a new FieldInfo for this type hint, so we do this.
                    field_info = FieldInfo.from_annotation(ann_type)
        else:
            field_info = FieldInfo.from_annotated_attribute(ann_type, default)
            # attributes which are fields are removed from the class namespace:
            # 1. To match the behaviour of annotation-only fields
            # 2. To avoid false positives in the NameError check above
            try:
                delattr(cls, ann_name)
            except AttributeError:
                pass  # indicates the attribute was on a parent class

        fields[ann_name] = field_info

    if typevars_map:
        for field in fields.values():
            field.apply_typevars_map(typevars_map, types_namespace)

    return fields, class_vars


def _is_finalvar_with_default_val(type_: type[Any], val: Any) -> bool:
    from ..fields import FieldInfo

    if not is_finalvar(type_):
        return False
    elif val is Undefined:
        return False
    elif isinstance(val, FieldInfo) and (val.default is Undefined and val.default_factory is None):
        return False
    else:
        return True


def collect_dataclass_fields(
    cls: type[StandardDataclass], types_namespace: dict[str, Any] | None, *, typevars_map: dict[Any, Any] | None = None
) -> dict[str, FieldInfo]:
    from ..fields import FieldInfo

    fields: dict[str, FieldInfo] = {}
    dataclass_fields: dict[str, dataclasses.Field] = cls.__dataclass_fields__
    cls_localns = dict(vars(cls))  # this matches get_cls_type_hints_lenient, but all tests pass with `= None` instead

    for ann_name, dataclass_field in dataclass_fields.items():
        ann_type = _typing_extra.eval_type_lenient(dataclass_field.type, types_namespace, cls_localns)
        if is_classvar(ann_type):
            continue

        if not dataclass_field.init:
            # TODO: We should probably do something with this so that validate_assignment behaves properly
            #   Issue: https://github.com/pydantic/pydantic/issues/5470
            continue

        if isinstance(dataclass_field.default, FieldInfo):
            field_info = FieldInfo.from_annotated_attribute(ann_type, dataclass_field.default)
        else:
            field_info = FieldInfo.from_annotated_attribute(ann_type, dataclass_field)
        fields[ann_name] = field_info

        if field_info.default is not Undefined:
            # We need this to fix the default when the "default" from __dataclass_fields__ is a pydantic.FieldInfo
            setattr(cls, ann_name, field_info.default)

    if typevars_map:
        for field in fields.values():
            field.apply_typevars_map(typevars_map, types_namespace)

    return fields
