from __future__ import annotations

from typing import TypedDict

from pydantic_core._pydantic_core import _schema_gather
from pydantic_core.core_schema import CoreSchema, DefinitionReferenceSchema

__all__ = [
    'GatherResult',
    'MissingDefinitionError',
    'gather_schemas_for_cleaning',
]

MissingDefinitionError = _schema_gather.MissingDefinitionError


class GatherResult(TypedDict):
    """Schema traversing result."""

    collected_references: dict[str, DefinitionReferenceSchema | None]
    """The collected definition references.

    If a definition reference schema can be inlined, it means that there is
    only one in the whole core schema. As such, it is stored as the value.
    Otherwise, the value is set to `None`.
    """

    deferred_discriminator_schemas: list[CoreSchema]
    """The list of core schemas having the discriminator application deferred."""


def gather_schemas_for_cleaning(schema: CoreSchema, definitions: dict[str, CoreSchema]) -> GatherResult:
    """Traverse the core schema and definitions and return the necessary information for schema cleaning.

    During the core schema traversing, any `'definition-ref'` schema is:

    - Validated: the reference must point to an existing definition. If this is not the case, a
      `MissingDefinitionError` exception is raised.
    - Stored in the context: the actual reference is stored in the context. Depending on whether
      the `'definition-ref'` schema is encountered more that once, the schema itself is also
      saved in the context to be inlined (i.e. replaced by the definition it points to).
    """
    collected_references, deferred_discriminator_schemas = _schema_gather.gather_schemas_for_cleaning(
        schema, definitions
    )
    return {
        'collected_references': collected_references,
        'deferred_discriminator_schemas': deferred_discriminator_schemas,
    }
