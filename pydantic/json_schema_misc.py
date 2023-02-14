from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Callable, Dict

from pydantic_core import CoreSchema

JsonSchemaValue = Dict[str, Any]
JsonValue = Dict[str, Any]


@dataclass(kw_only=True)
class JsonSchemaMisc:
    # ### Pre-processing of the JSON schema
    # If not None, this core schema will be used to generate the JSON schema instead of the real one for the field:
    core_schema_override: CoreSchema | None = None
    # A reference to the source class if appropriate, intended for extracting docstrings, etc.
    source_class: type[Any] | None = None

    # ### Overrides for the "miscellaneous properties that are available for all JSON types"
    # ### (see https://json-schema.org/understanding-json-schema/reference/generic.html)
    title: str | None = None
    description: str | None = None
    examples: list[JsonValue] | None = None
    deprecated: bool | None = None
    read_only: bool | None = None
    write_only: bool | None = None
    comment: str | None = None
    # Note: 'default', which is included with these fields in the JSON Schema docs, is handled by CoreSchema

    # ### Post-processing of the JSON schema
    # A catch-all for arbitrary data to add to the schema
    extra_updates: dict[str, Any] | None = None
    # A final function to apply to the JSON schema after all other modifications have been applied
    modify_json_schema: Callable[[JsonSchemaValue], JsonSchemaValue] | None = None

    @classmethod
    def merged(cls, base: JsonSchemaMisc | None, overrides: JsonSchemaMisc | None) -> JsonSchemaMisc | None:
        if base is None:
            return overrides
        if overrides is None:
            return base
        return base.with_updates(overrides)

    def with_updates(self, other: JsonSchemaMisc) -> JsonSchemaMisc:
        changes = {k: v for k, v in asdict(other).items() if v is not None}
        return replace(self, **changes)

    def without_core_schema_override(self) -> JsonSchemaMisc:
        return replace(self, core_schema_override=None)

    def update(self, schema: JsonSchemaValue) -> JsonSchemaValue:
        """
        Update the given JSON schema with the values from this object.

        Note that the "pre-processing" attributes are not used in this method.
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
