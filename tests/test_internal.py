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


def test_pure_annotation_schema_cache_is_bounded():
    """The set of pure annotations is unbounded (`Literal[...]` can hold arbitrary values), so a
    process building models from dynamically generated schemas must not grow the cache forever.
    """
    from typing import Literal

    from pydantic._internal._generate_schema import (
        _PURE_ANNOTATION_CACHE_SIZE,
        _pure_annotation_schema_cache,
    )

    for i in range(2 * _PURE_ANNOTATION_CACHE_SIZE):
        create_model(f'M{i}', v=(Literal[f'a{i}', f'b{i}'], ...))
        assert len(_pure_annotation_schema_cache) <= _PURE_ANNOTATION_CACHE_SIZE


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
