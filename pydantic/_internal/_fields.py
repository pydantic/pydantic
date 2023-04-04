"""
Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`.
"""
from __future__ import annotations as _annotations

import dataclasses
import sys
import typing
from abc import ABC, abstractmethod
from copy import copy
from typing import TYPE_CHECKING, Any

from pydantic_core import core_schema

from ._forward_ref import PydanticForwardRef
from ._generics import replace_types
from ._repr import Representation
from ._typing_extra import get_cls_type_hints_lenient, get_type_hints, is_classvar

if TYPE_CHECKING:
    from ..fields import FieldInfo


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
    def __call__(self, __input_value: Any, __info: core_schema.ValidationInfo) -> Any:
        raise NotImplementedError()

    def _update_attrs(self, constraints: dict[str, Any], attrs: set[str] | None = None) -> None:
        """
        Utility for updating attributes/slots and raising an error if they don't exist, to be used by
        implementations of `CustomValidator`.
        """
        attrs = attrs or set(self.__slots__)  # type: ignore[attr-defined]
        for k, v in constraints.items():
            if k not in attrs:
                raise TypeError(f'{k!r} is not a valid constraint for {self.__class__.__name__}')
            setattr(self, k, v)


# KW_ONLY is only available in Python 3.10+
DC_KW_ONLY = getattr(dataclasses, 'KW_ONLY', None)


def collect_fields(  # noqa: C901
    cls: type[Any],
    bases: tuple[type[Any], ...],
    types_namespace: dict[str, Any] | None,
    *,
    is_dataclass: bool = False,
    dc_kw_only: bool | None = None,
) -> tuple[dict[str, FieldInfo], set[str]]:
    """
    Collect the fields of:
    * a nascent pydantic model
    * a nascent pydantic dataclass
    * or, a standard library dataclass
    Also collect the names of any ClassVars present in the type hints.

    The returned value is a tuple of two items: the fields dict, and the set of ClassVar names.

    :param cls: BaseModel or dataclass
    :param bases: parents of the class, generally `cls.__bases__`
    :param types_namespace: optional extra namespace to look for types in
    :param is_dataclass: whether the class is a dataclass, used to decide about kw_only setting
    :param dc_kw_only: whether the whole dataclass is kw_only
    """
    from ..fields import FieldInfo

    type_hints = get_cls_type_hints_lenient(cls, types_namespace)

    # https://docs.python.org/3/howto/annotations.html#accessing-the-annotations-dict-of-an-object-in-python-3-9-and-older
    # annotations is only used for finding fields in parent classes
    annotations = cls.__dict__.get('__annotations__', {})
    fields: dict[str, FieldInfo] = {}

    # currently just used for `init=False` dataclass fields, this logic can probably be removed if
    # we simplify this function to not be "all things to all men"
    omitted_fields: set[str] | None = getattr(cls, '__pydantic_omitted_fields__', None)

    class_vars: set[str] = set()
    for ann_name, ann_type in type_hints.items():
        if is_classvar(ann_type):
            class_vars.add(ann_name)
            continue
        if ann_name.startswith('_') or (omitted_fields and ann_name in omitted_fields):
            continue

        if DC_KW_ONLY and ann_type is DC_KW_ONLY:
            # all field fields will be kw_only
            dc_kw_only = True
            continue
        kw_only = dc_kw_only

        init_var = False
        if ann_type is dataclasses.InitVar:
            if sys.version_info < (3, 8):
                raise RuntimeError('InitVar is not supported in Python 3.7 as type information is lost')

            init_var = True
            ann_type = Any
        elif isinstance(ann_type, dataclasses.InitVar):
            init_var = True
            ann_type = ann_type.type

        # when building a generic model with `MyModel[int]`, the generic_origin check makes sure we don't get
        # "... shadows an attribute" errors
        generic_origin = getattr(cls, '__pydantic_generic_origin__', None)
        for base in bases:
            if hasattr(base, ann_name):
                if base is generic_origin:
                    # Don't error when "shadowing" of attributes in parametrized generics
                    continue
                if is_dataclass and dataclasses.is_dataclass(base):
                    # Don't error when shadowing a field in a parent dataclass
                    continue
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
                field_info = FieldInfo.from_annotation(ann_type)
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
            if isinstance(default, dataclasses.Field):
                if not default.init:
                    # dataclasses.Field with init=False are not fields
                    continue
                if DC_KW_ONLY and default.kw_only is True:
                    kw_only = True

            field_info = FieldInfo.from_annotated_attribute(ann_type, default)
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

            if is_dataclass:
                # for dataclasses we preserve the default value if it is set
                # field, e.g. `a: int = 1` gets kept as is
                # and `a: int = field(default=1, repr=False)` gets converted to the above
                if isinstance(default, (dataclasses.Field, FieldInfo)):
                    if default.default not in (
                        Undefined,
                        dataclasses.MISSING,
                    ):
                        setattr(cls, ann_name, default.default)
                else:
                    # not a field default
                    setattr(cls, ann_name, default)

        if init_var:
            field_info.init_var = True
        if kw_only is not None:
            field_info.kw_only = kw_only
        fields[ann_name] = field_info

    typevars_map = getattr(cls, '__pydantic_generic_typevars_map__', None)
    if typevars_map:
        for field in fields.values():
            try:
                field.annotation = typing._eval_type(  # type: ignore[attr-defined]
                    field.annotation, types_namespace, None
                )
            except NameError:
                pass
            field.annotation = replace_types(field.annotation, typevars_map)

    return fields, class_vars
