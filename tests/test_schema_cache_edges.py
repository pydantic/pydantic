"""Edge cases for the pure-annotation schema caches.

These sit alongside the cache tests already in `tests/test_internal.py`. Each one covers
something the caches rely on that nothing else in the suite pins down, and several of them
are about what happens *after* the cache has been populated, which is the direction that is
easy to get wrong.
"""

from typing import Tuple  # noqa: UP035

import pytest

from pydantic import BaseModel, ValidationError
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
