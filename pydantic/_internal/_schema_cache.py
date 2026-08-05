"""Process-wide caches for the work performed when building model classes.

The caches in this module all revolve around the same observation: the exact same field
definition (annotation, and possibly a simple default) is typically repeated across many
fields and models of a codebase, and the work performed for it — evaluating the annotation,
building a `FieldInfo`, generating the core schema — produces an identical result every time,
as long as nothing model- or context-specific is involved.

The key notion is that of a *pure* annotation (see `pure_annotation_cache_key()`): an
annotation composed only of immutable C leaf types and of typing constructs (unions, literals
of primitive values, builtin containers) of pure annotations. For these:

- no custom `__get_pydantic_core_schema__`/`__get_pydantic_json_schema__` hook can ever be
  involved (the leaf types are immutable C types, and generic aliases don't proxy dunder
  attribute access to their origin),
- no generation context (forward reference namespaces, type variable maps, reference
  definitions) can affect any derived result,
- no configuration read during schema generation can affect the generated schema, with the
  exception of the deprecated `json_encoders` setting (callers are expected to check it).

Caches never hand out their stored values directly: consumers receive copies, so the derived
objects (`FieldInfo` instances, core schemas) of different models never share mutable state.
Cache keys hold only builtin types and typing constructs over them, so entries are small and
can never keep user classes alive.
"""

from __future__ import annotations

import datetime
import typing
from decimal import Decimal
from functools import cache
from types import NoneType
from typing import Any

import typing_extensions
from typing_extensions import get_args, get_origin  # noqa: UP035 (`typing`'s versions don't handle all cases)
from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin

if typing.TYPE_CHECKING:
    from pydantic_core import core_schema

    from ..fields import FieldInfo

# The leaf types of pure annotations. These are immutable C types only, guaranteeing that no
# custom `__get_pydantic_core_schema__`/`__get_pydantic_json_schema__` hook can ever be
# attached to them:
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
        datetime.date,
        datetime.datetime,
        datetime.time,
        datetime.timedelta,
        Decimal,
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

# The types of default values that can take part in cache keys. Immutable builtin types only —
# and no `float`, as e.g. `0.0` and `-0.0` are equal (and hash equal) yet visibly different:
IMMUTABLE_DEFAULT_TYPES: frozenset[type[Any]] = frozenset([NoneType, bool, int, str, bytes])


def _ids(objects: frozenset[Any], /) -> frozenset[int]:
    """The ids of the provided objects, for identity-based membership tests.

    Membership of the sets above is tested by identity and not with a plain `in`: a user-defined
    class whose metaclass implements `__eq__`/`__hash__` so that the class compares equal to e.g.
    `int` would otherwise be classified as pure and share `int`'s cache entries, letting its
    `__get_pydantic_core_schema__` hook poison the schema used for `int` fields (and vice versa).

    The objects are all builtin/stdlib singletons kept alive for the lifetime of the process by the
    (module-global) sets above, so their ids are stable and can't be reused by another object.
    """
    return frozenset(id(obj) for obj in objects)


_PURE_LEAF_TYPE_IDS = _ids(_PURE_LEAF_TYPES)
_PURE_CONTAINER_ORIGIN_IDS = _ids(_PURE_CONTAINER_ORIGINS)
_PURE_LITERAL_VALUE_TYPE_IDS = _ids(_PURE_LITERAL_VALUE_TYPES)
IMMUTABLE_DEFAULT_TYPE_IDS = _ids(IMMUTABLE_DEFAULT_TYPES)

# Returned by `pure_annotation_cache_key()` for annotations that aren't pure. A dedicated sentinel
# is required as `None` is itself a valid (and pure) annotation, and so a valid cache key:
NOT_PURE: Any = object()

# The number of entries above which the caches in this module are reset (see `store()`):
CACHE_SIZE_LIMIT = 512


# The value types allowed to appear in encoded metadata (constraint values, `Field()` attribute
# values). Immutable builtins only; floats are encoded together with their `repr()` (see
# `_encode_metadata_value()`):
_ENCODABLE_METADATA_VALUE_TYPES: frozenset[type[Any]] = frozenset([NoneType, bool, int, str, bytes, float])


@cache
def _encodable_constraint_types() -> frozenset[type[Any]]:
    """The `annotated_types` constraint classes that can take part in cache keys.

    These are frozen dataclasses holding a single value, compared and hashed by value.
    Imported lazily, as `annotated_types` is not imported at `pydantic` import time.
    """
    import annotated_types

    return frozenset(
        [
            annotated_types.Gt,
            annotated_types.Ge,
            annotated_types.Lt,
            annotated_types.Le,
            annotated_types.MultipleOf,
            annotated_types.MinLen,
            annotated_types.MaxLen,
        ]
    )


def _encode_metadata_value(value: Any) -> Any | None:
    """Encode a metadata value for use in a cache key, or return `None` if not encodable.

    The value type is included to discriminate equal values of different types (`1` vs `True`),
    and floats additionally include their `repr()` (`0.0` and `-0.0` are equal yet distinct).
    """
    value_type = type(value)
    if value_type not in _ENCODABLE_METADATA_VALUE_TYPES:
        return None
    if value_type is float:
        return (float, repr(value), value)
    return (value_type, value)


def encode_metadata_item(item: Any, /) -> Any | None:
    """Encode a single annotation metadata item for use in a cache key, or `None` if not encodable.

    Supported items are the single-value `annotated_types` constraints (`Gt(0)`, `MaxLen(10)`, …)
    and plain `Field()` functions (`FieldInfo` instances — not subclasses) whose explicitly set
    attributes (and collected constraints) are all encodable values. Such items are fully
    described by their values: the state they contribute to a `FieldInfo` (and to the generated
    schema) is identical for equal encodings, and no object sharing can result from reusing a
    cached result, as the items themselves don't end up in the derived objects.
    """
    item_type = type(item)
    if item_type in _encodable_constraint_types():
        import dataclasses

        encoded_values: list[Any] = [item_type]
        for field in dataclasses.fields(item):
            encoded = _encode_metadata_value(getattr(item, field.name))
            if encoded is None:
                return None
            encoded_values.append(encoded)
        return tuple(encoded_values)

    FieldInfo = _import_cached_field_info()
    if item_type is FieldInfo:
        encoded_attrs: list[Any] = []
        for attr, value in item._attributes_set.items():
            encoded = _encode_metadata_value(value)
            if encoded is None:
                return None
            encoded_attrs.append((attr, encoded))
        encoded_metadata: list[Any] = ['fieldinfo', tuple(encoded_attrs)]
        for sub_item in item.metadata:
            encoded = encode_metadata_item(sub_item)
            if encoded is None:
                return None
            encoded_metadata.append(encoded)
        return tuple(encoded_metadata)

    return None


@cache
def _import_cached_field_info() -> type[Any]:
    from ..fields import FieldInfo

    return FieldInfo


# Holds the strong references that keep the `_trusted_leaf_hooks()` ids below valid:
_trusted_leaf_classes: list[type[Any]] = []


@cache
def _trusted_leaf_hooks() -> dict[int, tuple[Any, Any, Any]]:
    """Trusted leaf classes (by `id()`), mapped to the schema hooks they are *expected* to carry.

    These are stdlib value classes, which carry no schema hook at all, and pydantic's own URL
    classes, whose `__get_pydantic_core_schema__` output is deterministic per class and context-free
    (no references, no configuration reads).

    As these are regular Python classes, hooks could be monkeypatched onto (or off of) them at
    runtime, which invalidates the reasoning above, so `_verified_leaf_class_key()` checks the
    expected hooks on every use. Note that the expectation is pinned to `None` and to pydantic's own
    function objects (looked up on the class *defining* them) rather than snapshotted from whatever
    happens to be present on first use: a hook monkeypatched before the first model is built would
    otherwise be absorbed into the baseline and trusted from then on.
    """
    from fractions import Fraction
    from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
    from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath
    from uuid import UUID

    from ..networks import AnyHttpUrl, AnyUrl, AnyWebsocketUrl, FileUrl, FtpUrl, HttpUrl, WebsocketUrl, _BaseUrl

    hook_free_classes: tuple[type[Any], ...] = (
        UUID,
        Fraction,
        IPv4Address,
        IPv4Interface,
        IPv4Network,
        IPv6Address,
        IPv6Interface,
        IPv6Network,
        Path,
        PosixPath,
        PurePath,
        PurePosixPath,
        PureWindowsPath,
        WindowsPath,
    )
    url_classes: tuple[type[Any], ...] = (
        AnyUrl,
        AnyHttpUrl,
        HttpUrl,
        AnyWebsocketUrl,
        WebsocketUrl,
        FileUrl,
        FtpUrl,
    )
    # All the URL classes above inherit both hooks from `_BaseUrl`:
    url_hooks = (
        _normalize_hook(_BaseUrl.__dict__['__get_pydantic_core_schema__']),
        _normalize_hook(_BaseUrl.__dict__['__get_pydantic_json_schema__']),
        None,
    )

    _trusted_leaf_classes.extend(hook_free_classes)
    _trusted_leaf_classes.extend(url_classes)
    return {
        **{id(cls): (None, None, None) for cls in hook_free_classes},
        **{id(cls): url_hooks for cls in url_classes},
    }


def _normalize_hook(hook: Any) -> Any:
    """Normalize a schema hook for identity comparison (bound classmethods are recreated on each access)."""
    return getattr(hook, '__func__', hook)


def _encode_url_constraints(constraints: Any) -> Any:
    """Encode a `UrlConstraints` instance for use in a cache key, or `NOT_PURE` if not encodable."""
    encoded: list[Any] = []
    for name, value in sorted(constraints.defined_constraints.items()):
        if type(value) is list:  # e.g. `allowed_schemes`
            items = [_encode_metadata_value(item) for item in value]
            if any(item is None for item in items):
                return NOT_PURE
            encoded.append((name, tuple(items)))
        else:
            item = _encode_metadata_value(value)
            if item is None:
                return NOT_PURE
            encoded.append((name, item))
    return tuple(encoded)


def _verified_leaf_class_key(tp: Any) -> Any:
    """Return a cache key for `tp` if it is a trusted leaf class, `NOT_PURE` otherwise."""
    expected = _trusted_leaf_hooks().get(id(tp))
    if expected is None:
        return NOT_PURE
    core_hook, json_hook, modify_hook = expected
    if (
        _normalize_hook(getattr(tp, '__get_pydantic_core_schema__', None)) is not core_hook
        or _normalize_hook(getattr(tp, '__get_pydantic_json_schema__', None)) is not json_hook
        or _normalize_hook(getattr(tp, '__modify_schema__', None)) is not modify_hook
    ):
        return NOT_PURE
    if core_hook is None:
        # A hook-free stdlib value class: nothing about it can influence the generated schema.
        return tp
    # Pydantic's URL hook reads two mutable class attributes — `cls._constraints` (whose
    # `UrlConstraints` instance can also be mutated in place) and `cls.serialize_url` — so they
    # take part in the key rather than being assumed constant:
    constraints_key = _encode_url_constraints(tp._constraints)
    if constraints_key is NOT_PURE:
        return NOT_PURE
    return ('url-class', tp, constraints_key, _normalize_hook(tp.serialize_url))


def pure_annotation_cache_key(tp: Any, /) -> Any:
    """Return a cache key for the annotation if it is pure, `NOT_PURE` otherwise.

    Note that the annotation objects themselves can't be used as cache keys: unions and literals
    compare (and hash) equal regardless of the order of their arguments, while the results derived
    from them (core schemas, `FieldInfo` instances) are order-sensitive (and `Annotated` forms
    holding `Field()` metadata aren't even hashable). The returned key is a nested tuple structure
    preserving order.

    The returned key only ever holds builtin/stdlib types, trusted leaf classes and encoded values
    of such types, so it is always hashable. Callers still guard against `TypeError` in case an
    unhashable annotation reaches a `get_args()` call.
    """
    origin = get_origin(tp)
    if origin is None:
        if id(tp) in _PURE_LEAF_TYPE_IDS:
            return tp
        if isinstance(tp, type):
            return _verified_leaf_class_key(tp)
        return NOT_PURE
    if typing_objects.is_annotated(origin):
        source_key = pure_annotation_cache_key(tp.__origin__)
        if source_key is NOT_PURE:
            return NOT_PURE
        arg_keys: list[Any] = ['annotated', source_key]
        for item in tp.__metadata__:
            item_key = encode_metadata_item(item)
            if item_key is None:
                return NOT_PURE
            arg_keys.append(item_key)
        return tuple(arg_keys)
    if is_union_origin(origin):
        arg_keys = ['union']
    elif id(origin) in _PURE_CONTAINER_ORIGIN_IDS:
        arg_keys = [origin]
    elif typing_objects.is_literal(origin):
        arg_keys = ['literal']
        for arg in get_args(tp):
            if id(type(arg)) not in _PURE_LITERAL_VALUE_TYPE_IDS:
                return NOT_PURE
            # The type is included to discriminate between equal values of different
            # types (e.g. `Literal[1]` and `Literal[True]`):
            arg_keys.append((type(arg), arg))
        return tuple(arg_keys)
    else:
        return NOT_PURE

    for arg in get_args(tp):
        if arg is Ellipsis:
            arg_keys.append(Ellipsis)
            continue
        arg_key = pure_annotation_cache_key(arg)
        if arg_key is NOT_PURE:
            return NOT_PURE
        arg_keys.append(arg_key)
    return tuple(arg_keys)


# Pure annotations already seen, used by `is_pure_annotation()` to avoid rewalking the same
# annotation. Only pure annotations are remembered (a set lookup collapses equal annotation
# objects), as impure ones both fail fast when walked and could keep user classes alive:
_pure_annotations_seen: set[Any] = set()


def is_pure_annotation(tp: Any, /) -> bool:
    """Return whether the annotation is pure, memoizing positive results.

    A pure annotation is — among the other properties described in the module docstring —
    guaranteed to be fully evaluated: it can't contain strings or `typing.ForwardRef` instances.
    """
    try:
        if tp in _pure_annotations_seen:
            return True
        pure = pure_annotation_cache_key(tp) is not NOT_PURE
    except TypeError:  # unhashable annotation (or part of it)
        return False
    if pure:
        if len(_pure_annotations_seen) >= CACHE_SIZE_LIMIT:
            _pure_annotations_seen.clear()
        _pure_annotations_seen.add(tp)
    return pure


def copy_pure_schema(schema: Any, /) -> Any:
    """Copy a core schema generated from a pure annotation.

    Only containers are copied; all other values appearing in such a schema are immutable.
    """
    if isinstance(schema, dict):
        return {k: copy_pure_schema(v) for k, v in schema.items()}
    if isinstance(schema, list):
        return [copy_pure_schema(v) for v in schema]
    if isinstance(schema, tuple):
        return tuple(copy_pure_schema(v) for v in schema)
    return schema


# The core schemas generated for pure field annotations with no metadata to apply, keyed by
# `pure_annotation_cache_key()` keys (see `GenerateSchema._apply_annotations()`):
pure_annotation_schema_cache: dict[Any, core_schema.CoreSchema] = {}

# `FieldInfo` templates for fields with a pure annotation and no (or an immutable) assigned
# default, keyed by `(annotation key, type of default, default)` (see
# `collect_model_fields()`). Stored templates are pristine — consumers receive `_copy()`s:
field_info_template_cache: dict[Any, FieldInfo] = {}

# Complete `model-field` core schema nodes (inner schema, default wrapper and all), keyed by
# `(annotation key, type of default, default)` (see `GenerateSchema._generate_md_field_schema()`):
model_field_schema_cache: dict[Any, core_schema.ModelField] = {}


def store(cache: dict[Any, Any], key: Any, value: Any, /) -> None:
    """Store an entry in one of the caches above, keeping it bounded.

    The set of pure annotations is unbounded in principle (`Literal[...]` can hold arbitrary
    values, and metadata and default values take part in some of the keys), so a process building
    models from dynamically generated schemas would otherwise grow these caches forever. Real-world
    libraries stay far below the limit — measured over a whole import, the Google GenAI SDK
    (766 models) produces 118 distinct pure annotations and the MCP Python SDK (643 models) 139 —
    so the reset only ever trips for workloads that wouldn't benefit from the retained entries
    anyway.

    Clearing wholesale (rather than evicting individual entries) keeps this to a single atomic
    `dict` operation, so no locking is required on free-threaded builds.
    """
    if len(cache) >= CACHE_SIZE_LIMIT:
        cache.clear()
    cache[key] = value
