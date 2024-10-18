"""
Tests for internal things that are complex enough to warrant their own unit tests.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import Any, List, Optional, Tuple, Union

import pytest
from dirty_equals import IsPartialDict, IsStr
from pydantic_core import CoreSchema, core_schema
from typing_extensions import TypedDict

from pydantic import BaseModel, TypeAdapter
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._generate_schema import GenerateSchema
from pydantic._internal._repr import Representation
from pydantic._internal._validators import _extract_decimal_digits_info


def ref(contains: str) -> IsStr:
    return IsStr(regex=f'.*{contains}.*')


def match(**kwargs: Any) -> IsPartialDict:
    return IsPartialDict(kwargs)


def init_schema_and_clean_schema(type_: Any) -> Tuple[CoreSchema, CoreSchema]:
    gen = GenerateSchema(ConfigWrapper(None))
    schema = gen.generate_schema(type_)
    clean_schema = gen.clean_schema(schema, deep_copy=True)
    assert TypeAdapter(type_).json_schema()  # Just to make sure it works and test setup is sane
    return schema, clean_schema


def test_simple_core_schema_with_no_references():
    init, clean = init_schema_and_clean_schema(List[int])
    assert init == core_schema.list_schema(core_schema.int_schema())
    assert clean == core_schema.list_schema(core_schema.int_schema())


@pytest.mark.parametrize('deep_ref', [False, True])
def test_core_schema_with_different_reference_depths_gets_inlined(deep_ref: bool):
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    init, clean = init_schema_and_clean_schema(List[M2] if deep_ref else M2)

    inner = match(type='definition-ref', schema_ref=ref('M2'))
    assert init == (match(type='list', items_schema=inner) if deep_ref else inner)

    inner = match(type='model', cls=M2, schema=match(fields={'b': match(schema=match(type='model', cls=M1))}))
    assert clean == (match(type='list', items_schema=inner) if deep_ref else inner)


@pytest.mark.parametrize('deep_ref', [False, True])
def test_core_schema_simple_recursive_schema_uses_refs(deep_ref: bool):
    class M1(BaseModel):
        a: 'M2'

    class M2(BaseModel):
        b: M1

    init, clean = init_schema_and_clean_schema(List[M1] if deep_ref else M1)

    inner = match(type='definition-ref', schema_ref=ref('M1'))
    assert init == (match(type='list', items_schema=inner) if deep_ref else inner)

    inner = match(type='definition-ref', schema_ref=ref('M1'))
    assert clean == match(
        type='definitions',
        schema=match(type='list', items_schema=inner) if deep_ref else inner,
        definitions=[match(type='model', ref=ref('M1')), match(type='model', ref=ref('M2'))],
    )


@pytest.mark.parametrize('deep_ref', [False, True])
def test_core_schema_with_deeply_nested_schema_with_multiple_references_gets_inlined(deep_ref: bool):
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    class M3(BaseModel):
        c: M2
        d: M1

    init, clean = init_schema_and_clean_schema(List[M3] if deep_ref else M3)

    inner = match(type='definition-ref', schema_ref=ref('M3'))
    assert init == (match(type='list', items_schema=inner) if deep_ref else inner)

    inner = match(
        type='model',
        cls=M3,
        schema=match(
            fields={'c': match(schema=match(type='model', cls=M2)), 'd': match(schema=match(type='model', cls=M1))}
        ),
    )
    assert clean == (match(type='list', items_schema=inner) if deep_ref else inner)


def test_core_schema_complex_recursive_schema_uses_refs():
    class M1(BaseModel):
        a: 'M3'

    class M2(BaseModel):
        b: M1

    class M3(BaseModel):
        c: M2

    init, clean = init_schema_and_clean_schema(M1)
    assert init == match(type='definition-ref', schema_ref=ref('M1'))
    assert clean == match(
        type='definitions',
        schema=match(type='definition-ref', schema_ref=ref('M1')),
        definitions=[
            match(type='model', cls=M1, schema=match(fields={'a': match(schema=match(schema_ref=ref('M3')))})),
            match(type='model', cls=M3, schema=match(fields={'c': match(schema=match(schema_ref=ref('M2')))})),
            match(type='model', cls=M2, schema=match(fields={'b': match(schema=match(schema_ref=ref('M1')))})),
        ],
    )


@pytest.mark.parametrize('deep_ref', [False, True])
def test_core_schema_with_model_used_in_multiple_places(deep_ref: bool):
    class M1(BaseModel):
        a: int

    class M2(BaseModel):
        b: M1

    class M3(BaseModel):
        c: Union[M2, M1]
        d: M1

    init, clean = init_schema_and_clean_schema(List[M3] if deep_ref else M3)

    inner = match(type='definition-ref', schema_ref=ref('M3'))
    assert init == (match(type='list', items_schema=inner) if deep_ref else inner)

    inner = match(type='model', cls=M3)
    assert clean == match(
        type='definitions',
        schema=(match(type='list', items_schema=inner) if deep_ref else inner),
        definitions=[match(type='model', cls=M1)],  # This was used in multiple places
    )


# https://github.com/pydantic/pydantic/issues/6270
def test_core_schema_with_multiple_duplicate_enums():
    class MyEnum(Enum):
        a = auto()

    class MyModel(TypedDict):
        a: Optional[MyEnum]
        b: Optional[MyEnum]

    _, clean = init_schema_and_clean_schema(MyModel)
    for k in ['a', 'b']:
        assert clean['fields'][k]['schema']['schema']['type'] == 'enum'
        assert clean['fields'][k]['schema']['schema']['cls'] is MyEnum


def test_representation_integrations():
    devtools = pytest.importorskip('devtools')

    @dataclass
    class Obj(Representation):
        int_attr: int = 42
        str_attr: str = 'Marvin'

    obj = Obj()

    assert str(devtools.debug.format(obj)).split('\n')[1:] == [
        '    Obj(',
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
