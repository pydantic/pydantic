
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
import functools
from typing import Any, Mapping, cast, overload
from .._types import NotGiven

def is_mapping(obj: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(obj, Mapping)

def is_list(obj: object) -> TypeGuard[list[object]]:
    return isinstance(obj, list)

@overload
def strip_not_given(obj: None) -> None:
    ...

@overload
def strip_not_given(obj: Mapping[_K, _V | NotGiven]) -> dict[_K, _V]:
    ...

@overload
def strip_not_given(obj: object) -> object:
    ...

def strip_not_given(obj: object | None) -> object:
    if obj is None:
        return None
    if not is_mapping(obj):
        return obj
    return {key: value for key, value in obj.items() if not isinstance(value, NotGiven)}

def coerce_boolean(val: str) -> bool:
    return val == 'true' or val == '1' or val == 'on'

def lru_cache(*, maxsize: int | None=128) -> Callable[[CallableT], CallableT]:
    wrapper = functools.lru_cache(maxsize=maxsize)
    return cast(Any, wrapper)
