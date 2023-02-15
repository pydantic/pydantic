from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Callable, Dict

from pydantic_core import CoreSchema

from pydantic._internal._utils import dict_not_none

JsonSchemaValue = Dict[str, Any]
JsonValue = Dict[str, Any]


@dataclass
class JsonSchemaMisc:
    # ### "Pre-processing" of the JSON schema
    # If not None, this CoreSchema will be used to generate the JSON schema instead of the "real one":
    core_schema_override: CoreSchema | None = None

    # ### "Miscellaneous properties" that are available for all JSON types
    # (see https://json-schema.org/understanding-json-schema/reference/generic.html)
    title: str | None = None
    description: str | None = None
    examples: list[JsonValue] | None = None
    deprecated: bool | None = None
    read_only: bool | None = None
    write_only: bool | None = None
    comment: str | None = None
    # Note: 'default', which is included with these fields in the JSON Schema docs, is handled by CoreSchema

    # ### "Post-processing" of the JSON schema
    # A catch-all for arbitrary data to add to the schema
    extra_updates: dict[str, Any] | None = None
    # A final function to apply to the JSON schema after all other modifications have been applied
    # If you want to force specific contents in the generated schema, you can use a function that ignores the
    # input value and just return the schema you want.
    modify_json_schema: Callable[[JsonSchemaValue], JsonSchemaValue] | None = None

    @classmethod
    def merged(cls, base: JsonSchemaMisc | None, overrides: JsonSchemaMisc | None) -> JsonSchemaMisc | None:
        """
        Merge two JsonSchemaMisc objects, with the values from the second overriding the first.

        Returns a new object, or None if both arguments are None. The provided objects are not modified.
        """
        if base is None:
            return replace(overrides)
        if overrides is None:
            return replace(base)
        return base.with_updates(overrides)

    def with_updates(self, other: JsonSchemaMisc) -> JsonSchemaMisc:
        """
        Replace the values in this object with the non-None values from the provided object.
        A new object is returned, and neither input is modified.
        """
        changes = dict_not_none(asdict(other))
        return replace(self, **changes)

    def without_core_schema_override(self) -> JsonSchemaMisc:
        """
        Return a copy of this object without the core_schema_override; when handling the core_schema_override,
        we need to remove it from the object so that the handler doesn't recurse infinitely.
        """
        return replace(self, core_schema_override=None)

    def apply_updates(self, schema: JsonSchemaValue) -> JsonSchemaValue:
        """
        Update the provided JSON schema in-place with the values from this object.

        Note that the "pre-processing" attributes are not used in this method and must be used separately.
        """
        if self.title is not None:
            schema['title'] = self.title
        if self.description is not None:
            schema['description'] = self.description
        if self.examples is not None:
            schema['examples'] = self.examples
        if self.deprecated is not None:
            schema['deprecated'] = self.deprecated
        if self.read_only is not None:
            schema['readOnly'] = self.read_only
        if self.write_only is not None:
            schema['writeOnly'] = self.write_only
        if self.comment is not None:
            schema['$comment'] = self.comment
        if self.extra_updates is not None:
            schema.update(self.extra_updates)
        if self.modify_json_schema is not None:
            schema = self.modify_json_schema(schema)
        return schema
