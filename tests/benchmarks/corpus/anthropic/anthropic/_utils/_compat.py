
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
import sys
import typing_extensions
from typing import Union, Literal
from typing_extensions import get_args as _get_args, get_origin as _get_origin
_LITERAL_TYPES = {Literal, typing_extensions.Literal}

def get_args(tp: type[Any]) -> tuple[Any, ...]:
    return _get_args(tp)

def get_origin(tp: type[Any]) -> type[Any] | None:
    return _get_origin(tp)

def is_union(tp: Optional[Type[Any]]) -> bool:
    if sys.version_info < (3, 10):
        return tp is Union
    else:
        import types
        return tp is Union or tp is types.UnionType

def is_literal_type(tp: Type[Any]) -> bool:
    return get_origin(tp) in _LITERAL_TYPES
