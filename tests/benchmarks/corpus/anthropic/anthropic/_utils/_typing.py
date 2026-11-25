
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
import sys
import typing
import typing_extensions
from typing import cast
from typing_extensions import Required, Annotated, get_args, get_origin
from ._utils import lru_cache

def is_annotated_type(typ: type) -> bool:
    return get_origin(typ) == Annotated

def is_required_type(typ: type) -> bool:
    return get_origin(typ) == Required
_TYPE_ALIAS_TYPES: tuple[type[typing_extensions.TypeAliasType], ...] = (typing_extensions.TypeAliasType,)
if sys.version_info >= (3, 12):
    _TYPE_ALIAS_TYPES = (*_TYPE_ALIAS_TYPES, typing.TypeAliasType)

def is_type_alias_type(tp: Any, /) -> TypeIs[typing_extensions.TypeAliasType]:
    return isinstance(tp, _TYPE_ALIAS_TYPES)

@lru_cache(maxsize=8096)
def strip_annotated_type(typ: type) -> type:
    if is_required_type(typ) or is_annotated_type(typ):
        return strip_annotated_type(cast(type, get_args(typ)[0]))
    return typ

def extract_type_arg(typ: type, index: int) -> type:
    args = get_args(typ)
    try:
        return cast(type, args[index])
    except IndexError as err:
        raise RuntimeError(f'Expected type {typ} to have a type argument at index {index} but it did not') from err
