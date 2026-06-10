"""
Regression test for https://github.com/pydantic/pydantic/issues/11553

Title: PydanticOmit failing with duplicated union field

When a custom type raises PydanticOmit in __get_pydantic_json_schema__,
schema generation must succeed even when that type appears in multiple
fields, causing pydantic-core to create a 'definitions' wrapper with
'definition-ref' nodes.
"""

import pytest
from pydantic_core import PydanticOmit
from pydantic import BaseModel


class OmittedType(BaseModel):
    """A BaseModel subclass that raises PydanticOmit from its JSON schema hook."""

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        raise PydanticOmit


def test_single_field_omitted_type_works() -> None:
    """Single field: already worked before, must keep working (non-regression)."""

    class SingleField(BaseModel):
        first_field: list[float | OmittedType]

    schema = SingleField.model_json_schema()
    assert schema == {
        'properties': {
            'first_field': {
                'items': {'type': 'number'},
                'title': 'First Field',
                'type': 'array',
            },
        },
        'required': ['first_field'],
        'title': 'SingleField',
        'type': 'object',
    }


def test_duplicated_field_omitted_type_regression() -> None:
    """
    Regression: two fields share the same omitted type.

    pydantic-core generates a 'definitions' wrapper for DuplicatedField because
    OmittedType is referenced from two fields. Each field's schema contains a
    'definition-ref' node pointing at the OmittedType definition.

    Expected: OmittedType is silently omitted from both union branches.
    Actual (bug): PydanticOmit propagates uncaught and crashes schema generation.
    """

    class DuplicatedField(BaseModel):
        first_field: list[float | OmittedType]
        second_field: list[float | OmittedType]

    # This must NOT raise PydanticOmit (or any other exception):
    schema = DuplicatedField.model_json_schema()

    assert schema == {
        'properties': {
            'first_field': {
                'items': {'type': 'number'},
                'title': 'First Field',
                'type': 'array',
            },
            'second_field': {
                'items': {'type': 'number'},
                'title': 'Second Field',
                'type': 'array',
            },
        },
        'required': ['first_field', 'second_field'],
        'title': 'DuplicatedField',
        'type': 'object',
    }
    # No stale $defs entry for the omitted type:
    assert '$defs' not in schema
