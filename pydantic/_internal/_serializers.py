from __future__ import annotations

import collections
import collections.abc
import typing
from typing import Any

from pydantic_core import PydanticOmit, core_schema

from ._typing_extra import is_namedtuple

SEQUENCE_ORIGIN_MAP: dict[Any, Any] = {
    typing.Deque: collections.deque,  # noqa: UP006
    collections.deque: collections.deque,
    list: list,
    typing.List: list,  # noqa: UP006
    tuple: tuple,
    typing.Tuple: tuple,  # noqa: UP006
    set: set,
    typing.AbstractSet: set,
    typing.Set: set,  # noqa: UP006
    frozenset: frozenset,
    typing.FrozenSet: frozenset,  # noqa: UP006
    typing.Sequence: list,
    typing.MutableSequence: list,
    typing.MutableSet: set,
    # this doesn't handle subclasses of these
    # parametrized typing.Set creates one of these
    collections.abc.MutableSet: set,
    collections.abc.Set: frozenset,
}


def _has_negative_int_keys(obj: Any) -> bool:
    """Check if a set, frozenset, or dict contains any negative integer keys."""
    items: Any = obj if isinstance(obj, (set, frozenset)) else obj.keys() if isinstance(obj, dict) else ()
    return any(isinstance(k, int) and k < 0 for k in items)


def _resolve_indices(obj: Any, length: int) -> set[int]:
    """Resolve an include/exclude set or dict keys to positive indices."""
    keys: Any = obj if isinstance(obj, (set, frozenset)) else obj.keys() if isinstance(obj, dict) else ()
    resolved: set[int] = set()
    for k in keys:
        if isinstance(k, int):
            resolved.add(k % length if k < 0 else k)
    return resolved


def serialize_sequence_via_list(
    v: Any, handler: core_schema.SerializerFunctionWrapHandler, info: core_schema.SerializationInfo
) -> Any:
    items: list[Any] = []

    value_type = type(v)
    mapped_origin = SEQUENCE_ORIGIN_MAP.get(value_type)
    if mapped_origin is None and not is_namedtuple(value_type):
        # we shouldn't hit this branch, should probably add a serialization error or something
        return v

    # pydantic-core's function-wrap handler doesn't know the sequence length,
    # so it can't resolve negative indices and raises ValueError.  When the
    # value is sized and include/exclude contain negative integers, resolve
    # them here and handle item-level filtering in Python.
    has_neg_exclude = info.exclude is not None and _has_negative_int_keys(info.exclude)
    has_neg_include = info.include is not None and _has_negative_int_keys(info.include)

    if (has_neg_exclude or has_neg_include) and hasattr(v, '__len__'):
        length = len(v)
        excl_set = _resolve_indices(info.exclude, length) if has_neg_exclude else set()
        incl_set = _resolve_indices(info.include, length) if has_neg_include else None

        # For set-style exclude with negative indices, skip excluded items
        # and remove fully-excluded entries from the set.  For dict-style
        # exclude (e.g. {-1: {'field'}}), only skip items whose value is
        # falsy (meaning "exclude the whole item").
        if has_neg_exclude and isinstance(info.exclude, dict):
            excl_set = set()
            for k, sub in info.exclude.items():
                if isinstance(k, int):
                    resolved_k = k % length if k < 0 else k
                    if not sub:
                        excl_set.add(resolved_k)

        for index, item in enumerate(v):
            if index in excl_set:
                continue
            if incl_set is not None and index not in incl_set:
                continue
            try:
                item_v = handler(item)
            except PydanticOmit:  # noqa: PERF203
                pass
            else:
                items.append(item_v)
    else:
        for index, item in enumerate(v):
            try:
                item_v = handler(item, index)
            except PydanticOmit:  # noqa: PERF203
                pass
            else:
                items.append(item_v)

    if info.mode_is_json():
        return items
    elif mapped_origin is not None:
        return mapped_origin(items)
    else:
        # named tuple: if some items were excluded, it can't be re-created
        return value_type(*items) if len(items) == len(v) else tuple(items)
