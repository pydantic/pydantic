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


@cache
def _trusted_class_hooks() -> dict[type[Any], tuple[Any, Any, Any]]:
    """Trusted leaf classes, mapped to a snapshot of their (normalized) schema hooks.

    These are stdlib value classes (with no schema hooks) and pydantic's own URL classes (whose
    `__get_pydantic_core_schema__` output is deterministic per class and context-free — no
    references, no configuration reads). As these are regular Python classes, hooks *could* be
    monkeypatched onto (or off of) them at runtime, so `_verified_leaf_class_key()` re-verifies
    the snapshot on every use: any difference makes the class uncacheable from that point on.
    """
    from fractions import Fraction
    from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
    from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath
    from uuid import UUID

    from ..networks import AnyHttpUrl, AnyUrl, AnyWebsocketUrl, FileUrl, FtpUrl, HttpUrl, WebsocketUrl

    return {
        cls: (
            _normalize_hook(getattr(cls, '__get_pydantic_core_schema__', None)),
            _normalize_hook(getattr(cls, '__get_pydantic_json_schema__', None)),
            _normalize_hook(getattr(cls, '__modify_schema__', None)),
        )
        for cls in (
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
            AnyUrl,
            AnyHttpUrl,
            HttpUrl,
            AnyWebsocketUrl,
            WebsocketUrl,
            FileUrl,
            FtpUrl,
        )
    }


def _normalize_hook(hook: Any) -> Any:
    """Normalize a schema hook for identity comparison (bound classmethods are recreated on each access)."""
    return getattr(hook, '__func__', hook)


def _verified_leaf_class_key(tp: Any) -> Any | None:
    """Return `tp` as a cache key if it is a trusted leaf class with unchanged hooks, else `None`."""
    hooks = _trusted_class_hooks().get(tp)
    if hooks is None:
        return None
    if (
        _normalize_hook(getattr(tp, '__get_pydantic_core_schema__', None)) is hooks[0]
        and _normalize_hook(getattr(tp, '__get_pydantic_json_schema__', None)) is hooks[1]
        and _normalize_hook(getattr(tp, '__modify_schema__', None)) is hooks[2]
    ):
        return tp
    return None


def pure_annotation_cache_key(tp: Any, /) -> Any | None:
    """Return a cache key for the annotation if it is pure, `None` otherwise.

    Note that the annotation objects themselves can't be used as cache keys: unions and literals
    compare (and hash) equal regardless of the order of their arguments, while the results derived
    from them (core schemas, `FieldInfo` instances) are order-sensitive (and `Annotated` forms
    holding `Field()` metadata aren't even hashable). The returned key is a nested tuple structure
    preserving order.

    May raise `TypeError` if the annotation (or a part of it) is unhashable.
    """
    origin = get_origin(tp)
    if origin is None:
        if tp in _PURE_LEAF_TYPES:
            return tp
        if isinstance(tp, type):
            return _verified_leaf_class_key(tp)
        return None
    if typing_objects.is_annotated(origin):
        source_key = pure_annotation_cache_key(tp.__origin__)
        if source_key is None:
            return None
        arg_keys: list[Any] = ['annotated', source_key]
        for item in tp.__metadata__:
            item_key = encode_metadata_item(item)
            if item_key is None:
                return None
            arg_keys.append(item_key)
        return tuple(arg_keys)
    if is_union_origin(origin):
        arg_keys = ['union']
    elif origin in _PURE_CONTAINER_ORIGINS:
        arg_keys = [origin]
    elif typing_objects.is_literal(origin):
        arg_keys = ['literal']
        for arg in get_args(tp):
            if type(arg) not in _PURE_LITERAL_VALUE_TYPES:
                return None
            # The type is included to discriminate between equal values of different
            # types (e.g. `Literal[1]` and `Literal[True]`):
            arg_keys.append((type(arg), arg))
        return tuple(arg_keys)
    else:
        return None

    for arg in get_args(tp):
        if arg is Ellipsis:
            arg_keys.append(Ellipsis)
            continue
        arg_key = pure_annotation_cache_key(arg)
        if arg_key is None:
            return None
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
        pure = pure_annotation_cache_key(tp) is not None
    except TypeError:  # unhashable annotation (or part of it)
        return False
    if pure:
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
