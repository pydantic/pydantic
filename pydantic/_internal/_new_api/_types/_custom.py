from __future__ import annotations

from typing import TYPE_CHECKING, Any


from .._type_handlers import TypeHandler
from .._custom_type_schema import custom_type_schema
from .._type_registry import pydantic_registry
from .._conditions import TypeIs


from pydantic_core import CoreSchema

if TYPE_CHECKING:
    from .._annotations_handler import AnnotationsHandler


class MyType:
    def __init__(self, x: int) -> None:
        assert isinstance(x, int)
        self.x = x

    def __repr__(self) -> str:
        return f'MyType(x={self.x})'


@pydantic_registry.register(condition=TypeIs(MyType))
class MyTypeHandler(TypeHandler):
    def handle_type(self, type: Any, annotations_handler: AnnotationsHandler) -> CoreSchema:
        def python_val(value):
            assert isinstance(value, MyType)
            return value

        return custom_type_schema(
            validator={'json': MyType, 'python': python_val},
        )
