from __future__ import annotations as _annotations

from collections.abc import Hashable, Sequence
from typing import TYPE_CHECKING, Any, cast

from pydantic_core import CoreSchema, core_schema

from ..errors import PydanticUserError
from . import _core_utils
from ._core_utils import (
    CoreSchemaField,
)

if TYPE_CHECKING:
    from ..types import Discriminator
    from ._core_metadata import CoreMetadata


class MissingDefinitionForUnionRef(Exception):
    """Raised when applying a discriminated union discriminator to a schema
    requires a definition that is not yet defined
    """

    def __init__(self, ref: str) -> None:
        self.ref = ref
        super().__init__(f'Missing definition for ref {self.ref!r}')


def set_discriminator_in_metadata(schema: CoreSchema, discriminator: Any) -> None:
    """Set the discriminator in the schema metadata for discriminated unions.
    Normalizes None type annotations to Literal[None] for discriminator evaluation.
    """
    metadata: CoreMetadata = schema.get('metadata') or {}
    metadata['pydantic_js_discriminator'] = discriminator
    schema['metadata'] = metadata
