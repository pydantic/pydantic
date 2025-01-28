"""
Tests for internal things that are complex enough to warrant their own unit tests.
"""

import sys
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Union

import pytest
from dirty_equals import Contains, IsPartialDict
from pydantic_core import CoreSchema
from pydantic_core import core_schema as cs

from pydantic import BaseModel, TypeAdapter
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._generate_schema import GenerateSchema
from pydantic._internal._repr import Representation
from pydantic._internal._validators import _extract_decimal_digits_info


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
        c: Union[M2, M1]
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

    if sys.version_info < (3, 11):
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
