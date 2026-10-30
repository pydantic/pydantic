"""A checking mode for the schema caches, entirely in the test suite.

With `PYDANTIC_VERIFY_SCHEMA_CACHE=1`, every field schema built during the run is also built
a second time with the caches emptied, and the two are compared structurally. A whole suite
run then reports how many fields were checked and how many differed, which is the evidence a
reviewer of a cache wants and which a handful of unit tests cannot give.

Doing it here rather than in `pydantic/` keeps roughly 120 lines of comparison machinery out
of the shipped diff, and needs nothing from the library: emptying the cache dicts in place is
enough to force the long way round.
"""

from __future__ import annotations

import contextlib
import functools
import os
from collections.abc import Iterator
from typing import Any

from pydantic._internal import _schema_cache
from pydantic._internal._generate_schema import GenerateSchema

ENABLED = bool(os.environ.get('PYDANTIC_VERIFY_SCHEMA_CACHE'))

_CACHE_NAMES = (
    'pure_annotation_schema_cache',
    'field_info_template_cache',
    'model_field_schema_cache',
)

counts = {'checked': 0, 'differed': 0}
differences: list[str] = []


@contextlib.contextmanager
def _caches_emptied() -> Iterator[None]:
    """Empty every cache in place for the duration, then put the entries back.

    In place, because the library binds these dicts under other names at import time;
    rebinding the module attribute would leave those pointing at the originals.
    """
    saved = {name: dict(getattr(_schema_cache, name)) for name in _CACHE_NAMES}
    seen = set(_schema_cache._pure_annotations_seen)
    for name in _CACHE_NAMES:
        getattr(_schema_cache, name).clear()
    _schema_cache._pure_annotations_seen.clear()
    try:
        yield
    finally:
        for name in _CACHE_NAMES:
            cache = getattr(_schema_cache, name)
            cache.clear()
            cache.update(saved[name])
        _schema_cache._pure_annotations_seen.clear()
        _schema_cache._pure_annotations_seen.update(seen)


def describe_difference(cached: Any, fresh: Any, path: str = '') -> str | None:
    """Where a cached result differs from the same thing built again, or `None`.

    Functions are compared by code object, because each build makes its own closures and two
    from the same `def` share one. A callable with no code object (`operator.attrgetter` and
    friends define neither that nor `__eq__`) is compared by repr, which carries what it was
    built from - without this it reports a difference between two identical ones.
    """
    if type(cached) is not type(fresh):
        return f'{path or "<root>"}: type {type(cached).__name__} != {type(fresh).__name__}'
    if isinstance(cached, dict):
        if cached.keys() != fresh.keys():
            return (
                f'{path or "<root>"}: keys differ, cached-only={sorted(set(cached) - set(fresh))} '
                f'fresh-only={sorted(set(fresh) - set(cached))}'
            )
        for key in cached:
            difference = describe_difference(cached[key], fresh[key], f'{path}.{key}')
            if difference is not None:
                return difference
        return None
    if isinstance(cached, (list, tuple)):
        if len(cached) != len(fresh):
            return f'{path or "<root>"}: length {len(cached)} != {len(fresh)}'
        for index, (left, right) in enumerate(zip(cached, fresh)):
            difference = describe_difference(left, right, f'{path}[{index}]')
            if difference is not None:
                return difference
        return None
    if isinstance(cached, functools.partial):
        # a partial's repr carries the address of whatever it wraps, and each build makes its
        # own closures, so compare what it is made of rather than how it prints
        for attribute in ('func', 'args', 'keywords'):
            difference = describe_difference(
                getattr(cached, attribute), getattr(fresh, attribute), f'{path}.{attribute}'
            )
            if difference is not None:
                return difference
        return None
    if callable(cached):
        if hasattr(cached, '__code__'):
            if cached.__code__ is not getattr(fresh, '__code__', None):
                return f'{path}: different function {cached!r} != {fresh!r}'
            return None
        if repr(cached) != repr(fresh):
            return f'{path}: different callable {cached!r} != {fresh!r}'
        return None
    try:
        if cached != fresh:
            return f'{path}: {cached!r} != {fresh!r}'
    except Exception:  # noqa: BLE001 - a value whose __eq__ raises is not evidence of a bug
        pass
    return None


def install() -> None:
    """Wrap field schema generation so every result is checked against an uncached one."""
    original = GenerateSchema._generate_md_field_schema
    checking = False

    def checked(self, name, field_info, decorators):  # noqa: ANN001, ANN202
        nonlocal checking
        cached = original(self, name, field_info, decorators)
        if checking:
            return cached
        checking = True
        try:
            with _caches_emptied():
                fresh = original(self, name, field_info, decorators)
        finally:
            checking = False
        counts['checked'] += 1
        difference = describe_difference(cached, fresh)
        if difference is not None:
            counts['differed'] += 1
            if len(differences) < 20:
                differences.append(f'{field_info.annotation!r}: {difference}')
        return cached

    GenerateSchema._generate_md_field_schema = checked


def report() -> str:
    lines = [
        f'schema caches: {counts["checked"]:,} field schemas checked against an uncached '
        f'build, {counts["differed"]:,} differed'
    ]
    lines.extend(f'  {difference}' for difference in differences)
    return '\n'.join(lines)
