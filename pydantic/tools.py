from __future__ import annotations

import json
import warnings
from functools import lru_cache
from typing import Any, Callable, Type, TypeVar, Union

from . import Validator
from ._internal import _repr

__all__ = 'parse_obj_as', 'schema_of', 'schema_json_of'

from ._internal import _generate_schema
from .json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema

NameFactory = Union[str, Callable[[Type[Any]], str]]


def _generate_parsing_type_name(type_: Any) -> str:
    return f'ParsingModel[{_repr.display_as_type(type_)}]'


@lru_cache(maxsize=2048)
def _get_parsing_type(type_: Any, *, type_name: NameFactory | None = None) -> Any:
    from pydantic.main import create_model

    if type_name is None:
        type_name = _generate_parsing_type_name
    if not isinstance(type_name, str):
        type_name = type_name(type_)
    return create_model(type_name, __root__=(type_, ...))


T = TypeVar('T')


def parse_obj_as(type_: type[T], obj: Any, type_name: NameFactory | None = None) -> T:
    if type_name is not None:  # pragma: no cover
        warnings.warn(
            'The type_name parameter is deprecated. parse_obj_as no longer creates temporary models', stacklevel=2
        )
    return Validator(type_)(obj)


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
        core_schema = _generate_schema.GenerateSchema(True, None, None).generate_schema(type_)
    json_schema = json_schema_generator.generate(core_schema)
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
