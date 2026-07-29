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


def pure_annotation_cache_key(tp: Any, /) -> Any | None:
    """Return a cache key for the annotation if it is pure, `None` otherwise.

    Note that the annotation objects themselves can't be used as cache keys: unions and literals
    compare (and hash) equal regardless of the order of their arguments, while the results derived
    from them (core schemas, `FieldInfo` instances) are order-sensitive. The returned key is a
    nested tuple structure preserving order.

    May raise `TypeError` if the annotation (or a part of it) is unhashable.
    """
    if tp in _PURE_LEAF_TYPES:
        return tp
    origin = get_origin(tp)
    if origin is None:
        return None
    if is_union_origin(origin):
        arg_keys: list[Any] = ['union']
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
