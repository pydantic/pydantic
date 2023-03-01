from __future__ import annotations

import sys
import types
import typing
from types import prepare_class, resolve_bases
from typing import Annotated, Any, Iterator, List, Mapping, TypeVar

import typing_extensions

from ._typing_extra import typing_base
from ._utils import all_identical, lenient_issubclass

TypeVarType = Any  # since mypy doesn't allow the use of TypeVar as a type

if sys.version_info >= (3, 10):
    from typing import _UnionGenericAlias  # type: ignore[attr-defined]

if typing.TYPE_CHECKING:
    from pydantic import BaseModel

    # class GenericBaseModel(BaseModel):
    #     __parameters__: typing.ClassVar[tuple[TypeVarType, ...]]
    #     __pydantic_generic_alias__: typing.ClassVar[Any]
    #     __pydantic_generic_origin__: typing.ClassVar[type['GenericBaseModel']]


def create_generic_submodel(model_name: str, origin: type[BaseModel], args: list[Any], typevars_map) -> type[BaseModel]:
    """
    Dynamically create a submodel of a provided (generic) BaseModel.

    This is used when producing concrete parametrizations of generic models. This function
    only *creates* the new subclass; the schema/validators/serialization must be updated to
    reflect a concrete parametrization elsewhere.

    :param model_name: name of the newly created model
    :param origin: base class for the new model to inherit from
    """
    namespace: dict[str, Any] = {'__module__': origin.__module__}
    bases = (origin,)
    resolved_bases = resolve_bases(bases)
    meta, ns, kwds = prepare_class(model_name, resolved_bases)
    if resolved_bases is not bases:
        ns['__orig_bases__'] = bases
    namespace.update(ns)
    created_model = meta(
        model_name,
        resolved_bases,
        namespace,
        generic_origin=origin,
        generic_args=args,
        typevars_map=typevars_map,
        **kwds,
    )
    # created_model.__parameters__ = base.__parameters__  # TODO: I think this is safe to remove, but not 100% sure yet

    model_module, called_globally = _get_caller_frame_info(depth=3)
    if called_globally:  # create global reference and therefore allow pickling
        object_by_reference = None
        reference_name = model_name
        reference_module_globals = sys.modules[created_model.__module__].__dict__
        while object_by_reference is not created_model:
            object_by_reference = reference_module_globals.setdefault(reference_name, created_model)
            reference_name += '_'

    return created_model


def _get_caller_frame_info(depth: int = 2) -> tuple[str | None, bool]:
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


def is_generic_model(x: type[BaseModel]) -> bool:  # typing.TypeGuard[type[GenericBaseModel]]:
    """
    This TypeGuard serves as a workaround for shortcomings in the ability to check at runtime
    if a (model) class is generic (i.e., inherits from typing.Generic), and also have mypy recognize
    the implications related to attributes.

    # TODO: Remove the above note unless we re-add the GenericBaseModel type-hint
    """
    return issubclass(x, typing.Generic)  # type: ignore[arg-type]


DictValues: type[Any] = {}.values().__class__


def iter_contained_typevars(v: Any) -> Iterator[TypeVarType]:
    """
    Recursively iterate through all subtypes and type args of `v` and yield any typevars that are found.

    This is meant as an alternative to directly accessing the `__parameters__` attribute of a GenericAlias,
    since __parameters__ of (nested) custom classes won't show up in that list.
    """
    from pydantic import BaseModel

    if isinstance(v, TypeVar):
        yield v
    elif (
        # TODO: I think we can/should replace __parameters__ with __pydantic_generic_parameters__
        # We can retain the ability to retrieve __parameters__ for backwards compatibility though
        hasattr(v, '__parameters__')
        and not typing_extensions.get_origin(v)
        and lenient_issubclass(v, BaseModel)
    ):
        yield from v.__parameters__
    elif isinstance(v, (DictValues, list)):
        for var in v:
            yield from iter_contained_typevars(var)
    else:
        args = get_args(v)
        for arg in args:
            yield from iter_contained_typevars(arg)


def get_args(v: Any) -> Any:
    pydantic_generic_args = getattr(v, '__pydantic_generic_args__', None)
    if pydantic_generic_args:
        return pydantic_generic_args
    return typing_extensions.get_args(v)


def get_origin(v: Any) -> Any:
    pydantic_generic_origin = getattr(v, '__pydantic_generic_origin__', None)
    if pydantic_generic_origin:
        return pydantic_generic_origin
    return typing_extensions.get_origin(v)


def replace_types(type_: Any, type_map: Mapping[Any, Any]) -> Any:
    """Return type with all occurrences of `type_map` keys recursively replaced with their values.

    :param type_: Any type, class or generic alias
    :param type_map: Mapping from `TypeVar` instance to concrete types.
    :return: New type representing the basic structure of `type_` with all
        `typevar_map` keys recursively replaced.

    >>> replace_types(Tuple[str, Union[List[str], float]], {str: int})
    Tuple[int, Union[List[int], float]]

    """
    if not type_map:
        return type_

    type_args = get_args(type_)
    origin_type = get_origin(type_)

    if origin_type is Annotated:
        annotated_type, *annotations = type_args
        return Annotated[replace_types(annotated_type, type_map), tuple(annotations)]

    # Having type args is a good indicator that this is a typing module
    # class instantiation or a generic alias of some sort.
    if type_args:
        resolved_type_args = tuple(replace_types(arg, type_map) for arg in type_args)
        if all_identical(type_args, resolved_type_args):
            # If all arguments are the same, there is no need to modify the
            # type or create a new object at all
            return type_
        if (
            origin_type is not None
            and isinstance(type_, typing_base)
            and not isinstance(origin_type, typing_base)
            and getattr(type_, '_name', None) is not None
        ):
            # In python < 3.9 generic aliases don't exist so any of these like `list`,
            # `type` or `collections.abc.Callable` need to be translated.
            # See: https://www.python.org/dev/peps/pep-0585
            origin_type = getattr(typing, type_._name)
        assert origin_type is not None
        # PEP-604 syntax (Ex.: list | str) is represented with a types.UnionType object that does not have __getitem__.
        # We also cannot use isinstance() since we have to compare types.
        if sys.version_info >= (3, 10) and origin_type is types.UnionType:  # noqa: E721
            return _UnionGenericAlias(origin_type, resolved_type_args)
        return origin_type[resolved_type_args]

    # We handle pydantic generic models separately as they don't have the same
    # semantics as "typing" classes or generic aliases
    from pydantic import BaseModel

    if not origin_type and lenient_issubclass(type_, BaseModel) and not getattr(type_, '__concrete__', None):
        type_args = type_.__parameters__
        resolved_type_args = tuple(replace_types(t, type_map) for t in type_args)
        if all_identical(type_args, resolved_type_args):
            return type_
        return type_[resolved_type_args]

    # Handle special case for typehints that can have lists as arguments.
    # `typing.Callable[[int, str], int]` is an example for this.
    if isinstance(type_, (List, list)):
        resolved_list = list(replace_types(element, type_map) for element in type_)
        if all_identical(type_, resolved_list):
            return type_
        return resolved_list

    # For JsonWrapperValue, need to handle its inner type to allow correct parsing
    # of generic Json arguments like Json[T]
    # if not origin_type and lenient_issubclass(type_, JsonWrapper):
    #     type_.inner_type = replace_types(type_.inner_type, type_map)
    #     return type_

    # If all else fails, we try to resolve the type directly and otherwise just
    # return the input with no modifications.
    return type_map.get(type_, type_)


def check_parameters_count(cls: type[BaseModel], parameters: tuple[Any, ...]) -> None:
    actual = len(parameters)
    expected = len(getattr(cls, '__parameters__', ()))
    if actual != expected:
        description = 'many' if actual > expected else 'few'
        raise TypeError(f'Too {description} parameters for {cls}; actual {actual}, expected {expected}')
