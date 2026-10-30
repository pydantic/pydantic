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


def serialize_sequence_via_list(
    v: Any, handler: core_schema.SerializerFunctionWrapHandler, info: core_schema.SerializationInfo
) -> Any:
    items: list[Any] = []

    value_type = type(v)
    mapped_origin = SEQUENCE_ORIGIN_MAP.get(value_type)
    if mapped_origin is None and not is_namedtuple(value_type):
        # we shouldn't hit this branch, should probably add a serialization error or something
        return v

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
