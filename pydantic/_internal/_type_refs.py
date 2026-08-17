"""Logic related to reference computation for types."""

from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin

from typing_extensions import Sentinel, TypeAliasType

from . import _repr
from ._import_utils import import_cached_base_model
from ._utils import lenient_issubclass

if TYPE_CHECKING:
    from pydantic import BaseModel


def _args_ref(args: tuple[Any, ...]) -> str:
    arg_refs: list[str] = []
    for arg in args:
        if isinstance(arg, str):
            # Handle string args as a special case; we may be able to remove this special handling if we
            # wrap them in a ForwardRef at some point.
            arg_ref = f'{arg}:str-{id(arg)}'
        else:
            arg_ref = f'{_repr.display_as_type(arg)}:{id(arg)}'
        arg_refs.append(arg_ref)

    if arg_refs:
        return f'[{",".join(arg_refs)}]'
    else:
        return ''


def model_type_ref(type_: type[BaseModel], args_override: tuple[Any, ...] | None = None) -> str:
    """Produce a reference for Pydantic base models."""
    try:
        generic_metadata = type_.__pydantic_generic_metadata__
    except AttributeError:
        # `type_` is `BaseModel`:
        return f'{type_.__module__}.{type_.__qualname__}:{id(type_)}'

    origin = generic_metadata['origin'] or type_
    args = generic_metadata['args']
    if not args and args_override is not None:
        args = args_override

    # While it is typed as `str`, `__module__` could in theory be `None`:
    module_name = cast(str | None, origin.__module__)
    if module_name is None:
        module_name = '<No __module__>'

    return f'{module_name}.{origin.__qualname__}:{id(origin)}{_args_ref(args)}'


def class_type_ref(type_: Any, origin: type[Any] | None) -> str:
    """Produce a reference for an arbitrary class (dataclasses, typed dictionaries, named tuples)."""
    tp: type[Any] = origin if origin is not None else type_

    # While it is typed as `str`, `__module__` could in theory be `None`:
    module_name = cast(str | None, tp.__module__)
    if module_name is None:
        module_name = '<No __module__>'

    return f'{module_name}.{tp.__qualname__}:{id(tp)}{_args_ref(get_args(type_))}'


_NOT_PROVIDED = Sentinel('_NOT_PROVIDED')


def any_class_type_ref(type_: Any, origin: type[Any] | None | _NOT_PROVIDED = _NOT_PROVIDED) -> str:
    """Produce a reference for any class kind, including Pydantic models."""
    BaseModel_ = import_cached_base_model()

    if lenient_issubclass(type_, BaseModel_):
        return model_type_ref(type_)  # pyright: ignore[reportArgumentType]

    origin = get_origin(type_) if origin is _NOT_PROVIDED else origin
    return class_type_ref(type_, origin)  # pyright: ignore[reportArgumentType] (https://github.com/microsoft/pyright/issues/11115)


def any_type_ref(type_: Any, origin: Any | _NOT_PROVIDED = _NOT_PROVIDED) -> str:
    """Produce a reference for any object, including non-class objects."""
    BaseModel_ = import_cached_base_model()

    if lenient_issubclass(type_, BaseModel_):
        return model_type_ref(type_)  # pyright: ignore[reportArgumentType]

    origin = get_origin(type_) if origin is _NOT_PROVIDED else origin
    tp: Any = origin if origin is not None else type_

    module_name = getattr(tp, '__module__', None)
    if module_name is None:
        module_name = '<No __module__>'

    try:
        qualname = getattr(tp, '__qualname__', f'<No __qualname__: {tp}>')
    except Exception:
        qualname = getattr(tp, '__qualname__', '<No __qualname__>')

    return f'{module_name}.{qualname}:{id(tp)}{_args_ref(get_args(type_))}'


def enum_type_ref(type_: type[Enum]) -> str:
    """Produce a reference for an enum class."""
    # While it is typed as `str`, `__module__` could in theory be `None`:
    module_name = cast(str | None, type_.__module__)
    if module_name is None:
        module_name = '<No __module__>'

    return f'{module_name}.{type_.__qualname__}:{id(type_)}'


def type_alias_type_ref(type_: TypeAliasType) -> str:
    """Produce a reference for a type alias."""
    origin: TypeAliasType = get_origin(type_) or type_

    module_name = type_.__module__
    if module_name is None:
        module_name = '<No __module__>'

    if sys.version_info >= (3, 15):
        type_ref = f'{module_name}.{origin.__qualname__}:{id(origin)}'
    else:
        type_ref = f'{module_name}.{origin.__name__}:{id(origin)}'

    return f'{type_ref}{_args_ref(get_args(type_))}'
