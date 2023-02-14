from __future__ import annotations as _annotations

import typing
import warnings
from typing import Any

import typing_extensions
from pydantic_core import CoreSchema
from pydantic_core.core_schema import TypedDictField

from ..json_schema_misc import JsonSchemaMisc
from ._typing_extra import EllipsisType

_UPDATE_CORE_SCHEMA_FIELD = 'pydantic_update_core_schema'
_JSON_SCHEMA_MISC_FIELD = 'pydantic_json_schema_misc'

_CoreMetadata = typing.Dict[str, Any]


class UpdateCoreSchemaCallable(typing_extensions.Protocol):
    def __call__(self, schema: CoreSchema, **kwargs: Any) -> None:
        ...


class HandleCoreMetadata:
    def __init__(self, schema: CoreSchema | TypedDictField):
        self.schema = schema

        metadata = schema.get('metadata')
        if metadata is None:
            schema['metadata'] = metadata = {}
        elif not isinstance(metadata, dict):
            raise ValueError(f'CoreSchema metadata should be a dict; got {metadata!r}.')
        self.metadata: _CoreMetadata = metadata

    @staticmethod
    def build(
        *,  # force keyword arguments to make it easier to modify this signature in a backwards-compatible way
        update_core_schema: UpdateCoreSchemaCallable | None | EllipsisType = ...,
        json_schema_misc: JsonSchemaMisc | None | EllipsisType = ...,
        initial_metadata: Any | None = None,
    ) -> Any:
        if initial_metadata is not None and not isinstance(initial_metadata, dict):
            warnings.warn(
                f'CoreSchema metadata should be a dict or None; cannot augment {initial_metadata}.', UserWarning
            )
            return initial_metadata

        metadata: _CoreMetadata = {} if initial_metadata is None else initial_metadata.copy()

        if update_core_schema is not ...:
            metadata[_UPDATE_CORE_SCHEMA_FIELD] = update_core_schema

        if json_schema_misc is not ...:
            metadata[_JSON_SCHEMA_MISC_FIELD] = json_schema_misc

        return metadata

    def get_update_core_schema(self) -> UpdateCoreSchemaCallable | None:
        return self.metadata.get(_UPDATE_CORE_SCHEMA_FIELD)

    def get_json_schema_misc(self) -> JsonSchemaMisc | None:
        return self.metadata.get(_JSON_SCHEMA_MISC_FIELD)

    def update_json_schema_misc(self, update: JsonSchemaMisc) -> None:
        self.metadata[_JSON_SCHEMA_MISC_FIELD] = JsonSchemaMisc.merged(self.get_json_schema_misc(), update)

    def json_schema_core_schema_override(self) -> CoreSchema | None:
        """
        Shorthand for grabbing the schema override off the JsonSchemaMisc object if present.

        For convenience, if missing, the override schema metadata's json_schema_misc is replaced with this value
        minus the override schema.
        """
        misc = self.get_json_schema_misc()
        if misc is None:
            return None
        if misc.core_schema_override is None:
            return None
        schema = misc.core_schema_override.copy()
        schema['metadata'] = schema.get('metadata') or {}
        HandleCoreMetadata(schema).update_json_schema_misc(misc.without_core_schema_override())

        return schema
