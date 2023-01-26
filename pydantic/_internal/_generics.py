from __future__ import annotations as _annotations

import sys
import typing
from types import prepare_class, resolve_bases
from typing import Any

from typing_extensions import TypeGuard

TypeVarType = Any  # since mypy doesn't allow the use of TypeVar as a type

if typing.TYPE_CHECKING:
    from pydantic import BaseModel

    class GenericBaseModel(BaseModel):
        __parameters__: typing.ClassVar[tuple[TypeVarType, ...]]
        __pydantic_generic_alias__: typing.ClassVar[Any]
        __pydantic_generic_parent__: typing.ClassVar[type[GenericBaseModel]]
        __pydantic_generic_typevars_map__: dict[Any, type[Any]]


def create_generic_submodel(model_name: str, base: type[GenericBaseModel]) -> type[GenericBaseModel]:
    """
    Dynamically create a submodel of a provided (generic) BaseModel.

    This is used when producing concrete parametrizations of generic models. This function
    only *creates* the new subclass; the schema/validators/serialization must be updated to
    reflect a concrete parametrization elsewhere.

    :param model_name: name of the newly created model
    :param base: base class for the new model to inherit from
    """
    namespace: dict[str, Any] = {'__module__': base.__module__}
    bases = (base,)
    resolved_bases = resolve_bases(bases)
    meta, ns, kwds = prepare_class(model_name, resolved_bases)
    if resolved_bases is not bases:
        ns['__orig_bases__'] = bases
    namespace.update(ns)
    created_model = meta(model_name, resolved_bases, namespace, **kwds)
    created_model.__parameters__ = base.__parameters__

    model_module, called_globally = _get_caller_frame_info(depth=3)
    if called_globally:  # create global reference and therefore allow pickling
        object_by_reference = None
        reference_name = model_name
        reference_module_globals = sys.modules[created_model.__module__].__dict__
        while object_by_reference is not created_model:
            object_by_reference = reference_module_globals.setdefault(reference_name, created_model)
            reference_name += '_'

    return created_model


def _get_caller_frame_info(depth: int = 2) -> tuple[typing.Optional[str], bool]:
    """
    Used inside a function to check whether it was called globally

    :returns Tuple[module_name, called_globally]
    """
    try:
        previous_caller_frame = sys._getframe(depth)
    except ValueError as e:
        raise RuntimeError('This function must be used inside another function') from e
    except AttributeError:  # sys module does not have _getframe function, so there's nothing we can do about it
        return None, False
    frame_globals = previous_caller_frame.f_globals
    return frame_globals.get('__name__'), previous_caller_frame.f_locals is frame_globals


def is_generic_model(x: type[BaseModel]) -> TypeGuard[type[GenericBaseModel]]:
    """
    This TypeGuard serves as a workaround for shortcomings in the ability to check at runtime
    if a (model) class is generic (i.e., inherits from typing.Generic), and also have mypy recognize
    the implications related to attributes.

    TODO: Need to make sure that, on all supported versions of python, this check works properly and implies
        that the `__parameters__` attribute exists with the expected contents.
    """
    return issubclass(x, typing.Generic)  # type: ignore[arg-type]
