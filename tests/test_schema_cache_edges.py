"""Edge cases for the pure-annotation schema caches.

These sit alongside the cache tests already in `tests/test_internal.py`. Each one covers
something the caches rely on that nothing else in the suite pins down, and several of them
are about what happens *after* the cache has been populated, which is the direction that is
easy to get wrong.
"""

import datetime
import gc
import sys
from decimal import Decimal
from enum import Enum
from typing import Any, Literal, Tuple  # noqa: UP035
from uuid import UUID

import pytest
from pydantic_core import core_schema

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, ValidationError, create_model
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


PURE_TYPES: dict[str, Any] = {
    'str': str,
    'bytes': bytes,
    'int': int,
    'float': float,
    'bool': bool,
    'Decimal': Decimal,
    'date': datetime.date,
    'datetime': datetime.datetime,
    'timedelta': datetime.timedelta,
    'list[str]': list[str],
    'str | None': str | None,
}

# Settings that could plausibly reach the schema of one of the types above rather than only
# the model's core config. `json_encoders` is excluded: the cache is bypassed for it.
CONFIG_SETTINGS: dict[str, tuple[Any, Any]] = {
    'allow_inf_nan': (True, False),
    'ser_json_bytes': ('utf8', 'base64'),
    'val_json_bytes': ('utf8', 'base64'),
    'ser_json_timedelta': ('iso8601', 'float'),
    'coerce_numbers_to_str': (False, True),
    'str_strip_whitespace': (False, True),
    'str_max_length': (None, 10),
    'strict': (False, True),
    'extra': ('ignore', 'allow'),
}


def _field_schema(annotation: Any, setting: str, value: Any) -> Any:
    model = type(
        'M',
        (BaseModel,),
        {'__annotations__': {'value': annotation}, 'model_config': ConfigDict(**{setting: value})},
    )
    return model.__pydantic_core_schema__['schema']['fields']['value']


@pytest.mark.parametrize('setting', CONFIG_SETTINGS)
@pytest.mark.parametrize('type_name', PURE_TYPES)
def test_no_config_setting_changes_a_pure_annotation_schema(type_name: str, setting: str) -> None:
    """The caches assume config cannot change what a pure annotation generates.

    If a new setting ever reaches one of these schemas it has to enter the cache key (or the
    type has to stop being pure), and this is what will say so.
    """
    off, on = CONFIG_SETTINGS[setting]
    annotation = PURE_TYPES[type_name]
    without = _field_schema(annotation, setting, off)
    # cleared in between, so the second model generates its schema rather than being handed
    # the first one's - otherwise this would compare a cache entry with itself and pass
    # whatever the setting does
    _clear_caches()
    assert without == _field_schema(annotation, setting, on)


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


def test_hook_added_to_a_trusted_leaf_class_after_caching_is_honoured() -> None:
    """Trusted leaf classes are regular python classes, so a hook can appear at any time."""

    class Before(BaseModel):
        value: UUID

    assert Before(value=UUID(int=0)).value == UUID(int=0)

    UUID.__get_pydantic_core_schema__ = classmethod(  # type: ignore[attr-defined]
        lambda cls, source, handler: core_schema.no_info_after_validator_function(lambda v: 'hooked', handler(source))
    )
    try:

        class After(BaseModel):
            value: UUID

        assert After(value=UUID(int=0)).value == 'hooked'
    finally:
        del UUID.__get_pydantic_core_schema__  # type: ignore[attr-defined]


def test_url_constraints_mutated_in_place_after_caching_are_honoured() -> None:
    """`AnyUrl._constraints` is a mutable instance on a mutable class attribute."""

    class Before(BaseModel):
        value: AnyUrl

    assert Before(value='http://example.com')

    original = AnyUrl._constraints.allowed_schemes
    AnyUrl._constraints.allowed_schemes = ['https']
    try:

        class After(BaseModel):
            value: AnyUrl

        with pytest.raises(ValidationError):
            After(value='http://example.com')
    finally:
        AnyUrl._constraints.allowed_schemes = original


def test_one_field_object_reused_by_two_models() -> None:
    """A single `Field()` assigned in two models must configure both."""
    shared = Field(default=1, description='shared')

    class First(BaseModel):
        a: int = shared

    class Second(BaseModel):
        b: int = shared

    assert First().a == 1 and Second().b == 1
    assert First.model_fields['a'].description == 'shared'
    assert Second.model_fields['b'].description == 'shared'


def test_equal_mutable_defaults_are_not_shared_between_models() -> None:
    """Two models with an equal list default must not end up with the same list."""

    class First(BaseModel):
        value: list[int] = []

    class Second(BaseModel):
        value: list[int] = []

    first = First()
    first.value.append(1)
    assert Second().value == []


def test_literal_of_an_enum_member_is_not_pure() -> None:
    """An enum is a mutable python class, so a `Literal` over one cannot be treated as pure."""

    class Colour(Enum):
        red = 'red'

    assert _schema_cache.pure_annotation_cache_key(Literal[Colour.red]) is _schema_cache.NOT_PURE
