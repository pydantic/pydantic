"""Bucket of reusable internal utilities.

This should be reduced as much as possible with functions only used in one place, moved to that place.
"""

from __future__ import annotations as _annotations

import dataclasses
import keyword
import weakref
from collections import OrderedDict, defaultdict, deque
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from functools import cached_property
from inspect import Parameter
from itertools import zip_longest
from types import BuiltinFunctionType, CodeType, FunctionType, LambdaType, ModuleType, NoneType
from typing import TYPE_CHECKING, Any, TypeGuard, TypeVar

from pydantic_core import MISSING, PydanticUndefined

from . import _typing_extra
from ._import_utils import import_cached_base_model

if TYPE_CHECKING:
    from ..main import BaseModel


# these are types that are returned unchanged by deepcopy
IMMUTABLE_NON_COLLECTIONS_TYPES: set[type[Any]] = {
    int,
    float,
    complex,
    str,
    bool,
    bytes,
    type,
    NoneType,
    FunctionType,
    BuiltinFunctionType,
    LambdaType,
    weakref.ref,
    CodeType,
    # note: including ModuleType will differ from behaviour of deepcopy by not producing error.
    # It might be not a good idea in general, but considering that this function used only internally
    # against default values of fields, this will allow one to actually have a field with module as default value
    ModuleType,
    NotImplemented.__class__,
    Ellipsis.__class__,
}

# these are types that if empty, might be copied with simple copy() instead of deepcopy()
BUILTIN_COLLECTIONS: set[type[Any]] = {
    list,
    set,
    tuple,
    frozenset,
    dict,
    OrderedDict,
    defaultdict,
    deque,
}


def can_be_positional(param: Parameter) -> bool:
    """Return whether the parameter accepts a positional argument.

    ```python {test="skip" lint="skip"}
    def func(a, /, b, *, c):
        pass

    params = inspect.signature(func).parameters
    can_be_positional(params['a'])
    #> True
    can_be_positional(params['b'])
    #> True
    can_be_positional(params['c'])
    #> False
    ```
    """
    return param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)


def lenient_issubclass(cls: Any, class_or_tuple: Any) -> bool:  # pragma: no cover
    try:
        return isinstance(cls, type) and issubclass(cls, class_or_tuple)
    except TypeError:
        if isinstance(cls, _typing_extra.WithArgsTypes):
            return False
        raise  # pragma: no cover


def is_model_class(cls: Any) -> TypeGuard[type[BaseModel]]:
    """Returns true if cls is a _proper_ subclass of BaseModel, and provides proper type-checking,
    unlike raw calls to lenient_issubclass.
    """
    BaseModel = import_cached_base_model()

    return lenient_issubclass(cls, BaseModel) and cls is not BaseModel


def is_valid_identifier(identifier: str) -> bool:
    """Checks that a string is a valid identifier and not a Python keyword.
    :param identifier: The identifier to test.
    :return: True if the identifier is valid.
    """
    return identifier.isidentifier() and not keyword.iskeyword(identifier)


def update_not_none(mapping: dict[Any, Any], **update: Any) -> None:
    mapping.update({k: v for k, v in update.items() if v is not None})


T = TypeVar('T')


if TYPE_CHECKING:

    def LazyClassAttribute(name: str, get_value: Callable[[], T]) -> T: ...

else:

    class LazyClassAttribute:
        """A descriptor exposing an attribute only accessible on a class (hidden from instances).

        The attribute is lazily computed and cached during the first access.
        """

        def __init__(self, name: str, get_value: Callable[[], Any]) -> None:
            self.name = name
            self.get_value = get_value

        @cached_property
        def value(self) -> Any:
            return self.get_value()

        def __get__(self, instance: Any, owner: type[Any]) -> Any:
            if instance is None:
                return self.value
            raise AttributeError(f'{self.name!r} attribute of {owner.__name__!r} is class-only')


Obj = TypeVar('Obj')


def smart_deepcopy(obj: Obj) -> Obj:
    """Return type as is for immutable built-in types
    Use obj.copy() for built-in empty collections
    Use copy.deepcopy() for non-empty collections and unknown objects.
    """
    if obj is MISSING or obj is PydanticUndefined:
        return obj  # pyright: ignore[reportReturnType]
    obj_type = obj.__class__
    if obj_type in IMMUTABLE_NON_COLLECTIONS_TYPES:
        return obj  # fastest case: obj is immutable and not collection therefore will not be copied anyway
    try:
        if not obj and obj_type in BUILTIN_COLLECTIONS:
            # faster way for empty collections, no need to copy its members
            return obj if obj_type is tuple else obj.copy()  # tuple doesn't have copy method  # type: ignore
    except (TypeError, ValueError, RuntimeError):
        # do we really dare to catch ALL errors? Seems a bit risky
        pass

    return deepcopy(obj)  # slowest way when we actually might need a deepcopy


_SENTINEL = object()


def all_identical(left: Iterable[Any], right: Iterable[Any]) -> bool:
    """Check that the items of `left` are the same objects as those in `right`.

    >>> a, b = object(), object()
    >>> all_identical([a, b, a], [a, b, a])
    True
    >>> all_identical([a, b, [a]], [a, b, [a]])  # new list object, while "equal" is not "identical"
    False
    """
    for left_item, right_item in zip_longest(left, right, fillvalue=_SENTINEL):
        if left_item is not right_item:
            return False
    return True


def get_first_not_none(a: Any, b: Any) -> Any:
    """Return the first argument if it is not `None`, otherwise return the second argument."""
    return a if a is not None else b


@dataclasses.dataclass(frozen=True, slots=True)
class SafeGetItemProxy:
    """Wrapper redirecting `__getitem__` to `get` with a sentinel value as default

    This makes it safe to use in `operator.itemgetter` when some keys may be missing
    """

    wrapped: Mapping[str, Any]

    def __getitem__(self, key: str, /) -> Any:
        return self.wrapped.get(key, _SENTINEL)

    # required to pass the object to operator.itemgetter() instances due to a quirk of typeshed
    # https://github.com/python/mypy/issues/13713
    # https://github.com/python/typeshed/pull/8785
    # Since this is typing-only, hide it in a typing.TYPE_CHECKING block
    if TYPE_CHECKING:

        def __contains__(self, key: str, /) -> bool:
            return self.wrapped.__contains__(key)
