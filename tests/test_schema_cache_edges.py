"""Edge cases for the pure-annotation schema caches.

These sit alongside the cache tests already in `tests/test_internal.py`. Each one covers
something the caches rely on that nothing else in the suite pins down, and several of them
are about what happens *after* the cache has been populated, which is the direction that is
easy to get wrong.
"""

import gc
import sys
from typing import Any, Literal, Tuple  # noqa: UP035

import pytest

from pydantic import BaseModel, Field, ValidationError, create_model
from pydantic._internal import _schema_cache


def _clear_caches() -> None:
    for cache in (
        _schema_cache.pure_annotation_schema_cache,
        _schema_cache.field_info_template_cache,
        _schema_cache.model_field_schema_cache,
        _schema_cache._pure_annotations_seen,
    ):
        cache.clear()


@pytest.fixture(autouse=True)
def _empty_caches():
    """Start and finish empty, so one test is never served another's entries."""
    _clear_caches()
    yield
    _clear_caches()


@pytest.mark.parametrize('empty_first', [False, True], ids=['variadic-first', 'empty-first'])
def test_unparameterized_tuple_is_not_the_empty_tuple(empty_first: bool) -> None:
    """`Tuple` is a variadic tuple; `Tuple[()]` is the empty one, and both have no arguments."""

    class Empty(BaseModel):
        value: Tuple[()]  # noqa: UP006

    class Variadic(BaseModel):
        value: Tuple  # noqa: UP006

    for model in (Empty, Variadic) if empty_first else (Variadic, Empty):
        model.model_rebuild(force=True)

    assert Variadic(value=(1, 2, 3)).value == (1, 2, 3)
    assert Empty(value=()).value == ()
    with pytest.raises(ValidationError):
        Empty(value=(1, 2, 3))


def _retained_bytes() -> int:
    """Total size of the large values reachable from the caches' keys."""
    seen: set[int] = set()
    total = 0

    def walk(obj: object) -> None:
        nonlocal total
        if id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj, (str, bytes, int)) and not isinstance(obj, bool):
            total += sys.getsizeof(obj)
        elif isinstance(obj, (tuple, list, set, frozenset)):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                walk(key)
                walk(value)

    for cache in (
        _schema_cache.pure_annotation_schema_cache,
        _schema_cache.field_info_template_cache,
        _schema_cache.model_field_schema_cache,
    ):
        walk(list(cache.keys()))
    walk(list(_schema_cache._pure_annotations_seen))
    return total


HUGE_STRING = 'x' * 1_000_000
HUGE_INT = 10**1_000_000


@pytest.mark.parametrize(
    ('label', 'make'),
    [
        ('literal', lambda i: create_model(f'L{i}', value=(Literal[HUGE_STRING + str(i)], ...))),
        ('str default', lambda i: create_model(f'S{i}', value=(str, HUGE_STRING + str(i)))),
        ('int default', lambda i: create_model(f'I{i}', value=(int, HUGE_INT + i))),
        (
            'description',
            lambda i: create_model(f'D{i}', value=(str, Field(default='x', description=HUGE_STRING + str(i)))),
        ),
    ],
)
def test_large_values_are_not_retained_by_the_caches(label: str, make: Any) -> None:
    """The entry-count limit bounds how many entries there are, not how large they are.

    A key holds its values until the cache is reset, so a value of unbounded size in a key
    means unbounded retention. Values this large are unique to their field and would never
    have been reused anyway.
    """
    for index in range(8):
        make(index)
    gc.collect()
    assert _retained_bytes() < 1_000_000, f'{label}: the caches retained large values'
