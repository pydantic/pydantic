from __future__ import annotations as _annotations

from typing import Any, Pattern

from pydantic_core.core_schema import SerializationInfo


def pattern_serializer(input_value: Pattern[Any], info: SerializationInfo) -> str | Pattern[Any]:
    if info.mode == 'json':
        return input_value.pattern
    else:
        return input_value
