from __future__ import annotations as _annotations

from collections import deque
from typing import Any, Pattern

from pydantic_core import PydanticOmit
from pydantic_core.core_schema import SerializationInfo, SerializerFunctionWrapHandler


def pattern_serializer(input_value: Pattern[Any], info: SerializationInfo) -> str | Pattern[Any]:
    if info.mode == 'json':
        return input_value.pattern
    else:
        return input_value


def serialize_deque(
    __value: Any, __serialize: SerializerFunctionWrapHandler, __info: SerializationInfo
) -> list[Any] | deque[Any]:
    items = []
    for index, item in enumerate(__value):
        try:
            v = __serialize(item, index)
        except PydanticOmit:
            pass
        else:
            items.append(v)
    if __info.mode_is_json():
        return items
    else:
        return deque(items)
