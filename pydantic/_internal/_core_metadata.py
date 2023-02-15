from __future__ import annotations as _annotations

import typing
import warnings
from typing import Any

import typing_extensions
from pydantic_core import CoreSchema
from pydantic_core.core_schema import TypedDictField

from ..json_schema_misc import JsonSchemaMisc, JsonSchemaValue
from ._typing_extra import EllipsisType

_UPDATE_CORE_SCHEMA_FIELD = 'pydantic_update_core_schema'
_JSON_SCHEMA_MISC_FIELD = 'pydantic_json_schema_misc'

_CoreMetadata = typing.Dict[str, Any]


class UpdateCoreSchemaCallable(typing_extensions.Protocol):
    def __call__(self, schema: CoreSchema, **kwargs: Any) -> None:
        ...


class CoreMetadataHandler:
    """
    Because the metadata field in pydantic_core is of type `Any`, we can't assume much about its contents.

    This class is used to interact with the metadata field on a CoreSchema object in a consistent
    way throughout pydantic.
    """

    def __init__(self, schema: CoreSchema | TypedDictField):
        self.schema = schema

        metadata = schema.get('metadata')
        if metadata is None:
            schema['metadata'] = {}
        elif not isinstance(metadata, dict):
            raise ValueError(f'CoreSchema metadata should be a dict; got {metadata!r}.')

    @property
    def metadata(self) -> _CoreMetadata:
        metadata = self.schema.get('metadata')
        if metadata is None:
            self.schema['metadata'] = metadata = {}
        if not isinstance(metadata, dict):
            raise ValueError(f'CoreSchema metadata should be a dict; got {metadata!r}.')
        return metadata

    @property
    def update_core_schema(self) -> UpdateCoreSchemaCallable | None:
        return self.metadata.get(_UPDATE_CORE_SCHEMA_FIELD)

    @update_core_schema.setter
    def update_core_schema(self, value: UpdateCoreSchemaCallable | None) -> None:
        self.metadata[_UPDATE_CORE_SCHEMA_FIELD] = value

    @property
    def json_schema_misc(self) -> JsonSchemaMisc | None:
        return self.metadata.get(_JSON_SCHEMA_MISC_FIELD)

    @json_schema_misc.setter
    def json_schema_misc(self, value: JsonSchemaMisc | None) -> None:
        self.metadata[_JSON_SCHEMA_MISC_FIELD] = value

    def merge_json_schema_misc(self, update: JsonSchemaMisc) -> None:
        """
        Given a JsonSchemaMisc object, merge it into the wrapped schema's metadata.
        """
        self.metadata[_JSON_SCHEMA_MISC_FIELD] = JsonSchemaMisc.merged(self.json_schema_misc, update)

    def get_json_schema_core_schema_override(self) -> CoreSchema | None:
        """
        Returns the core_schema_override off the JsonSchemaMisc object if it is present,
        merging in the json_schema_misc if present on the wrapped schema.
        """
        misc = self.json_schema_misc
        if misc is None:
            return None
        if misc.core_schema_override is None:
            return None

        # Create a copy so we don't modify the original schema
        schema = misc.core_schema_override.copy()
        metadata_handler = CoreMetadataHandler(schema)

        # Merge in the json_schema_misc (without the core_schema_override, to prevent recursion)
        #
        # By merging the json_schema_misc like this, we ensure that you don't have to
        # manually merge the json_schema_misc into the core_schema_override when generating
        # the core schema.
        metadata_handler.merge_json_schema_misc(misc.without_core_schema_override())

        return schema

    def get_source_class(self) -> type[Any] | None:
        """
        Returns the source class off the JsonSchemaMisc object if it is present.
        """
        misc = self.json_schema_misc
        if misc is None:
            return None
        return misc.source_class

    def get_modify_json_schema(self) -> typing.Callable[[JsonSchemaValue], JsonSchemaValue] | None:
        """
        Returns the modify_json_schema off the JsonSchemaMisc object if it is present.
        """
        misc = self.json_schema_misc
        if misc is None:
            return None
        return misc.modify_json_schema


def build_metadata_dict(
    *,  # force keyword arguments to make it easier to modify this signature in a backwards-compatible way
    update_core_schema: UpdateCoreSchemaCallable | None | EllipsisType = ...,
    json_schema_misc: JsonSchemaMisc | None | EllipsisType = ...,
    initial_metadata: Any | None = None,
) -> Any:
    """
    Builds a dict to use as the metadata field of a CoreSchema object in a manner that is consistent
    with the CoreMetadataHandler class.
    """
    if initial_metadata is not None and not isinstance(initial_metadata, dict):
        warnings.warn(f'CoreSchema metadata should be a dict or None; cannot augment {initial_metadata}.', UserWarning)
        return initial_metadata

    metadata: _CoreMetadata = {} if initial_metadata is None else initial_metadata.copy()

    if update_core_schema is not ...:
        metadata[_UPDATE_CORE_SCHEMA_FIELD] = update_core_schema

    if json_schema_misc is not ...:
        metadata[_JSON_SCHEMA_MISC_FIELD] = json_schema_misc

    return metadata
