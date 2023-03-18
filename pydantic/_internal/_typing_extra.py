"""
Logic for interacting with type annotations, mostly extensions, shims and hacks to wrap python's typing module.
"""
from __future__ import annotations as _annotations

import sys
import types
import typing
from collections.abc import Callable
from typing import Annotated, Any, Final, ForwardRef, Literal, get_args, get_origin

__all__ = (
    'NoneType',
    'is_none_type',
    'is_callable_type',
    'is_literal_type',
    'all_literal_values',
    'is_annotated',
    'is_namedtuple',
    'is_new_type',
    'is_classvar',
    'is_finalvar',
    'WithArgsTypes',
    'typing_base',
    'origin_is_union',
    'NotRequired',
    'Required',
    'parent_frame_namespace',
    'get_type_hints',
    'EllipsisType',
)

try:
    from typing import _TypingBase  # type: ignore[attr-defined]
except ImportError:
    from typing import _Final as _TypingBase  # type: ignore[attr-defined]

typing_base = _TypingBase


from typing import GenericAlias as TypingGenericAlias  # type: ignore # noqa: E402

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Required
else:
    from typing import NotRequired, Required


if sys.version_info < (3, 10):

    def origin_is_union(tp: type[Any] | None) -> bool:
        return tp is typing.Union

    WithArgsTypes = (TypingGenericAlias,)

else:

    def origin_is_union(tp: type[Any] | None) -> bool:
        return tp is typing.Union or tp is types.UnionType  # noqa: E721

    WithArgsTypes = typing._GenericAlias, types.GenericAlias, types.UnionType  # type: ignore[attr-defined]


if sys.version_info < (3, 10):
    NoneType = type(None)
    EllipsisType = type(Ellipsis)
else:
    from types import EllipsisType as EllipsisType
    from types import NoneType as NoneType


NONE_TYPES: tuple[Any, Any, Any] = (None, NoneType, Literal[None])


TypeVarType = Any  # since mypy doesn't allow the use of TypeVar as a type


if sys.version_info[:2] == (3, 8):

    def is_none_type(type_: Any) -> bool:
        for none_type in NONE_TYPES:
            if type_ is none_type:
                return True
        # With python 3.8, specifically 3.8.10, Literal "is" checks are very flakey
        # can change on very subtle changes like use of types in other modules,
        # hopefully this check avoids that issue.
        if is_literal_type(type_):  # pragma: no cover
            return all_literal_values(type_) == (None,)
        return False

else:

    def is_none_type(type_: Any) -> bool:
        for none_type in NONE_TYPES:
            if type_ is none_type:
                return True
        return False


def is_callable_type(type_: type[Any]) -> bool:
    return type_ is Callable or get_origin(type_) is Callable


def is_literal_type(type_: type[Any]) -> bool:
    return Literal is not None and get_origin(type_) is Literal


def literal_values(type_: type[Any]) -> tuple[Any, ...]:
    return get_args(type_)


def all_literal_values(type_: type[Any]) -> tuple[Any, ...]:
    """
    This method is used to retrieve all Literal values as
    Literal can be used recursively (see https://www.python.org/dev/peps/pep-0586)
    e.g. `Literal[Literal[Literal[1, 2, 3], "foo"], 5, None]`
    """
    if not is_literal_type(type_):
        return (type_,)

    values = literal_values(type_)
    return tuple(x for value in values for x in all_literal_values(value))


def is_annotated(ann_type: Any) -> bool:
    from ._utils import lenient_issubclass

    origin = get_origin(ann_type)
    return origin is not None and lenient_issubclass(origin, Annotated)


def is_namedtuple(type_: type[Any]) -> bool:
    """
    Check if a given class is a named tuple.
    It can be either a `typing.NamedTuple` or `collections.namedtuple`
    """
    from ._utils import lenient_issubclass

    return lenient_issubclass(type_, tuple) and hasattr(type_, '_fields')


test_new_type = typing.NewType('test_new_type', str)


def is_new_type(type_: type[Any]) -> bool:
    """
    Check whether type_ was created using typing.NewType.

    Can't use isinstance because it fails <3.10.
    """
    return isinstance(type_, test_new_type.__class__) and hasattr(type_, '__supertype__')  # type: ignore[arg-type]


def _check_classvar(v: type[Any] | None) -> bool:
    if v is None:
        return False

    return v.__class__ == typing.ClassVar.__class__ and getattr(v, '_name', None) == 'ClassVar'


def is_classvar(ann_type: type[Any]) -> bool:
    if _check_classvar(ann_type) or _check_classvar(get_origin(ann_type)):
        return True

    # this is an ugly workaround for class vars that contain forward references and are therefore themselves
    # forward references, see #3679
    if ann_type.__class__ == typing.ForwardRef and ann_type.__forward_arg__.startswith('ClassVar['):
        return True

    return False


def _check_finalvar(v: type[Any] | None) -> bool:
    """
    Check if a given type is a `typing.Final` type.
    """
    if v is None:
        return False

    return v.__class__ == Final.__class__ and (sys.version_info < (3, 8) or getattr(v, '_name', None) == 'Final')


def is_finalvar(ann_type: type[Any]) -> bool:
    return _check_finalvar(ann_type) or _check_finalvar(get_origin(ann_type))


def parent_frame_namespace(*, parent_depth: int = 2) -> dict[str, Any] | None:
    """
    We allow use of items in parent namespace to get around the issue with `get_type_hints` only looking in the
    global module namespace. See https://github.com/pydantic/pydantic/issues/2678#issuecomment-1008139014 -> Scope
    and suggestion at the end of the next comment by @gvanrossum.

    WARNING 1: it matters exactly where this is called. By default, this function will build a namespace from the
    parent of where it is called.

    WARNING 2: this only looks in the parent namespace, not other parents since (AFAIK) there's no way to collect a
    dict of exactly what's in scope. Using `f_back` would work sometimes but would be very wrong and confusing in many
    other cases. See https://discuss.python.org/t/is-there-a-way-to-access-parent-nested-namespaces/20659.
    """
    frame = sys._getframe(parent_depth)
    # if f_back is None, it's the global module namespace and we don't need to include it here
    if frame.f_back is None:
        return None
    else:
        return frame.f_locals


get_type_hints = typing.get_type_hints


def evaluate_fwd_ref(
    ref: ForwardRef, globalns: dict[str, Any] | None = None, localns: dict[str, Any] | None = None
) -> Any:
    return ref._evaluate(globalns=globalns, localns=localns, recursive_guard=frozenset())
