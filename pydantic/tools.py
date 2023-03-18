import warnings
from collections.abc import Callable
from functools import lru_cache
from typing import Any, TypeVar, Union

from . import Validator
from ._internal import _repr

__all__ = 'parse_obj_as', 'schema_of', 'schema_json_of'

NameFactory = Union[str, Callable[[type[Any]], str]]


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
            'The type_name parameter is deprecated. parse_obj_as not longer creates temporary models', stacklevel=2
        )
    return Validator(type_)(obj)


def schema_of(type_: Any, *, title: NameFactory | None = None, **schema_kwargs: Any) -> 'dict[str, Any]':
    """Generate a JSON schema (as dict) for the passed model or dynamically generated one"""
    return _get_parsing_type(type_, type_name=title).model_json_schema(**schema_kwargs)


def schema_json_of(type_: Any, *, title: NameFactory | None = None, **schema_json_kwargs: Any) -> str:
    """Generate a JSON schema (as JSON) for the passed model or dynamically generated one"""
    return _get_parsing_type(type_, type_name=title).schema_json(**schema_json_kwargs)
