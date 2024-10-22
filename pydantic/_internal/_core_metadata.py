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
        pydantic_js_udpates: key / value pair updates to apply to the JSON schema for a type.
        pydantic_js_extra: WIP, either key/value pair updates to apply to the JSON schema, or a custom callable.

    TODO: Perhaps we should move this structure to pydantic-core. At the moment, though,
    it's easier to iterate on if we leave it in pydantic until we feel there is a semi-stable API.
    We should implement more `cast` calls to enforce these types, though I'm unsure of if there's a way
    to inherently make this compatible with dict[str, Any] effectively as a super type.

    TODO: It's unfortunate how functionally oriented JSON schema generation is, especially that which occurs during
    the core schema generation process. It's inevitable that we need to store some json schema related information
    on core schemas, given that we generate JSON schemas directly from core schemas. That being said, debugging related
    issues is quite difficult when JSON schema information is disguised via dynamically defined functions.

    TODO: add utility function for updating pydantic_js_updates and pydantic_js_extra - not as easy as an append,
    and we want to be consistent about how we do this across files.

    TODO: should we have a separate attribute as we do now for pydantic_js_extra? Can we just override in the case of a callable - think
    about this re breaking change in v2.8 (see currently failing test), basically a dict extra + callable extra no longer works (imo it shouldn't)
    """

    pydantic_js_functions: list[GetJsonSchemaFunction]
    pydantic_js_annotation_functions: list[GetJsonSchemaFunction]
    pydantic_js_prefer_positional_arguments: bool | None
    pydantic_js_input_core_schema: CoreSchema | None
    pydantic_js_updates: JsonDict | None
    pydantic_js_extra: JsonDict | JsonSchemaExtraCallable | None
