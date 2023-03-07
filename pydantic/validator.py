import inspect
from copy import deepcopy
from typing import Any, Generic, Type, TypeVar

from pydantic_core import SchemaValidator

from pydantic._internal._generate_schema import GenerateSchema
from pydantic.main import BaseModel

T = TypeVar('T')


class Validator(Generic[T]):
    def __init__(self, __type: Type[T]) -> None:
        self._type = __type
        if inspect.isclass(self._type) and issubclass(self._type, BaseModel):
            schema = deepcopy(self._type.__pydantic_core_validation_schema__)
            # TODO: how can we avoid this mess?
            assert schema['type'] == 'union'
            inner = next(choice for choice in schema['choices'] if choice['type'] == 'typed-dict')
            assert inner['type'] == 'typed-dict'
            inner['return_fields_set'] = False
            self._validator = SchemaValidator(schema)
        else:
            gen = GenerateSchema(False, None)
            schema = gen.generate_schema(__type)
            if schema['type'] == 'typed-dict':
                schema['return_fields_set'] = False
            self._validator = SchemaValidator(schema)

    def __call__(self, __input: Any) -> T:
        return self._validator.validate_python(__input)
