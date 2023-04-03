from __future__ import annotations as _annotations

import inspect
import typing
import warnings
from typing import Any

import typing_extensions
from pydantic_core import CoreSchema, core_schema

if typing.TYPE_CHECKING:
    from ..json_schema import JsonSchemaValue


# CS is shorthand for Core Schema
# JS is shorthand for JSON Schema
_CS_UPDATE_FUNCTION_FIELD = 'pydantic_cs_update_function'
_JS_OVERRIDE_FIELD = 'pydantic_js_override'
_JS_CS_OVERRIDE_FIELD = 'pydantic_js_cs_override'
_JS_MODIFY_FUNCTION_FIELD = 'pydantic_js_modify_function'
_JS_PREFER_POSITIONAL_ARGUMENTS_FIELD = 'pydantic_js_prefer_positional_arguments'

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

    def __init__(self, schema: CoreSchema | core_schema.TypedDictField | core_schema.DataclassField):
        self._schema = schema

        metadata = schema.get('metadata')
        if metadata is None:
            schema['metadata'] = {}
        elif not isinstance(metadata, dict):
            raise TypeError(f'CoreSchema metadata should be a dict; got {metadata!r}.')

    @property
    def _metadata(self) -> _CoreMetadata:
        """
        Retrieves the metadata dict off the schema, initializing it to a dict if it is None
        and raises an error if it is not a dict.
        """
        metadata = self._schema.get('metadata')
        if metadata is None:
            self._schema['metadata'] = metadata = {}
        if not isinstance(metadata, dict):
            raise TypeError(f'CoreSchema metadata should be a dict; got {metadata!r}.')
        return metadata

    @property
    def cs_update_function(self) -> UpdateCoreSchemaCallable | None:
        """
        Retrieves the function that will be used to update the CoreSchema.
        This is generally obtained from a `__pydantic_update_schema__` function
        """
        return self._metadata.get(_CS_UPDATE_FUNCTION_FIELD)

    @property
    def js_override(self) -> JsonSchemaValue | None:
        """
        The js_override, if present, is used instead of performing JSON schema generation for this core schema.
        """
        js_override = self._metadata.get(_JS_OVERRIDE_FIELD)
        if inspect.isfunction(js_override):
            return js_override()
        return js_override

    @property
    def js_cs_override(self) -> CoreSchema | None:
        """
        The js_cs_override, if present, is used as the input schema for JSON schema generation in place
        of this schema. This will be ignored if js_override is present.
        """
        core_schema_override = self._metadata.get(_JS_CS_OVERRIDE_FIELD)
        if inspect.isfunction(core_schema_override):
            return core_schema_override()
        return core_schema_override

    @property
    def js_modify_function(self) -> typing.Callable[[JsonSchemaValue], JsonSchemaValue] | None:
        """
        The js_modify_function, if present, is called after generating the JSON schema.
        This is still called on the js_override if that is present, and is also called
        on the result of generating for the js_cs_override if that is present.
        """
        return self._metadata.get(_JS_MODIFY_FUNCTION_FIELD)

    @property
    def js_prefer_positional_arguments(self) -> bool | None:
        """
        If True, the JSON schema generator will prefer positional over keyword arguments for an 'arguments' schema.
        """
        return self._metadata.get(_JS_PREFER_POSITIONAL_ARGUMENTS_FIELD)

    def compose_js_modify_functions(
        self, js_modify_function: typing.Callable[[JsonSchemaValue], JsonSchemaValue] | None, inner: bool = False
    ) -> None:
        """
        Composes the provided js_modify_function with the existing js_modify_function.

        This operation is performed in-place and modifies the wrapped schema's metadata.

        If `inner` is True, the provided js_modify_function will be called on the input schema first.
        """

        if inner:
            outer_func, inner_func = self.js_modify_function, js_modify_function
        else:
            outer_func, inner_func = js_modify_function, self.js_modify_function

        self._metadata[_JS_MODIFY_FUNCTION_FIELD] = compose_js_modify_functions(outer_func, inner_func)

    def apply_js_modify_function(self, schema: JsonSchemaValue) -> JsonSchemaValue:
        """
        Return the result of calling the js_modify_function on the provided JSON schema.
        """
        js_modify_function = self.js_modify_function
        if js_modify_function is None:
            return schema

        modified_schema = js_modify_function(schema)
        if modified_schema is None:
            warnings.warn(
                f'JSON schema modification function {js_modify_function} returned None; it should return a schema',
                UserWarning,
            )
            modified_schema = schema
        return modified_schema


def build_metadata_dict(
    *,  # force keyword arguments to make it easier to modify this signature in a backwards-compatible way
    cs_update_function: UpdateCoreSchemaCallable | None = None,
    js_override: JsonSchemaValue | typing.Callable[[], JsonSchemaValue] | None = None,
    js_cs_override: CoreSchema | typing.Callable[[], CoreSchema] | None = None,
    js_modify_function: typing.Callable[[JsonSchemaValue], JsonSchemaValue] | None = None,
    js_prefer_positional_arguments: bool | None = None,
    initial_metadata: Any | None = None,
) -> Any:
    """
    Builds a dict to use as the metadata field of a CoreSchema object in a manner that is consistent
    with the CoreMetadataHandler class.
    """
    if initial_metadata is not None and not isinstance(initial_metadata, dict):
        raise TypeError(f'CoreSchema metadata should be a dict; got {initial_metadata!r}.')

    metadata = {
        _CS_UPDATE_FUNCTION_FIELD: cs_update_function,
        _JS_OVERRIDE_FIELD: js_override,
        _JS_CS_OVERRIDE_FIELD: js_cs_override,
        _JS_MODIFY_FUNCTION_FIELD: js_modify_function,
        _JS_PREFER_POSITIONAL_ARGUMENTS_FIELD: js_prefer_positional_arguments,
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    if initial_metadata is not None:
        metadata = {**initial_metadata, **metadata}

    return metadata


def compose_js_modify_functions(
    outer: typing.Callable[[JsonSchemaValue], JsonSchemaValue] | None,
    inner: typing.Callable[[JsonSchemaValue], JsonSchemaValue] | None,
) -> typing.Callable[[JsonSchemaValue], JsonSchemaValue] | None:
    """
    Composes the provided `outer` and `inner` js_modify_functions.

    The `outer` function will be called on the result of calling the `inner` function on the provided schema.
    """
    if outer is None:
        return inner
    if inner is None:
        return outer

    def combined_js_modify_function(schema: JsonSchemaValue) -> JsonSchemaValue:
        assert outer is not None and inner is not None  # for mypy
        return outer(inner(schema))

    return combined_js_modify_function
