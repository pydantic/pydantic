import sys
import typing
from types import prepare_class, resolve_bases
from typing import Any

TypeVarType = Any  # since mypy doesn't allow the use of TypeVar as a type
Parametrization = typing.Mapping[TypeVarType, type[Any]]

if typing.TYPE_CHECKING:
    from pydantic import BaseModel

    class GenericBaseModel(BaseModel):
        __parameters__: typing.ClassVar[typing.Tuple[TypeVarType, ...]]


def create_generic_submodel(model_name: str, base: type['GenericBaseModel']) -> type['GenericBaseModel']:
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


def _get_caller_frame_info(depth: int = 2) -> typing.Tuple[typing.Optional[str], bool]:
    """
    Used inside a function to check whether it was called globally

    Will only work against non-compiled code, therefore used only in pydantic.generics

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


def is_generic_model(x: type['BaseModel']) -> typing.TypeGuard[type['GenericBaseModel']]:
    return issubclass(x, typing.Generic)  # type: ignore[arg-type]
