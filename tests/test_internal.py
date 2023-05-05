"""
Tests for internal things that are complex enough to warrant their own unit tests.
"""
import pytest
from pydantic_core import core_schema as cs

# TODO: rewrite these tests to use the two individual functions
from pydantic._internal._core_utils import _simplify_schema_references as simplify_schema_references  # type: ignore


@pytest.mark.parametrize(
    'input_schema, expected_output',
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
            cs.list_schema(cs.list_schema(cs.int_schema())),
        ),
        # Test case 3: Schema with multiple single-level nested references
        (
            cs.list_schema(
                cs.definitions_schema(cs.definition_reference_schema('int'), definitions=[cs.int_schema(ref='int')])
            ),
            cs.list_schema(cs.int_schema()),
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
            cs.list_schema(cs.list_schema(cs.list_schema(cs.int_schema()))),
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
            cs.list_schema(cs.list_schema(cs.int_schema())),
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
            cs.list_schema(cs.list_schema(cs.int_schema())),
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
                        cs.list_schema(cs.definition_reference_schema('int')),
                        cs.tuple_variable_schema(cs.definition_reference_schema('int')),
                    ]
                ),
                definitions=[cs.int_schema(ref='int')],
            ),
        ),
    ],
)
def test_build_definitions_schema(input_schema: cs.CoreSchema, expected_output: cs.CoreSchema):
    result = simplify_schema_references(input_schema, True)
    assert result == expected_output
