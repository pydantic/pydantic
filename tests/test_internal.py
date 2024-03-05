"""
Tests for internal things that are complex enough to warrant their own unit tests.
"""
from dataclasses import dataclass

import pytest
from pydantic_core import CoreSchema, SchemaValidator
from pydantic_core import core_schema as cs

from pydantic._internal._core_utils import (
    HAS_INVALID_SCHEMAS_METADATA_KEY,
    Walk,
    collect_invalid_schemas,
    simplify_schema_references,
    walk_core_schema,
)
from pydantic._internal._repr import Representation


def remove_metadata(schema: CoreSchema) -> CoreSchema:
    def inner(s: CoreSchema, recurse: Walk) -> CoreSchema:
        s = s.copy()
        s.pop('metadata', None)
        return recurse(s, inner)

    return walk_core_schema(schema, inner)


@pytest.mark.parametrize(
    'input_schema,inlined',
    [
        # Test case 1: Simple schema with no references
        (cs.list_schema(cs.int_schema()), cs.list_schema(cs.int_schema())),
        # Test case 2: Schema with single-level nested references
        (
            cs.definitions_schema(
                cs.list_schema(cs.definition_reference_schema('list_of_ints')),
                definitions=[
                    cs.list_schema(cs.definition_reference_schema('int'), ref='list_of_ints'),
                    cs.int_schema(ref='int'),
                ],
            ),
            cs.list_schema(cs.list_schema(cs.int_schema(ref='int'), ref='list_of_ints')),
        ),
        # Test case 3: Schema with multiple single-level nested references
        (
            cs.list_schema(
                cs.definitions_schema(cs.definition_reference_schema('int'), definitions=[cs.int_schema(ref='int')])
            ),
            cs.list_schema(cs.int_schema(ref='int')),
        ),
        # Test case 4: A simple recursive schema
        (
            cs.list_schema(cs.definition_reference_schema(schema_ref='list'), ref='list'),
            cs.definitions_schema(
                cs.definition_reference_schema(schema_ref='list'),
                definitions=[cs.list_schema(cs.definition_reference_schema(schema_ref='list'), ref='list')],
            ),
        ),
        # Test case 5: Deeply nested schema with multiple references
        (
            cs.definitions_schema(
                cs.list_schema(cs.definition_reference_schema('list_of_lists_of_ints')),
                definitions=[
                    cs.list_schema(cs.definition_reference_schema('list_of_ints'), ref='list_of_lists_of_ints'),
                    cs.list_schema(cs.definition_reference_schema('int'), ref='list_of_ints'),
                    cs.int_schema(ref='int'),
                ],
            ),
            cs.list_schema(
                cs.list_schema(
                    cs.list_schema(cs.int_schema(ref='int'), ref='list_of_ints'), ref='list_of_lists_of_ints'
                )
            ),
        ),
        # Test case 6: More complex recursive schema
        (
            cs.definitions_schema(
                cs.list_schema(cs.definition_reference_schema(schema_ref='list_of_ints_and_lists')),
                definitions=[
                    cs.list_schema(
                        cs.definitions_schema(
                            cs.definition_reference_schema(schema_ref='int_or_list'),
                            definitions=[
                                cs.int_schema(ref='int'),
                                cs.tuple_variable_schema(
                                    cs.definition_reference_schema(schema_ref='list_of_ints_and_lists'), ref='a tuple'
                                ),
                            ],
                        ),
                        ref='list_of_ints_and_lists',
                    ),
                    cs.int_schema(ref='int_or_list'),
                ],
            ),
            cs.list_schema(cs.list_schema(cs.int_schema(ref='int_or_list'), ref='list_of_ints_and_lists')),
        ),
        # Test case 7: Schema with multiple definitions and nested references, some of which are unused
        (
            cs.definitions_schema(
                cs.list_schema(cs.definition_reference_schema('list_of_ints')),
                definitions=[
                    cs.list_schema(
                        cs.definitions_schema(
                            cs.definition_reference_schema('int'), definitions=[cs.int_schema(ref='int')]
                        ),
                        ref='list_of_ints',
                    )
                ],
            ),
            cs.list_schema(cs.list_schema(cs.int_schema(ref='int'), ref='list_of_ints')),
        ),
        # Test case 8: Reference is used in multiple places
        (
            cs.definitions_schema(
                cs.union_schema(
                    [
                        cs.definition_reference_schema('list_of_ints'),
                        cs.tuple_variable_schema(cs.definition_reference_schema('int')),
                    ]
                ),
                definitions=[
                    cs.list_schema(cs.definition_reference_schema('int'), ref='list_of_ints'),
                    cs.int_schema(ref='int'),
                ],
            ),
            cs.definitions_schema(
                cs.union_schema(
                    [
                        cs.list_schema(cs.definition_reference_schema('int'), ref='list_of_ints'),
                        cs.tuple_variable_schema(cs.definition_reference_schema('int')),
                    ]
                ),
                definitions=[cs.int_schema(ref='int')],
            ),
        ),
        # Test case 9: https://github.com/pydantic/pydantic/issues/6270
        (
            cs.definitions_schema(
                cs.definition_reference_schema('model'),
                definitions=[
                    cs.typed_dict_schema(
                        {
                            'a': cs.typed_dict_field(
                                cs.nullable_schema(
                                    cs.int_schema(ref='ref'),
                                ),
                            ),
                            'b': cs.typed_dict_field(
                                cs.nullable_schema(
                                    cs.int_schema(ref='ref'),
                                ),
                            ),
                        },
                        ref='model',
                    ),
                ],
            ),
            cs.definitions_schema(
                cs.typed_dict_schema(
                    {
                        'a': cs.typed_dict_field(
                            cs.nullable_schema(cs.definition_reference_schema(schema_ref='ref')),
                        ),
                        'b': cs.typed_dict_field(
                            cs.nullable_schema(cs.definition_reference_schema(schema_ref='ref')),
                        ),
                    },
                    ref='model',
                ),
                definitions=[
                    cs.int_schema(ref='ref'),
                ],
            ),
        ),
    ],
)
def test_build_schema_defs(input_schema: cs.CoreSchema, inlined: cs.CoreSchema):
    actual_inlined = remove_metadata(simplify_schema_references(input_schema))
    assert actual_inlined == inlined
    SchemaValidator(actual_inlined)  # check for validity


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


def test_schema_is_valid():
    assert collect_invalid_schemas(cs.none_schema()) is False
    assert (
        collect_invalid_schemas(cs.nullable_schema(cs.int_schema(metadata={HAS_INVALID_SCHEMAS_METADATA_KEY: True})))
        is True
    )
