from __future__ import annotations as _annotations

import inspect
import typing
from typing import Any

import typing_extensions
from pydantic_core import CoreSchema
from pydantic_core.core_schema import TypedDictField

from ._typing_extra import EllipsisType

if typing.TYPE_CHECKING:
    from ..json_schema import JsonSchemaMetadata, JsonSchemaValue


# CS is shorthand for Core Schema
# JS is shorthand for JSON Schema
_UPDATE_CS_FUNCTION_FIELD = 'pydantic_update_core_schema_function'
_JS_METADATA_FIELD = 'pydantic_json_schema_metadata'

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

    __slots__ = ('_schema',)

    def __init__(self, schema: CoreSchema | TypedDictField):
        self._schema = schema

        try:
            metadata = schema.get('metadata')
        except AttributeError:  # This happens for schema of type _fields.SelfType
            # TODO: Need to figure out a better way to handle _fields.SelfType
            #   Solution?: Adding `definitions` into pydantic_core
            metadata = {}

        if metadata is None:
            schema['metadata'] = {}
        elif not isinstance(metadata, dict):
            raise TypeError(f'CoreSchema metadata should be a dict; got {metadata!r}.')

    @property
    def metadata(self) -> _CoreMetadata:
        """
        Retrieves the metadata dict off the schema, initializing it to a dict if necessary,
        and raise an error if it is not a dict.
        """
        metadata = self._schema.get('metadata')
        if metadata is None:
            self._schema['metadata'] = metadata = {}
        if not isinstance(metadata, dict):
            raise TypeError(f'CoreSchema metadata should be a dict; got {metadata!r}.')
        return metadata

    @property
    def update_cs_function(self) -> UpdateCoreSchemaCallable | None:
        """
        Retrieves the function that will be used to update the CoreSchema.
        This is generally obtained from a `__pydantic_update_schema__` function
        """
        return self.metadata.get(_UPDATE_CS_FUNCTION_FIELD)

    @update_cs_function.setter
    def update_cs_function(self, value: UpdateCoreSchemaCallable | None) -> None:
        """
        Sets the update_cs_function on the wrapped schema, providing a clean API even when
        the wrapped schema had metadata set to None
        """
        self.metadata[_UPDATE_CS_FUNCTION_FIELD] = value

    @property
    def json_schema_metadata(self) -> JsonSchemaMetadata | None:
        """
        Retrieves the JsonSchemaMetadata instance out of the wrapped schema's metadata
        """
        return self.metadata.get(_JS_METADATA_FIELD)

    @json_schema_metadata.setter
    def json_schema_metadata(self, value: JsonSchemaMetadata | None) -> None:
        """
        Sets the JsonSchemaMetadata on the wrapped schema, providing a clean API even when
        the wrapped schema had metadata set to None
        """
        self.metadata[_JS_METADATA_FIELD] = value

    def merge_json_schema_metadata(self, update: JsonSchemaMetadata) -> None:
        """
        Given a JsonSchemaMetadata object, merge it into the wrapped schema's metadata.
        """
        from pydantic.json_schema import merge_js_metadata

        self.metadata[_JS_METADATA_FIELD] = merge_js_metadata(self.json_schema_metadata, update)

    def get_json_schema_core_schema_override(self) -> CoreSchema | None:
        """
        Returns the core_schema_override off the JsonSchemaMetadata object if it is present,
        merging in the json_schema_metadata if present on the wrapped schema.
        """
        metadata = self.json_schema_metadata
        if metadata is None:
            return None
        core_schema_override = metadata.get('core_schema_override')
        if core_schema_override is None:
            return None
        if inspect.isfunction(core_schema_override):
            # Perform deferred schema evaluation
            schema = core_schema_override()
        else:
            # Create a copy so we don't modify the original schema
            schema = typing.cast(CoreSchema, core_schema_override).copy()

        metadata_handler = CoreMetadataHandler(schema)

        # Merge in the json_schema_metadata (without the core_schema_override, to prevent recursion)
        #
        # By merging the json_schema_metadata like this, we ensure that you don't have to
        # manually merge the json_schema_metadata into the core_schema_override when generating
        # the core schema.
        from pydantic.json_schema import without_core_schema_override

        metadata_handler.merge_json_schema_metadata(without_core_schema_override(metadata))

        return schema

    def get_source_class(self) -> type[Any] | None:
        """
        Returns the source class off the JsonSchemaMetadata object if it is present.
        """
        misc = self.json_schema_metadata
        if misc is None:
            return None
        return misc.get('source_class')

    def get_modify_js_function(self) -> typing.Callable[[JsonSchemaValue], None] | None:
        """
        Returns the modify_js_function off the JsonSchemaMetadata object if it is present.
        """
        misc = self.json_schema_metadata
        if misc is None:
            return None
        return misc.get('modify_js_function')

    def combine_modify_js_functions(
        self, modify_js_function: typing.Callable[[JsonSchemaValue], None] | None, before: bool = True
    ) -> None:
        """
        Composes the provided modify_js_function with the existing modify_js_function.

        This operation is performed in-place and modifies the wrapped schema's metadata.

        If before is True, the provided modify_js_function will be called first.
        """
        if modify_js_function is None:
            return  # nothing to do

        metadata = self.json_schema_metadata

        if metadata is None:
            self.json_schema_metadata = {'modify_js_function': modify_js_function}
        else:
            original_modify = metadata.get('modify_js_function')
            if original_modify is None:
                metadata['modify_js_function'] = modify_js_function
            else:

                def combined_modify_js_function(schema: JsonSchemaValue) -> None:
                    assert original_modify is not None  # for mypy
                    assert modify_js_function is not None  # for mypy
                    if before:
                        modify_js_function(schema)
                    original_modify(schema)
                    if not before:
                        modify_js_function(schema)

                metadata['modify_js_function'] = combined_modify_js_function


def build_metadata_dict(
    *,  # force keyword arguments to make it easier to modify this signature in a backwards-compatible way
    update_cs_function: UpdateCoreSchemaCallable | None | EllipsisType = ...,
    js_metadata: JsonSchemaMetadata | None | EllipsisType = ...,
    initial_metadata: Any | None = None,
) -> Any:
    """
    Builds a dict to use as the metadata field of a CoreSchema object in a manner that is consistent
    with the CoreMetadataHandler class.
    """
    if initial_metadata is not None and not isinstance(initial_metadata, dict):
        raise TypeError(f'CoreSchema metadata should be a dict; got {initial_metadata!r}.')

    metadata: _CoreMetadata = {} if initial_metadata is None else initial_metadata.copy()

    if update_cs_function is not ...:
        metadata[_UPDATE_CS_FUNCTION_FIELD] = update_cs_function

    if js_metadata is not ...:
        metadata[_JS_METADATA_FIELD] = js_metadata

    return metadata
