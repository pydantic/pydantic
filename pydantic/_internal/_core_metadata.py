from __future__ import annotations as _annotations

import typing

import typing_extensions

if typing.TYPE_CHECKING:
    from pydantic_core import CoreSchema

    from ..config import JsonDict, JsonSchemaExtraCallable
    from ._schema_generation_shared import (
        GetJsonSchemaFunction,
    )


class CoreMetadata(typing_extensions.TypedDict, total=False):
    """A `TypedDict` for holding the metadata dict of the schema.

    Attributes:
        pydantic_js_functions: List of JSON schema functions.
        pydantic_js_annotation_functions: List of JSON schema functions that use ref simplification? TBD...
        pydantic_js_prefer_positional_arguments: Whether JSON schema generator will
            prefer positional over keyword arguments for an 'arguments' schema.
        pydantic_js_input_core_schema: Schema associated with the input value for the associated
            custom validation function. Only applies to before, plain, and wrap validators.

    TODO: Ultimately, we should move this structure to pydantic-core. At the moment, though,
    it's easier to iterate on if we leave it in pydantic until we feel there is a semi-stable API.

    That being said, we don't get significant type checking benefits by using this CoreMetadataHandler
    business, and that should be phased out as we migrate to a pydantic-core TypedDict, which
    will offer the same benefits.

    NOTE: this is currently not used, I'm just adding attributes for tracking purposes so that when we migrate
    to `pydantic-core`, things can be used.

    TODO: We'd like to refactor the storage of json related metadata to be more explicit, and less functionally oriented.
    This should make its way into our v2.10 release. It's inevitable that we need to store some json schema related information
    on core schemas, given that we generate JSON schemas directly from core schemas. That being said, debugging related
    issues is quite difficult when JSON schema information is disguised via dynamically defined functions.
    """

    pydantic_js_functions: list[GetJsonSchemaFunction]
    pydantic_js_annotation_functions: list[GetJsonSchemaFunction]
    pydantic_js_prefer_positional_arguments: bool | None
    pydantic_js_input_core_schema: CoreSchema | None
    pydantic_js_updates: JsonDict | None
    pydantic_js_extra: JsonDict | JsonSchemaExtraCallable | None
