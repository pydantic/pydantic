"""Shared helpers for caching schemas of pure annotations."""

from __future__ import annotations

import datetime
import sys
import typing
from decimal import Decimal
from types import NoneType
from typing import Any

import typing_extensions
from pydantic_core import core_schema
from typing_extensions import get_args, get_origin  # noqa: UP035
from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin

# The leaf types of "pure" annotations (see `_pure_annotation_cache_key()`). These are immutable
# C types only, guaranteeing that no custom `__get_pydantic_core_schema__`/`__get_pydantic_json_schema__`
# hook can ever be attached to them.
#
# Note: membership of these collections is tested by identity (through `_ids()` below) and not with
# a plain `in`. A user-defined class whose metaclass implements `__eq__`/`__hash__` so that the
# class compares equal to e.g. `int` would otherwise be classified as pure and share `int`'s cache
# entry, letting its `__get_pydantic_core_schema__` hook poison the schema used for `int` fields
# (and vice versa):
_PURE_LEAF_TYPES: frozenset[Any] = frozenset(
    [
        str,
        bytes,
        int,
        float,
        bool,
        complex,
        None,
        NoneType,
        Any,
        typing_extensions.Any,
        object,
        # These classes are mutable on PyPy and may acquire custom schema hooks.
        *(
            [datetime.date, datetime.datetime, datetime.time, datetime.timedelta, Decimal]
            if sys.implementation.name == 'cpython'
            else []
        ),
        # The bare container forms (their schemas don't depend on configuration or context either):
        list,
        set,
        frozenset,
        dict,
        tuple,
    ]
)
_PURE_CONTAINER_ORIGINS: frozenset[Any] = frozenset([list, set, frozenset, dict, tuple])
_PURE_LITERAL_VALUE_TYPES: frozenset[type[Any]] = frozenset([str, bytes, int, bool, NoneType])


def _ids(objects: frozenset[Any], /) -> frozenset[int]:
    """The ids of the provided objects, for identity-based membership tests.

    The objects are all builtin/stdlib singletons kept alive for the lifetime of the process by the
    (module-global) sets above, so their ids are stable and can't be reused by another object.
    """
    return frozenset(id(obj) for obj in objects)


_PURE_LEAF_TYPE_IDS = _ids(_PURE_LEAF_TYPES)
_PURE_CONTAINER_ORIGIN_IDS = _ids(_PURE_CONTAINER_ORIGINS)
_PURE_LITERAL_VALUE_TYPE_IDS = _ids(_PURE_LITERAL_VALUE_TYPES)

# Returned by `_pure_annotation_cache_key()` for annotations that aren't cacheable. A dedicated sentinel
# is required as `None` is itself a valid (and pure) annotation, and so a valid cache key:
_NOT_PURE: Any = object()

# Bound the combined literal payload retained by each entry, including nested literals.
# Together with the entry cap, this limits cached literal payload to roughly 4 MiB,
# excluding the additional memory used by schema and key containers.
_PURE_ANNOTATION_MAX_LITERAL_BYTES = 8 * 1024


def _normalize_tuple_args(tuple_type: Any, args: tuple[Any, ...] | None) -> tuple[Any, ...] | None:
    """Return tuple element annotations, or `None` for a bare, arbitrary-length tuple.

    An empty tuple of arguments denotes a fixed-length empty tuple. On Python 3.10,
    `typing.Tuple[()]` instead supplies `((),)`, which is normalized to the same shape.
    """
    if not args:
        return None if tuple_type is tuple or tuple_type is typing.Tuple else ()  # noqa: UP006
    if len(args) == 1 and args[0] == ():
        return ()
    return args


def _pure_annotation_cache_key(tp: Any, literal_bytes: list[int] | None = None) -> Any:
    """Return a cache key for a pure annotation within the literal budget, `_NOT_PURE` otherwise.

    `literal_bytes` accumulates the combined literal payload across a recursive traversal.
    It is allocated only for compound annotations, keeping leaf lookups unchanged.

    An annotation is pure if it is composed only of immutable C leaf types and of typing
    constructs (unions, literals of primitive values, builtin containers) of pure annotations.
    The generated core schema for a pure annotation is guaranteed to be identical every time
    it is generated: no custom schema hooks can be involved, and the schema can't be affected
    by configuration (assuming no `json_encoders`, checked separately) or by generation context
    (namespaces, type variable maps, reference definitions). This makes it safe to cache.

    Note that the annotation objects themselves can't be used as cache keys: unions and literals
    compare (and hash) equal regardless of the order of their arguments, while their generated
    schemas are order-sensitive. The returned key is a nested tuple structure preserving order.

    The returned key only ever holds builtin/stdlib types and literal values of such types (both
    guaranteed by the identity-based membership tests), so it is always hashable. Callers still
    guard against `TypeError` in case an unhashable annotation reaches a `get_args()` call.
    """
    type_id = id(tp)
    if type_id in _PURE_LEAF_TYPE_IDS:
        return tp
    # Match schema dispatch's normalization of bare deprecated aliases, preserving
    # the distinction between `typing.Tuple` (arbitrary length) and `Tuple[()]`.
    if aliased_type := typing_objects.DEPRECATED_ALIASES_IDS.get(type_id):
        return aliased_type if id(aliased_type) in _PURE_LEAF_TYPE_IDS else _NOT_PURE
    origin = get_origin(tp)
    if origin is None:
        return _NOT_PURE
    if is_union_origin(origin):
        arg_keys: list[Any] = ['union']
    elif id(origin) in _PURE_CONTAINER_ORIGIN_IDS:
        arg_keys = [origin]
    elif typing_objects.is_literal(origin):
        arg_keys = ['literal']
        size = literal_bytes[0] if literal_bytes is not None else 0
        for arg in get_args(tp):
            if id(type(arg)) not in _PURE_LITERAL_VALUE_TYPE_IDS:
                return _NOT_PURE
            value_size = sys.getsizeof(arg, 0)
            if not value_size:
                # PyPy cannot report object sizes. Use conservative estimates there,
                # accounting for wide Unicode strings and arbitrary-precision integers.
                if isinstance(arg, (str, bytes)):
                    value_size = 80 + len(arg) * (4 if isinstance(arg, str) else 1)
                elif isinstance(arg, int):
                    value_size = 32 + 4 * ((arg.bit_length() + 29) // 30)
                else:
                    value_size = 32
            size += value_size
            if size > _PURE_ANNOTATION_MAX_LITERAL_BYTES:
                return _NOT_PURE
            # The type is included to discriminate between equal values of different
            # types (e.g. `Literal[1]` and `Literal[True]`):
            arg_keys.append((type(arg), arg))
        if literal_bytes is not None:
            literal_bytes[0] = size
        return tuple(arg_keys)
    else:
        return _NOT_PURE

    args = get_args(tp)
    if origin is tuple:
        args = _normalize_tuple_args(tp, args)
        if args is None:
            return tuple
    if literal_bytes is None:
        literal_bytes = [0]
    for arg in args:
        if arg is Ellipsis:
            arg_keys.append(Ellipsis)
            continue
        arg_key = _pure_annotation_cache_key(arg, literal_bytes)
        if arg_key is _NOT_PURE:
            return _NOT_PURE
        arg_keys.append(arg_key)
    return tuple(arg_keys)


def _copy_pure_schema(schema: Any) -> Any:
    """Copy a core schema generated from a pure annotation.

    Only containers are copied; all other values appearing in such a schema are immutable.
    """
    if isinstance(schema, dict):
        return {k: _copy_pure_schema(v) for k, v in schema.items()}
    if isinstance(schema, list):
        return [_copy_pure_schema(v) for v in schema]
    if isinstance(schema, tuple):
        return tuple(_copy_pure_schema(v) for v in schema)
    return schema


# A process-wide cache of the core schemas generated for pure field annotations, keyed by
# `_pure_annotation_cache_key()` keys. Values are the pristine generated schemas — they are
# never handed out directly, only `_copy_pure_schema()` copies of them are. Keys only ever
# hold builtin types and size-limited literal values, and can't keep user classes alive:
_pure_annotation_schema_cache: dict[Any, core_schema.CoreSchema] = {}

# The number of entries above which `_pure_annotation_schema_cache` is reset. The set of pure
# annotations is unbounded (`Literal[...]` in particular can hold arbitrary values), so a process
# building models from dynamically generated schemas would otherwise grow the cache forever.
# Real-world libraries stay far below this limit — measured over a whole import, the Google GenAI
# SDK (766 models) uses 118 entries and the MCP Python SDK (643 models) 139 — so the reset only
# ever trips for workloads that wouldn't benefit from the cached entries anyway:
_PURE_ANNOTATION_CACHE_SIZE = 512
