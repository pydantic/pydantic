from typing import final

from pydantic_core.core_schema import CoreSchema, DefinitionReferenceSchema

__all__ = ['MissingDefinitionError', 'gather_schemas_for_cleaning']

@final
class MissingDefinitionError(LookupError):
    """A reference was pointing to a non-existing core schema."""

    def __init__(self, schema_reference: str, /) -> None: ...
    @property
    def schema_reference(self) -> str: ...

def gather_schemas_for_cleaning(
    schema: CoreSchema, definitions: dict[str, CoreSchema]
) -> tuple[dict[str, DefinitionReferenceSchema | None], list[CoreSchema]]:
    """Traverse the core schema and definitions and return the necessary information for schema cleaning.

    During the core schema traversing, any `'definition-ref'` schema is:

    - Validated: the reference must point to an existing definition. If this is not the case, a
      `MissingDefinitionError` exception is raised.
    - Stored in the context: the actual reference is stored in the context. Depending on whether
      the `'definition-ref'` schema is encountered more than once, the schema itself is also
      saved in the context to be inlined (i.e. replaced by the definition it points to).

    Returns a `(collected_references, deferred_discriminator_schemas)` tuple:

    - `collected_references`: the collected definition references. If a definition reference schema
      can be inlined, it means that there is only one in the whole core schema. As such, it is stored
      as the value. Otherwise, the value is set to `None`.
    - `deferred_discriminator_schemas`: the list of core schemas having the discriminator application deferred.
    """
