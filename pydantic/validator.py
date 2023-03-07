from typing import Any, Generic, Type, TypeVar

from pydantic_core import CoreConfig, SchemaValidator

from pydantic._internal._generate_schema import GenerateSchema

T = TypeVar('T')


class Validator(Generic[T]):
    def __init__(self, __type: Type[T], *, config: CoreConfig | None = None) -> None:
        self._type = __type
        gen = GenerateSchema(False, None)
        schema = gen.generate_schema(__type)
        self._validator = SchemaValidator(schema, config=config)

    def __call__(self, __input: Any) -> T:
        return self._validator.validate_python(__input)
