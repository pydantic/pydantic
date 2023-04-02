from __future__ import annotations

import json
import warnings
from typing import Any, Callable, Type, TypeVar, Union

from . import AnalyzedType

__all__ = 'parse_obj_as', 'schema_of', 'schema_json_of'

from ._internal import _generate_schema
from .json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema

NameFactory = Union[str, Callable[[Type[Any]], str]]


T = TypeVar('T')


def parse_obj_as(type_: type[T], obj: Any, type_name: NameFactory | None = None) -> T:
    # TODO: add deprecation warning of some sort
    if type_name is not None:  # pragma: no cover
        warnings.warn(
            'The type_name parameter is deprecated. parse_obj_as no longer creates temporary models', stacklevel=2
        )
    return AnalyzedType(type_).validate_python(obj)


def schema_of(
    type_: Any,
    *,
    title: NameFactory | None = None,
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> dict[str, Any]:
    """Generate a JSON schema (as dict) for the passed model or dynamically generated one"""
    json_schema_generator = schema_generator(by_alias=by_alias, ref_template=ref_template)
    if hasattr(type_, '__pydantic_core_schema__'):
        core_schema = type_.__pydantic_core_schema__
    else:
        core_schema = _generate_schema.GenerateSchema(True, None).generate_schema(type_)
    json_schema = json_schema_generator.generate(core_schema)
    if title is not None:
        json_schema['title'] = title
    return json_schema


def schema_json_of(
    type_: Any,
    *,
    title: NameFactory | None = None,
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    **dumps_kwargs: Any,
) -> str:
    """Generate a JSON schema (as JSON) for the passed model or dynamically generated one"""
    return json.dumps(
        schema_of(type_, title=title, by_alias=by_alias, ref_template=ref_template, schema_generator=schema_generator),
        **dumps_kwargs,
    )
