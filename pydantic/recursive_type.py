from typing import Any, Callable

from pydantic_core import core_schema

from ._internal import _generate_schema, _internal_dataclass


@_internal_dataclass.slots_dataclass
class RecursiveType:
    name: str

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler(_generate_schema._RecursiveTypeWrapper(source_type, self.name))
        return schema
