"""
Tests for internal things that are complex enough to warrant their own unit tests.
"""

import sys
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest
from dirty_equals import Contains, IsPartialDict
from pydantic_core import CoreSchema, PydanticUndefined
from pydantic_core import core_schema as cs

from pydantic import BaseModel, TypeAdapter, ValidationError, create_model
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._core_metadata import update_core_metadata
from pydantic._internal._fields import resolve_default_value
from pydantic._internal._generate_schema import GenerateSchema
from pydantic._internal._repr import Representation
from pydantic._internal._validators import _extract_decimal_digits_info
from pydantic.config import JsonDict
from pydantic.json_schema import GetJsonSchemaHandler, JsonSchemaValue, PydanticJsonSchemaWarning


def init_schema_and_cleaned_schema(type_: Any) -> tuple[CoreSchema, CoreSchema]:
    gen = GenerateSchema(ConfigWrapper(None))
    schema = gen.generate_schema(type_)
    cleaned_schema = deepcopy(schema)
    cleaned_schema = gen.clean_schema(cleaned_schema)
    assert TypeAdapter(type_).pydantic_complete  # Just to make sure it works and test setup is sane
    return schema, cleaned_schema


def test_simple_core_schema_with_no_references() -> None:
    init, cleaned = init_schema_and_cleaned_schema(list[int])
    assert init == cs.list_schema(cs.int_schema())
    assert cleaned == cs.list_schema(cs.int_schema())


@pytest.mark.parametrize('nested_ref', [False, True])
def test_core_schema_with_different_reference_depths_gets_inlined(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M2] if nested_ref else M2)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M2'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(
        type='model',
        cls=M2,
        schema=IsPartialDict(fields={'b': IsPartialDict(schema=IsPartialDict(type='model', cls=M1))}),
    )
    assert cleaned == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)


@pytest.mark.parametrize('nested_ref', [False, True])
@pytest.mark.xfail(
    reason=(
        "While the cleaned schema is of type 'definitions', the inner schema is inlined. This is not an "
        'issue, but the test is kept so that we notice the change when tweaking core schema generation.'
    )
)
def test_core_schema_simple_recursive_schema_uses_refs(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: 'M2'

    class M2(BaseModel):
        b: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M1] if nested_ref else M1)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M1'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M1'))
    assert cleaned == IsPartialDict(
        type='definitions',
        schema=IsPartialDict(type='list', items_schema=inner) if nested_ref else inner,
        definitions=[IsPartialDict(type='model', ref=Contains('M1')), IsPartialDict(type='model', ref=Contains('M2'))],
    )


@pytest.mark.parametrize('nested_ref', [False, True])
def test_core_schema_with_deeply_nested_schema_with_multiple_references_gets_inlined(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    class M3(BaseModel):
        c: M2
        d: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M3] if nested_ref else M3)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M3'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(
        type='model',
        cls=M3,
        schema=IsPartialDict(
            fields={
                'c': IsPartialDict(schema=IsPartialDict(type='model', cls=M2)),
                'd': IsPartialDict(schema=IsPartialDict(type='model', cls=M1)),
            }
        ),
    )
    assert cleaned == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)


@pytest.mark.parametrize('nested_ref', [False, True])
def test_core_schema_with_model_used_in_multiple_places(nested_ref: bool) -> None:
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    class M3(BaseModel):
        c: M2 | M1
        d: M1

    init, cleaned = init_schema_and_cleaned_schema(list[M3] if nested_ref else M3)

    inner = IsPartialDict(type='definition-ref', schema_ref=Contains('M3'))
    assert init == (IsPartialDict(type='list', items_schema=inner) if nested_ref else inner)

    inner = IsPartialDict(type='model', cls=M3)
    assert cleaned == IsPartialDict(
        type='definitions',
        schema=(IsPartialDict(type='list', items_schema=inner) if nested_ref else inner),
        definitions=[IsPartialDict(type='model', cls=M1)],  # This was used in multiple places
    )


def test_representation_integrations():
    devtools = pytest.importorskip('devtools')

    @dataclass
    class Obj(Representation):
        int_attr: int = 42
        str_attr: str = 'Marvin'

    obj = Obj()

    if sys.version_info < (3, 11) or sys.implementation.name == 'pypy':
        assert str(devtools.debug.format(obj)).split('\n')[1:] == [
            '    Obj(',
            '        int_attr=42,',
            "        str_attr='Marvin',",
            '    ) (Obj)',
        ]
    else:
        assert str(devtools.debug.format(obj)).split('\n')[1:] == [
            '    obj: Obj(',
            '        int_attr=42,',
            "        str_attr='Marvin',",
            '    ) (Obj)',
        ]
    assert list(obj.__rich_repr__()) == [('int_attr', 42), ('str_attr', 'Marvin')]


@pytest.mark.parametrize(
    'decimal,decimal_places,digits',
    [
        (Decimal('0.0'), 1, 1),
        (Decimal('0.'), 0, 1),
        (Decimal('0.000'), 3, 3),
        (Decimal('0.0001'), 4, 4),
        (Decimal('.0001'), 4, 4),
        (Decimal('123.123'), 3, 6),
        (Decimal('123.1230'), 4, 7),
    ],
)
def test_decimal_digits_calculation(decimal: Decimal, decimal_places: int, digits: int) -> None:
    assert _extract_decimal_digits_info(decimal) == (decimal_places, digits)


@pytest.mark.parametrize(
    'value',
    [Decimal.from_float(float('nan')), 1.0],
)
def test_decimal_digits_calculation_type_error(value) -> None:
    with pytest.raises(TypeError, match=f'Unable to extract decimal digits info from supplied value {value}'):
        _extract_decimal_digits_info(value)


def test_update_js_extra_as_callable_when_existing_js_extra_is_dict_type():
    """
    It should ignore the callable with a warning.
    """
    metadata: dict[str, Any] = {}

    extra_dict: JsonDict = {'testKey': 'testValue'}

    def extra_func(schema: JsonDict) -> None:
        schema['testKey'] = 'testValue'

    update_core_metadata(metadata, pydantic_js_extra=extra_dict)

    with pytest.warns(PydanticJsonSchemaWarning):
        update_core_metadata(metadata, pydantic_js_extra=extra_func)
    assert metadata['pydantic_js_extra'] is extra_dict


def test_update_js_extra_as_callable_when_existing_js_extra_is_callable_type():
    """
    It should overwrite existing js_extra with the new callable.
    """
    metadata: dict[str, Any] = {}

    def extra_func1(schema: JsonDict) -> None:
        schema['testKey1'] = 'testValue1'

    def extra_func2(schema: JsonDict) -> None:
        schema['testKey2'] = 'testValue2'

    update_core_metadata(metadata, pydantic_js_extra=extra_func1)
    update_core_metadata(metadata, pydantic_js_extra=extra_func2)
    assert metadata['pydantic_js_extra'] is extra_func2


def test_pydantic_js_functions():
    metadata: dict[str, Any] = {}

    def func(schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {'type': 'string'}

    update_core_metadata(
        metadata,
        pydantic_js_functions=[func],
    )

    assert metadata['pydantic_js_functions'] == [func]


@pytest.mark.parametrize(
    [
        'default',
        'default_factory',
        'default_factory_takes_validated_data_argument',
        'validated_data',
        'call_default_factory',
        'expected',
    ],
    [
        ('foo', None, False, None, True, 'foo'),
        ('foo', None, False, None, False, 'foo'),
        ('foo-unused', lambda: 'foo', False, None, False, PydanticUndefined),
        ('foo-unused', lambda: 'foo', False, None, True, 'foo'),
        ('foo-unused', lambda data: data['foo'], True, {'foo': 'bar'}, True, 'bar'),
    ],
)
def test_resolve_default_value(
    default,
    default_factory,
    default_factory_takes_validated_data_argument,
    validated_data,
    call_default_factory,
    expected,
):
    result = resolve_default_value(
        default=default,
        default_factory=default_factory,
        default_factory_takes_validated_data_argument=default_factory_takes_validated_data_argument,
        validated_data=validated_data,
        call_default_factory=call_default_factory,
    )
    assert result == expected


def test_resolve_default_value_missing_validated_data():
    # When factory requires validated_data but none is provided, a ValueError should be raised.
    with pytest.raises(ValueError):
        resolve_default_value(
            default='foo',
            default_factory=lambda data: data['foo'],
            default_factory_takes_validated_data_argument=True,
            validated_data=None,
            call_default_factory=True,
        )


class _NotPure:
    pass


@pytest.mark.parametrize(
    ['annotation', 'pure'],
    [
        (int, True),
        (str, True),
        (type(None), True),
        ('int | None', True),
        ('list[int]', True),
        ('dict[str, list[int | None]]', True),
        ('tuple[int, ...]', True),
        ('Literal["a", "b"]', True),
        # `None` is a valid annotation, and must not be confused with the "not pure" sentinel.
        # Note that unlike `typing.Tuple[int, None]`, the builtin generic alias form does *not*
        # normalize `None` to `NoneType`, so the key builder has to cope with a literal `None` arg:
        (None, True),
        ('list[None]', True),
        ('tuple[int, None]', True),
        (_NotPure, False),
        ('list[_NotPure]', False),
        ('int | _NotPure', False),
        ('Literal[_AnEnum.A]', False),
        ('list["Forward"]', False),
    ],
)
def test_pure_annotation_cache_key(annotation, pure):
    import enum
    from typing import Literal  # noqa: F401

    from pydantic._internal._generate_schema import _NOT_PURE, _pure_annotation_cache_key

    class _AnEnum(enum.Enum):
        A = 'a'

    if isinstance(annotation, str):
        annotation = eval(annotation)

    key = _pure_annotation_cache_key(annotation)
    assert (key is not _NOT_PURE) is pure


def test_pure_annotation_cache_key_is_order_sensitive():
    """Unions and literals compare (and hash) equal regardless of argument order,
    so the annotations themselves would be unsound cache keys."""
    from typing import Literal, Union

    from pydantic._internal._generate_schema import _pure_annotation_cache_key

    assert _pure_annotation_cache_key(Union[int, str]) != _pure_annotation_cache_key(Union[str, int])  # noqa: UP007
    assert _pure_annotation_cache_key(Literal['a', 'b']) != _pure_annotation_cache_key(Literal['b', 'a'])
    # `1 == True`, so the value types must take part in the key:
    assert _pure_annotation_cache_key(Literal[1]) != _pure_annotation_cache_key(Literal[True])
    # The same annotation spelled differently must produce equal keys:
    assert _pure_annotation_cache_key(Union[int, None]) == _pure_annotation_cache_key(int | None)  # noqa: UP007


def test_pure_annotation_schema_cache_schemas_are_independent():
    """Models sharing an annotation must not share (mutable parts of) their core schemas."""

    class A(BaseModel):
        v: 'int | None' = None

    class B(BaseModel):
        v: 'int | None' = None

    schema_a = A.__pydantic_core_schema__['schema']['fields']['v']['schema']
    schema_b = B.__pydantic_core_schema__['schema']['fields']['v']['schema']
    assert schema_a == schema_b
    assert schema_a is not schema_b
    assert schema_a['schema'] is not schema_b['schema']

    schema_a['schema']['type'] = 'mutated'
    assert schema_b['schema']['type'] == 'nullable'


def test_pure_annotation_schema_cache_union_order():
    """Regression test: `Union[int, str]` and `Union[str, int]` compare equal but their
    schemas differ, so they must not share a cache entry."""
    from typing import Union

    class A(BaseModel):
        v: Union[int, str] = 1  # noqa: UP007

    class B(BaseModel):
        v: Union[str, int] = 'a'  # noqa: UP007

    choices_a = [c['type'] for c in A.__pydantic_core_schema__['schema']['fields']['v']['schema']['schema']['choices']]
    choices_b = [c['type'] for c in B.__pydantic_core_schema__['schema']['fields']['v']['schema']['schema']['choices']]
    assert choices_a == ['int', 'str']
    assert choices_b == ['str', 'int']


@pytest.mark.filterwarnings('ignore:`json_encoders` is deprecated.*:DeprecationWarning')
def test_pure_annotation_schema_cache_json_encoders_bypass():
    """`json_encoders` alter the generated schema, so configs setting them bypass the cache."""

    class A(BaseModel):
        v: 'str | None' = None

    class B(BaseModel):
        model_config = {'json_encoders': {str: lambda v: f'enc:{v}'}}

        v: 'str | None' = None

    assert A(v='x').model_dump_json() == '{"v":"x"}'
    assert B(v='x').model_dump_json() == '{"v":"enc:x"}'


def test_pure_annotation_caches_are_bounded():
    """The set of pure annotations is unbounded (`Literal[...]` can hold arbitrary values, and
    metadata and defaults take part in some keys), so a process building models from dynamically
    generated schemas must not grow the caches forever.
    """
    from typing import Literal

    from pydantic._internal import _schema_cache

    caches = (
        _schema_cache.pure_annotation_schema_cache,
        _schema_cache.field_info_template_cache,
        _schema_cache.model_field_schema_cache,
        _schema_cache._pure_annotations_seen,
    )
    for i in range(2 * _schema_cache.CACHE_SIZE_LIMIT):
        create_model(f'M{i}', v=(Literal[f'a{i}', f'b{i}'], f'a{i}'))
        for cache in caches:
            assert len(cache) <= _schema_cache.CACHE_SIZE_LIMIT


def test_pure_annotation_cache_key_membership_is_identity_based():
    """A class comparing equal to a pure leaf type must not be classified as pure.

    It would otherwise share the leaf type's cache entry, letting its custom
    `__get_pydantic_core_schema__` hook poison the schema generated for that leaf type
    (and vice versa).
    """
    from pydantic._internal._generate_schema import _NOT_PURE, _pure_annotation_cache_key

    class EqualsIntMeta(type):
        def __eq__(cls, other):
            return other is int or super().__eq__(other)

        def __hash__(cls):
            return hash(int)

    class LooksLikeInt(metaclass=EqualsIntMeta):
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type, handler):
            return cs.str_schema()

    assert LooksLikeInt == int and hash(LooksLikeInt) == hash(int)
    assert _pure_annotation_cache_key(LooksLikeInt) is _NOT_PURE
    assert _pure_annotation_cache_key(list[LooksLikeInt]) is _NOT_PURE

    class Model(BaseModel):
        a: LooksLikeInt
        b: int

    assert Model(a='x', b=1).a == 'x'
    with pytest.raises(ValidationError):
        Model(a='x', b='not an int')


def test_pure_annotation_schema_cache_none_annotations():
    """`None` is a valid (and pure) annotation, so it can't double as the "not pure" sentinel."""

    class A(BaseModel):
        v: None = None
        w: 'list[None]' = []
        x: 'tuple[int, None]' = (1, None)

    class B(BaseModel):
        v: None = None
        w: 'list[None]' = []
        x: 'tuple[int, None]' = (1, None)

    for name in ('v', 'w', 'x'):
        schema_a = A.__pydantic_core_schema__['schema']['fields'][name]['schema']
        schema_b = B.__pydantic_core_schema__['schema']['fields'][name]['schema']
        assert schema_a == schema_b
        assert schema_a is not schema_b

    assert B(w=[None], x=(2, None)).x == (2, None)
    with pytest.raises(ValidationError):
        B(v=1)


def test_field_info_template_cache_instances_are_independent():
    """Models sharing a field definition must not share `FieldInfo` state."""

    class A(BaseModel):
        v: 'int | None' = None

    class B(BaseModel):
        v: 'int | None' = None

    assert A.model_fields['v'] is not B.model_fields['v']
    A.model_fields['v'].description = 'mutated'
    assert B.model_fields['v'].description is None


def test_field_info_template_cache_annotation_spelling_preserved():
    """Equal-but-distinct annotation spellings must be preserved on `FieldInfo.annotation`."""
    from typing import Optional, Union, get_args

    class A(BaseModel):
        v: Union[int, str] = 1  # noqa: UP007
        w: Optional[str] = None  # noqa: UP045

    class B(BaseModel):
        v: Union[str, int] = 1  # noqa: UP007
        w: 'str | None' = None

    assert get_args(A.model_fields['v'].annotation) == (int, str)
    assert get_args(B.model_fields['v'].annotation) == (str, int)
    assert A.model_fields['w'].annotation == B.model_fields['w'].annotation


def test_model_field_schema_cache_respects_field_info_mutation_on_rebuild():
    """Directly mutating a `model_fields` entry and rebuilding must bypass the field schema cache."""

    class Model(BaseModel):
        a: int = 1

    Model.model_fields['a'].serialization_alias = 'A'
    Model.model_rebuild(force=True)
    assert Model(a=2).model_dump(by_alias=True) == {'A': 2}


def test_none_annotation_still_evaluates_to_none_type():
    class Model(BaseModel):
        v: None = None

    assert Model.model_fields['v'].annotation is type(None)


def test_encode_metadata_item_discriminates_value_types():
    import annotated_types

    from pydantic._internal._schema_cache import encode_metadata_item

    assert encode_metadata_item(annotated_types.Gt(1)) != encode_metadata_item(annotated_types.Gt(True))
    assert encode_metadata_item(annotated_types.Gt(0.0)) != encode_metadata_item(annotated_types.Gt(-0.0))
    assert encode_metadata_item(annotated_types.Gt(1)) == encode_metadata_item(annotated_types.Gt(1))
    # Items holding arbitrary objects (e.g. functions) are not encodable:
    assert encode_metadata_item(annotated_types.Predicate(bool)) is None


def test_field_schema_cache_with_constraints_and_aliases():
    from typing import Annotated

    from pydantic import Field, ValidationError

    class A(BaseModel):
        v: Annotated[int, Field(gt=0, le=10)] = 5
        w: Annotated[str, Field(alias='wAlias')] = 'x'

    class B(BaseModel):
        v: Annotated[int, Field(gt=0, le=10)] = 5
        w: Annotated[str, Field(alias='otherAlias')] = 'x'

    node_a = A.__pydantic_core_schema__['schema']['fields']['v']
    node_b = B.__pydantic_core_schema__['schema']['fields']['v']
    assert node_a == node_b
    assert node_a is not node_b

    # constraints are enforced through the cached node:
    with pytest.raises(ValidationError):
        B(v=11)

    # aliases take part in the cache key, so equal shapes with different aliases don't collide:
    assert A.__pydantic_core_schema__['schema']['fields']['w']['validation_alias'] == 'wAlias'
    assert B.__pydantic_core_schema__['schema']['fields']['w']['validation_alias'] == 'otherAlias'


def test_trusted_leaf_class_hook_patching_bypasses_cache():
    import uuid

    class A(BaseModel):
        v: uuid.UUID | None = None

    assert A.__pydantic_core_schema__['schema']['fields']['v']['schema']['schema']['schema']['type'] == 'uuid'

    uuid.UUID.__get_pydantic_core_schema__ = classmethod(lambda cls, source, handler: {'type': 'int'})
    try:

        class B(BaseModel):
            v: uuid.UUID | None = None

        assert B.__pydantic_core_schema__['schema']['fields']['v']['schema']['schema']['schema']['type'] == 'int'
    finally:
        del uuid.UUID.__get_pydantic_core_schema__

    class C(BaseModel):
        v: uuid.UUID | None = None

    assert C.__pydantic_core_schema__['schema']['fields']['v']['schema']['schema']['schema']['type'] == 'uuid'


def test_trusted_leaf_class_rejects_monkeypatched_hook(monkeypatch):
    """A hook monkeypatched onto a trusted leaf class must not be absorbed into the baseline.

    The expected hooks are pinned to `None` / pydantic's own functions rather than snapshotted from
    whatever is present on first use, which would trust a patch applied before the first build and
    then reuse one model's schema for every later one.
    """
    from pathlib import Path

    from pydantic._internal._schema_cache import NOT_PURE, _verified_leaf_class_key

    assert _verified_leaf_class_key(Path) is Path

    calls: list[Any] = []

    def custom_hook(cls, source, handler):
        calls.append(source)
        return cs.str_schema()

    monkeypatch.setattr(Path, '__get_pydantic_core_schema__', classmethod(custom_hook), raising=False)
    assert _verified_leaf_class_key(Path) is NOT_PURE

    class A(BaseModel):
        p: Path

    class B(BaseModel):
        p: Path

    # Both models must go through the custom hook, rather than the second reusing the first's schema:
    assert len(calls) == 2


def test_trusted_url_class_key_covers_mutable_class_attributes():
    """The URL schema hook reads `cls._constraints` and `cls.serialize_url`, so a change to either
    must not be served a schema cached before it.
    """
    from pydantic import HttpUrl
    from pydantic.networks import UrlConstraints

    original = HttpUrl._constraints
    try:

        class Before(BaseModel):
            u: HttpUrl

        HttpUrl._constraints = UrlConstraints(allowed_schemes=['https'])

        class After(BaseModel):
            u: HttpUrl

        Before(u='http://example.com')  # still valid under the constraints it was built with
        with pytest.raises(ValidationError):
            After(u='http://example.com')
    finally:
        HttpUrl._constraints = original
