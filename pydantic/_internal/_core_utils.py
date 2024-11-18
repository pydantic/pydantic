from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Union

from pydantic_core import CoreSchema, core_schema
from pydantic_core import validate_core_schema as _validate_core_schema
from typing_extensions import TypeGuard, get_args, get_origin

from . import _repr
from ._typing_extra import is_generic_alias, is_type_alias_type

FunctionSchemaWithInnerSchema = Union[
    core_schema.AfterValidatorFunctionSchema,
    core_schema.BeforeValidatorFunctionSchema,
    core_schema.WrapValidatorFunctionSchema,
]

CoreSchemaField = Union[
    core_schema.ModelField, core_schema.DataclassField, core_schema.TypedDictField, core_schema.ComputedField
]
CoreSchemaOrField = Union[core_schema.CoreSchema, CoreSchemaField]

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


def is_list_like_schema_with_items_schema(
    schema: CoreSchema,
) -> TypeGuard[core_schema.ListSchema | core_schema.SetSchema | core_schema.FrozenSetSchema]:
    return schema['type'] in _LIST_LIKE_SCHEMA_WITH_ITEMS_TYPES


def get_type_ref(type_: type[Any], args_override: tuple[type[Any], ...] | None = None) -> str:
    """Produces the ref to be used for this type by pydantic_core's core schemas.

    This `args_override` argument was added for the purpose of creating valid recursive references
    when creating generic models without needing to create a concrete class.
    """
    origin = get_origin(type_) or type_

    args = get_args(type_) if is_generic_alias(type_) else (args_override or ())
    generic_metadata = getattr(type_, '__pydantic_generic_metadata__', None)
    if generic_metadata:
        origin = generic_metadata['origin'] or origin
        args = generic_metadata['args'] or args

    module_name = getattr(origin, '__module__', '<No __module__>')
    if is_type_alias_type(origin):
        type_ref = f'{module_name}.{origin.__name__}:{id(origin)}'
    else:
        try:
            qualname = getattr(origin, '__qualname__', f'<No __qualname__: {origin}>')
        except Exception:
            qualname = getattr(origin, '__qualname__', '<No __qualname__>')
        type_ref = f'{module_name}.{qualname}:{id(origin)}'

    arg_refs: list[str] = []
    for arg in args:
        if isinstance(arg, str):
            # Handle string literals as a special case; we may be able to remove this special handling if we
            # wrap them in a ForwardRef at some point.
            arg_ref = f'{arg}:str-{id(arg)}'
        else:
            arg_ref = f'{_repr.display_as_type(arg)}:{id(arg)}'
        arg_refs.append(arg_ref)
    if arg_refs:
        type_ref = f'{type_ref}[{",".join(arg_refs)}]'
    return type_ref


def _print_strip_metadata(s: dict[str, Any]) -> None:
    s.pop('metadata', None)
    if s.get('type') == 'model-fields':
        if not s.get('computed_fields', None):
            s.pop('computed_fields', None)
    elif s.get('type') == 'model':
        # remove some defaults
        if s.get('custom_init', True) is False:
            s.pop('custom_init')
        if s.get('root_model', True) is False:
            s.pop('root_model')
        if {'title'}.issuperset(s.get('config', {}).keys()):
            s.pop('config', None)


def _print_strip_metadata_recursively(val: Any) -> None:
    if isinstance(val, dict):
        for v in val.values():
            _print_strip_metadata_recursively(v)
        _print_strip_metadata(val)  # type: ignore
    elif isinstance(val, list):
        for v in val:
            _print_strip_metadata_recursively(v)


def pretty_print_core_schema(
    schema: CoreSchema,
    include_metadata: bool = False,
) -> None:
    """Pretty print a CoreSchema using rich.
    This is intended for debugging purposes.

    Args:
        schema: The CoreSchema to print.
        include_metadata: Whether to include metadata in the output. Defaults to `False`.
    """
    from rich import print  # type: ignore  # install it manually in your dev env

    if not include_metadata:
        schema = deepcopy(schema)
        _print_strip_metadata_recursively(schema)

    return print(schema)


def validate_core_schema(schema: CoreSchema) -> CoreSchema:
    if 'PYDANTIC_SKIP_VALIDATING_CORE_SCHEMAS' in os.environ:
        return schema
    return _validate_core_schema(schema)
