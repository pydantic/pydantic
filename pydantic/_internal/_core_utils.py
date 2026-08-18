from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypeAlias, TypeGuard

from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
    from rich.console import Console

AnyFunctionSchema: TypeAlias = (
    core_schema.AfterValidatorFunctionSchema
    | core_schema.BeforeValidatorFunctionSchema
    | core_schema.WrapValidatorFunctionSchema
    | core_schema.PlainValidatorFunctionSchema
)


FunctionSchemaWithInnerSchema: TypeAlias = (
    core_schema.AfterValidatorFunctionSchema
    | core_schema.BeforeValidatorFunctionSchema
    | core_schema.WrapValidatorFunctionSchema
)


CoreSchemaField: TypeAlias = (
    core_schema.ModelField | core_schema.DataclassField | core_schema.TypedDictField | core_schema.ComputedField
)

CoreSchemaOrField: TypeAlias = core_schema.CoreSchema | CoreSchemaField

_CORE_SCHEMA_FIELD_TYPES = {'typed-dict-field', 'dataclass-field', 'model-field', 'computed-field'}
_FUNCTION_WITH_INNER_SCHEMA_TYPES = {'function-before', 'function-after', 'function-wrap'}
_LIST_LIKE_SCHEMA_WITH_ITEMS_TYPES = {'list', 'set', 'frozenset'}


def is_core_schema(
    schema: CoreSchemaOrField,
) -> TypeGuard[CoreSchema]:
    return schema['type'] not in _CORE_SCHEMA_FIELD_TYPES


def is_core_schema_field(
    schema: CoreSchemaOrField,
) -> TypeGuard[CoreSchemaField]:
    return schema['type'] in _CORE_SCHEMA_FIELD_TYPES


def is_function_with_inner_schema(
    schema: CoreSchemaOrField,
) -> TypeGuard[FunctionSchemaWithInnerSchema]:
    return schema['type'] in _FUNCTION_WITH_INNER_SCHEMA_TYPES


def as_ser_schema(schema: CoreSchema) -> core_schema.SerSchema:
    """Return a schema suitable for the `'serialization'` key of a core schema, from an arbitrary core schema.

    Any core schema can be used as a serialization schema, except `'function-plain'` and `'function-wrap'`
    schemas, as these types are already used by the plain and wrap serializer *function* schemas.
    For these, mimic what pydantic-core would do if they were used as the *main* schema:

    - if the function schema has a `'serialization'` schema, use it.
    - otherwise, a `'function-plain'` schema is serialized as `'any'`, and a `'function-wrap'` schema
      is serialized using its inner schema.

    Note that `schema` is expected to be a *core* schema (e.g. as returned by the schema generator),
    not an existing `'serialization'` schema.
    """
    if schema['type'] == 'function-plain' or schema['type'] == 'function-wrap':
        if (ser_schema := schema.get('serialization')) is not None:
            return ser_schema
        if schema['type'] == 'function-plain':
            return core_schema.any_schema()
        return as_ser_schema(schema['schema'])
    return schema


def is_list_like_schema_with_items_schema(
    schema: CoreSchema,
) -> TypeGuard[core_schema.ListSchema | core_schema.SetSchema | core_schema.FrozenSetSchema]:
    return schema['type'] in _LIST_LIKE_SCHEMA_WITH_ITEMS_TYPES


def get_ref(s: core_schema.CoreSchema) -> None | str:
    """Get the ref from the schema if it has one.
    This exists just for type checking to work correctly.
    """
    return s.get('ref', None)


def _clean_schema_for_pretty_print(obj: Any, strip_metadata: bool = True) -> Any:  # pragma: no cover
    """A utility function to remove irrelevant information from a core schema."""
    if isinstance(obj, Mapping):
        new_dct = {}
        for k, v in obj.items():
            if k == 'metadata' and strip_metadata:
                new_metadata = {}

                for meta_k, meta_v in v.items():
                    if meta_k in ('pydantic_js_functions', 'pydantic_js_annotation_functions'):
                        new_metadata['js_metadata'] = '<stripped>'
                    else:
                        new_metadata[meta_k] = _clean_schema_for_pretty_print(meta_v, strip_metadata=strip_metadata)

                if list(new_metadata.keys()) == ['js_metadata']:
                    new_metadata = {'<stripped>'}

                new_dct[k] = new_metadata
            # Remove some defaults:
            elif k in ('custom_init', 'root_model') and not v:
                continue
            else:
                new_dct[k] = _clean_schema_for_pretty_print(v, strip_metadata=strip_metadata)

        return new_dct
    elif isinstance(obj, Sequence) and not isinstance(obj, str):
        return [_clean_schema_for_pretty_print(v, strip_metadata=strip_metadata) for v in obj]
    else:
        return obj


def pretty_print_core_schema(
    val: Any,
    *,
    console: Console | None = None,
    max_depth: int | None = None,
    strip_metadata: bool = True,
) -> None:  # pragma: no cover
    """Pretty-print a core schema using the `rich` library.

    Args:
        val: The core schema to print, or a Pydantic model/dataclass/type adapter
            (in which case the cached core schema is fetched and printed).
        console: A rich console to use when printing. Defaults to the global rich console instance.
        max_depth: The number of nesting levels which may be printed.
        strip_metadata: Whether to strip metadata in the output. If `True` any known core metadata
            attributes will be stripped (but custom attributes are kept). Defaults to `True`.
    """
    # lazy import:
    from rich.pretty import pprint

    # circ. imports:
    from pydantic import BaseModel, TypeAdapter
    from pydantic.dataclasses import is_pydantic_dataclass

    if (inspect.isclass(val) and issubclass(val, BaseModel)) or is_pydantic_dataclass(val):
        val = val.__pydantic_core_schema__
    if isinstance(val, TypeAdapter):
        val = val.core_schema
    cleaned_schema = _clean_schema_for_pretty_print(val, strip_metadata=strip_metadata)

    pprint(cleaned_schema, console=console, max_depth=max_depth)


pps = pretty_print_core_schema
